"""HTTP endpoints for the analysis plan. Thin: translate HTTP <-> AnalysisPlanner."""
import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.dependencies import get_analysis_planner
from app.schemas import AnalysisPlanResponse
from app.services.analysis_planner import AnalysisPlanner, PlanEvent, PlanNotFound
from app.services.llm_client import LLMError
from app.services.upload_service import UploadError, UploadNotFound

router = APIRouter(prefix="/api/uploads", tags=["analysis"])
logger = logging.getLogger(__name__)


def _sse(name: str, payload: dict) -> str:
    """One Server-Sent Event: 'event: <name>' + 'data: <json>' + blank line."""
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _sse_stream(events: Iterator[PlanEvent]) -> Iterator[str]:
    # The 200 status is already sent once streaming starts, so failures
    # become an "error" event instead of an HTTP error code.
    try:
        for name, payload in events:
            yield _sse(name, payload)
    except (UploadError, LLMError) as exc:
        yield _sse("error", {"message": str(exc)})
    except Exception:
        logger.exception("Plan stream failed")
        yield _sse("error", {"message": "Something went wrong while planning. Try again."})


@router.post("/{upload_id}/plan/stream")
def stream_plan(upload_id: str, planner: AnalysisPlanner = Depends(get_analysis_planner)):
    """Same as POST /plan, but streams progress as Server-Sent Events:
    stage* -> summary -> item* -> done (or error)."""
    try:
        upload = planner.get_ready_upload(upload_id)
    except UploadNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except UploadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    return StreamingResponse(
        _sse_stream(planner.stream_plan(upload)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{upload_id}/plan", response_model=AnalysisPlanResponse)
def create_plan(upload_id: str, planner: AnalysisPlanner = Depends(get_analysis_planner)):
    """Profile the uploaded file and ask Claude which analyses to run. Waits for the full plan."""
    try:
        return planner.create_plan(upload_id)
    except UploadNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except UploadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except LLMError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


@router.get("/{upload_id}/plan", response_model=AnalysisPlanResponse)
def get_plan(upload_id: str, planner: AnalysisPlanner = Depends(get_analysis_planner)):
    """The last plan generated for this upload."""
    try:
        return planner.get_plan(upload_id)
    except PlanNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
