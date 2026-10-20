"""Turns a CSV/XLSX file into a small JSON-friendly profile for the LLM.

The LLM never sees the whole file, only this summary: column names, a
semantic type per column, simple stats, top values and a few sample rows.
"""
import io
import warnings

import pandas as pd

from app.config import CATEGORICAL_MAX_UNIQUE, PROFILE_SAMPLE_ROWS, PROFILE_TOP_VALUES


def load_dataframe(data: bytes, extension: str) -> pd.DataFrame:
    """Read the whole file into pandas (no scaling tricks yet)."""
    if extension == ".csv":
        return pd.read_csv(io.BytesIO(data))
    if extension == ".xlsx":
        return pd.read_excel(io.BytesIO(data))  # first sheet
    raise ValueError(f"Unsupported file type: {extension}")


def profile_dataframe(df: pd.DataFrame, file_name: str) -> dict:
    return {
        "file_name": file_name,
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": [_profile_column(df[name]) for name in df.columns],
        "sample_rows": _sample_rows(df),
    }


def _profile_column(series: pd.Series) -> dict:
    non_null = series.dropna()
    semantic_type = _semantic_type(series, non_null)
    profile = {
        "name": str(series.name),
        "type": semantic_type,
        "null_pct": round(float(series.isna().mean() * 100), 2),
        "unique_count": int(non_null.nunique()),
    }

    if semantic_type == "numeric":
        profile.update(
            min=_num(non_null.min()),
            max=_num(non_null.max()),
            mean=_num(non_null.mean()),
            median=_num(non_null.median()),
        )
    elif semantic_type == "datetime":
        dates = _to_datetime(non_null)
        profile.update(min=str(dates.min().date()), max=str(dates.max().date()))
    elif semantic_type == "categorical":
        counts = non_null.astype(str).value_counts().head(PROFILE_TOP_VALUES)
        profile["top_values"] = {value: int(count) for value, count in counts.items()}
    else:  # text or id
        profile["examples"] = non_null.astype(str).head(3).tolist()

    return profile


def _semantic_type(series: pd.Series, non_null: pd.Series) -> str:
    """numeric | datetime | categorical | id | text. Decided in code, not by the LLM."""
    if non_null.empty:
        return "text"

    unique_ratio = non_null.nunique() / len(non_null)
    looks_like_id = unique_ratio > 0.95 and "id" in str(series.name).lower()

    if pd.api.types.is_bool_dtype(series):
        return "categorical"
    if pd.api.types.is_numeric_dtype(series):
        return "id" if looks_like_id else "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if _to_datetime(non_null.head(200)).notna().mean() > 0.9:
        return "datetime"
    if looks_like_id:
        return "id"
    if non_null.nunique() <= CATEGORICAL_MAX_UNIQUE:
        return "categorical"
    return "text"


def _to_datetime(values: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # "could not infer format" noise
        return pd.to_datetime(values, errors="coerce")


def _sample_rows(df: pd.DataFrame) -> list[dict]:
    rows = df.head(PROFILE_SAMPLE_ROWS).to_dict("records")
    return [{str(k): (None if pd.isna(v) else str(v)) for k, v in row.items()} for row in rows]


def _num(value) -> float:
    return round(float(value), 2)
