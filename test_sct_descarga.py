import os
import json
import pandas as pd
import requests

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("URL", "https://api-bots.mrbot.com.ar/").rstrip('/') + '/'
API_KEY = os.getenv("API_KEY", "")
MAIL = os.getenv("MAIL", "")
EXCEL_CANDIDATES = [
    os.path.join("ejemplos_api", "SCT-texting.xlsx"),
    os.path.join("ejemplos_api", "sct-test.xlsx"),
]


def pick_excel_path() -> str:
    for path in EXCEL_CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"No se encontró ninguno de los Excels de prueba: {EXCEL_CANDIDATES}")


EXCEL_PATH = pick_excel_path()

HEADERS = {"Content-Type": "application/json"}
if API_KEY:
    HEADERS["x-api-key"] = API_KEY
if MAIL:
    HEADERS["email"] = MAIL

GROUPED_KEYS = {
    "vencimientos": [
        "vencimientos_excel_minio_url",
        "vencimientos_csv_minio_url",
        "vencimientos_pdf_minio_url",
    ],
    "deudas": [
        "deudas_excel_minio_url",
        "deudas_csv_minio_url",
        "deudas_pdf_minio_url",
    ],
    "ddjj pendientes": [
        "ddjj_pendientes_excel_minio_url",
        "ddjj_pendientes_csv_minio_url",
        "ddjj_pendientes_pdf_minio_url",
    ],
}

def build_payload_from_excel(path: str) -> dict:
    df = pd.read_excel(path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    # Usar primera fila procesable
    row = df.iloc[0]
    payload = {
        "cuit_login": row.get("cuit_login", "").strip(),
        "clave": row.get("clave", ""),
        "cuit_representado": row.get("cuit_representado", "").strip(),
        "proxy_request": False,
        # Forzar todas las salidas minio = True y b64 = False
        "vencimientos_excel_b64": False,
        "vencimientos_csv_b64": False,
        "vencimientos_pdf_b64": False,
        "vencimientos_excel_minio": True,
        "vencimientos_csv_minio": True,
        "vencimientos_pdf_minio": True,
        "deudas_excel_b64": False,
        "deudas_csv_b64": False,
        "deudas_pdf_b64": False,
        "deudas_excel_minio": True,
        "deudas_csv_minio": True,
        "deudas_pdf_minio": True,
        "ddjj_pendientes_excel_b64": False,
        "ddjj_pendientes_csv_b64": False,
        "ddjj_pendientes_pdf_b64": False,
        "ddjj_pendientes_excel_minio": True,
        "ddjj_pendientes_csv_minio": True,
        "ddjj_pendientes_pdf_minio": True,
    }
    return payload

def test_sct_descarga_links():
    assert os.path.exists(EXCEL_PATH), f"No existe el excel de prueba: {EXCEL_PATH}"
    payload = build_payload_from_excel(EXCEL_PATH)
    url = BASE_URL + "api/v1/sct/consulta"
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=180)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    errors = [e.lower() for e in data.get("errors", [])]

    def has_error_for(section: str) -> bool:
        # Si la API reporta un error de la sección, los links no vienen en la respuesta.
        return any(section in err for err in errors)

    for section, keys in GROUPED_KEYS.items():
        values = [data.get(k) for k in keys]
        missing_keys = [k for k in keys if k not in data]
        has_link = any(values)
        all_empty = all(v in ("", None) for v in values)
        section_has_error = has_error_for(section) or (errors and not has_link)

        if section_has_error:
            # Nueva versión: con error las claves siguen presentes pero con string vacío.
            assert (
                not missing_keys
            ), f"Se esperaban claves vacías de {section} ante error, faltan: {missing_keys}\nErrores: {errors}"
            assert (
                all_empty
            ), f"Se esperaban strings vacíos de {section} ante error, pero vinieron datos: {values}\nErrores: {errors}"
            print(f"Sección {section} con error; claves vacías confirmadas")
        else:
            missing_non_empty = [k for k, v in zip(keys, values) if not v]
            assert (
                not missing_non_empty
            ), f"Faltan links de {section} sin errores declarados: {missing_non_empty}\nErrores: {errors}"

    print("Links recibidos:")
    for section, keys in GROUPED_KEYS.items():
        for k in keys:
            if data.get(k):
                print(f" - {section}: {k} -> {data.get(k)[:80]}...")
