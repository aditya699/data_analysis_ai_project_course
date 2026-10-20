"""The only file that talks to the LLM (Claude via the Anthropic SDK)."""
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import Settings

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The LLM call failed or returned no usable answer."""


@dataclass
class LLMEvent(Generic[T]):
    """What happens while Claude answers, in order:
    "thinking" (started reasoning) -> "text" (many JSON chunks) -> "final" (validated object).
    """

    type: Literal["thinking", "text", "final"]
    text: str = ""
    parsed: T | None = None


class LLMClient:
    def __init__(self, settings: Settings):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model

    def stream_parse(self, system: str, user: str, output_model: type[T]) -> Iterator[LLMEvent[T]]:
        """Stream Claude's answer as it is written; the last event carries the validated object.

        Structured output: the text chunks join up into JSON matching `output_model`.
        """
        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": "medium"},
                output_format=output_model,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start" and event.content_block.type == "thinking":
                        yield LLMEvent("thinking")
                    elif event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield LLMEvent("text", text=event.delta.text)
                response = stream.get_final_message()
        except anthropic.RateLimitError as exc:
            raise LLMError("The AI service is busy. Try again in a minute.") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"The AI service returned an error ({exc.status_code}).") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError("Could not reach the AI service. Check the network.") from exc

        if response.stop_reason == "refusal":
            raise LLMError("The AI declined to analyse this dataset.")
        if response.stop_reason == "max_tokens":
            raise LLMError("The AI response was cut off. Try again.")
        if response.parsed_output is None:
            raise LLMError("The AI response did not match the expected format.")
        yield LLMEvent("final", parsed=response.parsed_output)
