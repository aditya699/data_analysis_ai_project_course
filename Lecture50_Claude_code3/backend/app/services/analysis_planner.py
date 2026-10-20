"""The Plan feature: uploaded file -> profile -> prompt -> Claude -> validated plan.

`stream_plan` yields progress events as it goes, so the UI can show what is
happening and draw each suggestion as soon as Claude finishes writing it.
"""
import json
from collections.abc import Iterator
from datetime import datetime, timezone

from pydantic import ValidationError

from app.config import PLAN_MAX_ITEMS, PROMPTS_DIR, REPORTS_PREFIX
from app.schemas import AnalysisItem, AnalysisPlan, AnalysisPlanResponse, UploadInfo
from app.services.blob_storage import BlobStorage
from app.services.llm_client import LLMClient
from app.services.profiler import load_dataframe, profile_dataframe
from app.services.upload_registry import UploadRegistry
from app.services.upload_service import UploadError, UploadNotFound
from app.utils.file_rules import get_extension
from app.utils.plan_stream_parser import PlanStreamParser

SYSTEM_PROMPT = (PROMPTS_DIR / "analysis_plan_v1.md").read_text(encoding="utf-8")

# One progress event: (event name, JSON-friendly payload)
PlanEvent = tuple[str, dict]


class PlanNotFound(Exception):
    """No plan has been generated for this upload yet (404)."""


def _report_blob(upload_id: str, name: str) -> str:
    return f"{REPORTS_PREFIX}/{upload_id}/{name}"


def _stage(stage: str, message: str) -> PlanEvent:
    return "stage", {"stage": stage, "message": message}


class AnalysisPlanner:
    def __init__(self, storage: BlobStorage, registry: UploadRegistry, llm: LLMClient):
        self._storage = storage
        self._registry = registry
        self._llm = llm

    def get_ready_upload(self, upload_id: str) -> UploadInfo:
        """Checks done before streaming starts, so they can still return 400/404."""
        upload = self._registry.get(upload_id)
        if upload is None:
            raise UploadNotFound(f"Upload {upload_id} not found.")
        if upload.status != "uploaded":
            raise UploadError("Finish uploading the file before asking for a plan.")
        return upload

    def stream_plan(self, upload: UploadInfo) -> Iterator[PlanEvent]:
        """Events: stage* -> summary -> item* -> done. Errors are raised to the caller."""
        yield _stage("reading", f"Reading {upload.original_filename}")
        data = self._storage.download_bytes(upload.blob_name)
        if data is None:
            raise UploadError("The file is missing from storage. Upload it again.")
        try:
            df = load_dataframe(data, get_extension(upload.original_filename))
        except Exception as exc:  # pandas raises many types for bad files
            raise UploadError(f"Could not read the file as a table: {exc}") from exc

        profile = profile_dataframe(df, upload.original_filename)
        known_columns = {c["name"] for c in profile["columns"]}
        yield _stage(
            "profiling",
            f"Profiled {profile['row_count']:,} rows and {profile['column_count']} columns",
        )

        user_message = (
            "<dataset_profile>\n"
            f"{json.dumps(profile, indent=2, ensure_ascii=False)}\n"
            "</dataset_profile>\n\n"
            "Suggest the analyses for this dataset."
        )
        parser = PlanStreamParser()
        plan: AnalysisPlan | None = None
        writing = False

        yield _stage("thinking", "Agent is studying your columns")
        for event in self._llm.stream_parse(SYSTEM_PROMPT, user_message, AnalysisPlan):
            if event.type == "text":
                if not writing:
                    writing = True
                    yield _stage("writing", "Agent is writing suggestions")
                for kind, value in parser.feed(event.text):
                    if kind == "summary":
                        yield "summary", {"dataset_summary": value}
                    elif (item := self._valid_item(value, known_columns)) is not None:
                        yield "item", item.model_dump()
            elif event.type == "final":
                plan = event.parsed

        items = self._clean_items(plan.items, known_columns)
        response = AnalysisPlanResponse(
            upload_id=upload.upload_id,
            file_name=upload.original_filename,
            model=self._llm.model,
            generated_at=datetime.now(timezone.utc),
            dataset_summary=plan.dataset_summary,
            items=items,
            dropped_items=len(plan.items) - len(items),
        )

        # Keep both so they survive a refresh and later steps can reuse the profile.
        self._storage.upload_text(
            _report_blob(upload.upload_id, "profile.json"),
            json.dumps(profile, indent=2, ensure_ascii=False),
            "application/json",
        )
        self._storage.upload_text(
            _report_blob(upload.upload_id, "plan.json"),
            response.model_dump_json(indent=2),
            "application/json",
        )
        yield "done", response.model_dump(mode="json")

    def create_plan(self, upload_id: str) -> AnalysisPlanResponse:
        """Same flow without streaming: wait for the "done" event."""
        upload = self.get_ready_upload(upload_id)
        for name, payload in self.stream_plan(upload):
            if name == "done":
                return AnalysisPlanResponse.model_validate(payload)
        raise RuntimeError("Plan stream ended without a result.")

    def get_plan(self, upload_id: str) -> AnalysisPlanResponse:
        data = self._storage.download_bytes(_report_blob(upload_id, "plan.json"))
        if data is None:
            raise PlanNotFound(f"No plan yet for upload {upload_id}.")
        return AnalysisPlanResponse.model_validate_json(data)

    @staticmethod
    def _valid_item(raw: dict, known_columns: set[str]) -> AnalysisItem | None:
        try:
            item = AnalysisItem.model_validate(raw)
        except ValidationError:
            return None
        return item if item.columns and set(item.columns) <= known_columns else None

    @staticmethod
    def _clean_items(items: list[AnalysisItem], known_columns: set[str]) -> list[AnalysisItem]:
        """Drop items that mention columns the file doesn't have, then order by priority."""
        valid = [item for item in items if item.columns and set(item.columns) <= known_columns]
        valid.sort(key=lambda item: item.priority)
        valid = valid[:PLAN_MAX_ITEMS]
        for rank, item in enumerate(valid, start=1):
            item.priority = rank
        return valid
