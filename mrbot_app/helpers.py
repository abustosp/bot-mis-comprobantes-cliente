import os
import sys
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests


def ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"


def build_headers(api_key: str, email: str) -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    if email:
        headers["email"] = email
    return headers


def safe_post(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_sec: int = 120) -> Dict[str, Any]:
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}
        return {"http_status": resp.status_code, "data": data}
    except Exception as exc:
        return {"http_status": None, "data": {"success": False, "message": f"Error de conexion: {exc}"}}


def safe_get(url: str, headers: Dict[str, str], timeout_sec: int = 60) -> Dict[str, Any]:
    try:
        resp = requests.get(url, headers=headers, timeout=timeout_sec)
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}
        return {"http_status": resp.status_code, "data": data}
    except Exception as exc:
        return {"http_status": None, "data": {"success": False, "message": f"Error de conexion: {exc}"}}


def _format_dates_str(df: pd.DataFrame) -> pd.DataFrame:
    """Intenta formatear columnas con nombres que contengan desde/hasta/fecha a dd/mm/aaaa como string."""
    out = df.copy()
    for col in out.columns:
        if any(key in col.lower() for key in ["desde", "hasta", "fecha"]):
            try:
                out[col] = pd.to_datetime(out[col], dayfirst=True, errors="coerce").dt.strftime("%d/%m/%Y")
            except Exception:
                out[col] = out[col].astype(str)
    return out


def df_preview(df: pd.DataFrame, rows: int = 5) -> str:
    if df.empty:
        return "Sin filas para mostrar."
    subset = _format_dates_str(df.head(rows).copy())
    headers = list(subset.columns)
    header_line = " | ".join(headers)
    rows_str = []
    for _, row in subset.iterrows():
        row_vals = ["" if pd.isna(row[h]) else str(row[h]) for h in headers]
        rows_str.append(" | ".join(row_vals))
    max_len = max(len(header_line), *(len(r) for r in rows_str))
    sep = "-" * max_len
    return "\n".join([header_line, sep] + rows_str)


def parse_bool_cell(value: Any, default: bool = False) -> bool:
    """
    Convierte valores de celdas a booleano. Acepta 1/0, true/false, si/no, yes/no.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "si", "sí", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return default


def make_today_str() -> str:
    return date.today().strftime("%d/%m/%Y")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Datos") -> bytes:
    with pd.ExcelWriter(os.devnull if sys.platform == "win32" else "/tmp/ignore.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    from io import BytesIO

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()
