"""Pulls finished pieces out of a plan JSON that is still being streamed.

Claude streams the plan as JSON text, a few characters at a time:
    {"dataset_summary": "UPI pay...", "items": [{"title": ...}, {"title": ...
We don't want to wait for the closing brace, so this scanner walks the text
once and reports each piece the moment it is complete:
    ("summary", "UPI payments for 2025...")
    ("item", {"title": "Monthly trend", ...})
Pure Python, no FastAPI or LLM imports.
"""
import json


class PlanStreamParser:
    def __init__(self):
        self._buf = ""
        self._pos = 0              # next character to scan
        self._depth = 0            # 1 = top-level object, 2 = items array, 3 = one item
        self._in_string = False
        self._escaped = False
        self._string_start = 0
        self._top_key = None       # last key seen at depth 1
        self._expect_value = False  # at depth 1: after ':' and before ','
        self._in_items = False
        self._item_start = None

    def feed(self, chunk: str) -> list[tuple[str, object]]:
        self._buf += chunk
        found = []
        while self._pos < len(self._buf):
            char = self._buf[self._pos]
            if self._in_string:
                self._scan_string_char(char, found)
            else:
                self._scan_structure_char(char, found)
            self._pos += 1
        return found

    def _scan_string_char(self, char: str, found: list) -> None:
        if self._escaped:
            self._escaped = False
        elif char == "\\":
            self._escaped = True
        elif char == '"':
            self._in_string = False
            if self._depth == 1:
                text = json.loads(self._buf[self._string_start : self._pos + 1])
                if not self._expect_value:
                    self._top_key = text
                elif self._top_key == "dataset_summary":
                    found.append(("summary", text))

    def _scan_structure_char(self, char: str, found: list) -> None:
        if char == '"':
            self._in_string = True
            self._string_start = self._pos
        elif char == ":" and self._depth == 1:
            self._expect_value = True
        elif char == "," and self._depth == 1:
            self._expect_value = False
        elif char in "[{":
            self._depth += 1
            if char == "[" and self._depth == 2 and self._top_key == "items":
                self._in_items = True
            elif char == "{" and self._in_items and self._depth == 3:
                self._item_start = self._pos
        elif char in "]}":
            if char == "}" and self._in_items and self._depth == 3 and self._item_start is not None:
                found.append(("item", json.loads(self._buf[self._item_start : self._pos + 1])))
                self._item_start = None
            elif char == "]" and self._depth == 2:
                self._in_items = False
            self._depth -= 1
