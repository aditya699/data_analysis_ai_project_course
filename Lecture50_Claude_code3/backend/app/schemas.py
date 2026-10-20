"""Request and response shapes for the API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UploadStatus = Literal["pending", "uploaded", "failed"]


class CreateUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255, examples=["upi_transactions.csv"])
    size_bytes: int = Field(examples=[4_812_345])
    content_type: str = Field(default="application/octet-stream", max_length=200)


class CreateUploadResponse(BaseModel):
    upload_id: str
    upload_url: str = Field(description="Signed URL. PUT the file here, directly to blob storage.")
    upload_method: Literal["PUT"] = "PUT"
    upload_headers: dict[str, str] = Field(description="Headers the PUT request must send.")
    expires_at: datetime


AnalysisType = Literal[
    "trend", "breakdown", "distribution", "top_n", "comparison", "relationship", "data_quality"
]
ChartType = Literal["line", "bar", "pie", "histogram", "scatter", "table"]


class AnalysisItem(BaseModel):
    """One suggested analysis. Also the schema Claude must follow (structured output)."""

    title: str = Field(description="Short name, e.g. 'Monthly sales trend'")
    question: str = Field(description="The business question this analysis answers")
    analysis_type: AnalysisType
    columns: list[str] = Field(description="Exact column names from the profile")
    chart: ChartType
    priority: int = Field(description="1 = most useful. Unique per item.")
    reason: str = Field(description="Why this is worth looking at for this dataset")


class AnalysisPlan(BaseModel):
    dataset_summary: str = Field(description="One or two sentences on what this dataset is")
    items: list[AnalysisItem]


class AnalysisPlanResponse(AnalysisPlan):
    upload_id: str
    file_name: str
    model: str
    generated_at: datetime
    dropped_items: int = Field(description="Items removed because they used unknown columns")


class UploadInfo(BaseModel):
    upload_id: str
    original_filename: str
    size_bytes: int
    content_type: str
    blob_name: str
    status: UploadStatus
    error: str | None = None
    created_at: datetime
    uploaded_at: datetime | None = None
