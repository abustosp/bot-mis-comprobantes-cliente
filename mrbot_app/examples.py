import os
import sys
import pathlib
from typing import Dict, Tuple

# Ajustar sys.path si se ejecuta directamente (python mrbot_app/examples.py)
if __package__ is None or __package__ == "":
    sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from mrbot_app.constants import EXAMPLE_DIR, ACCENT, FG
from mrbot_app.formatos import aplicar_formato_encabezado, autoajustar_columnas, agregar_filtros


def ensure_example_excels() -> Dict[str, str]:
    """
    Crea archivos Excel de ejemplo para cada endpoint si no existen.
    Retorna un dict con el nombre corto -> ruta.
    """
    os.makedirs(EXAMPLE_DIR, exist_ok=True)
    examples: Dict[str, Tuple[str, pd.DataFrame]] = {
        "mis_comprobantes.xlsx": pd.DataFrame(
            [
                {
                    "procesar": "SI",
                    "cuit_inicio_sesion": "20123456789",
                    "nombre_representado": "Empresa Demo SA",
                    "cuit_representado": "20987654321",
                    "contrasena": "clave_demo",
                    "descarga_emitidos": "SI",
                    "descarga_recibidos": "SI",
                    "desde": "01/01/2024",
                    "hasta": "31/12/2024",
                    "ubicacion_emitidos": "/tmp/emitidos",
                    "nombre_emitidos": "emitidos-demo",
                    "ubicacion_recibidos": "/tmp/recibidos",
                    "nombre_recibidos": "recibidos-demo",
                },
                {
                    "procesar": "NO",
                    "cuit_inicio_sesion": "20111111111",
                    "nombre_representado": "Ejemplo NO",
                    "cuit_representado": "20999999999",
                    "contrasena": "clave_no",
                    "descarga_emitidos": "NO",
                    "descarga_recibidos": "NO",
                    "desde": "01/01/2024",
                    "hasta": "31/12/2024",
                    "ubicacion_emitidos": "/tmp/emitidos",
                    "nombre_emitidos": "emitidos-no",
                    "ubicacion_recibidos": "/tmp/recibidos",
                    "nombre_recibidos": "recibidos-no",
                },
            ]
        ),
        "rcel.xlsx": pd.DataFrame(
            [
                {
                    "procesar": "SI",
                    "cuit_representante": "20123456789",
                    "nombre_rcel": "Empresa Demo SA",
                    "representado_cuit": "20987654321",
                    "clave": "clave_demo",
                    "desde": "01/01/2024",
                    "hasta": "31/12/2024",
                    "ubicacion_descarga": "./descargas/RCEL/20987654321",
                },
                {
                    "procesar": "NO",
                    "cuit_representante": "20111111111",
                    "nombre_rcel": "Ejemplo NO",
                    "representado_cuit": "20999999999",
                    "clave": "clave_no",
                    "desde": "01/01/2024",
                    "hasta": "31/12/2024",
                    "ubicacion_descarga": "./descargas/RCEL/20999999999",
                },
            ]
        ),
        "sct.xlsx": pd.DataFrame(
            [
                {
                    "procesar": "SI",
                    "cuit_login": "20123456789",
                    "cuit_representado": "20987654321",
                    "clave": "clave_demo",
                    "deuda": "SI",
                    "vencimientos": "SI",
                    "presentacion_ddjj": "SI",
                    "excel": "SI",
                    "csv": "SI",
                    "pdf": "NO",
                    "ubicacion_deuda": "./Descargas",
                    "nombre_deuda": "deuda-demo",
                    "ubicacion_vencimientos": "./Descargas",
                    "nombre_vencimientos": "vencimientos-demo",
                    "ubicacion_ddjj": "./Descargas",
                    "nombre_ddjj": "ddjj-demo",
                },
                {
                    "procesar": "NO",
                    "cuit_login": "20111111111",
                    "cuit_representado": "20999999999",
                    "clave": "clave_no",
                    "deuda": "NO",
                    "vencimientos": "NO",
                    "presentacion_ddjj": "NO",
                    "excel": "NO",
                    "csv": "NO",
                    "pdf": "NO",
                    "ubicacion_deuda": "./Descargas",
                    "nombre_deuda": "deuda-no",
                    "ubicacion_vencimientos": "./Descargas",
                    "nombre_vencimientos": "vencimientos-no",
                    "ubicacion_ddjj": "./Descargas",
                    "nombre_ddjj": "ddjj-no",
                },
            ]
        ),
        "ccma.xlsx": pd.DataFrame(
            [
                {
                    "procesar": "SI",
                    "cuit_representante": "20123456789",
                    "clave_representante": "clave_demo",
                    "cuit_representado": "20987654321",
                },
                {
                    "procesar": "NO",
                    "cuit_representante": "20111111111",
                    "clave_representante": "clave_no",
                    "cuit_representado": "20999999999",
                },
            ]
        ),
        "apocrifos.xlsx": pd.DataFrame(
            [
                {"cuit": "20333444555"},
                {"cuit": "27999888777"},
            ]
        ),
        "consulta_cuit.xlsx": pd.DataFrame([{"cuit": "20333444555"}, {"cuit": "20987654321"}]),
    }

    paths: Dict[str, str] = {}
    for name, df in examples.items():
        path = os.path.join(EXAMPLE_DIR, name)
        paths[name] = path
        if not os.path.exists(path):
            try:
                df.to_excel(path, index=False)
                _format_excel(path)
            except Exception:
                pass
        else:
            _format_excel(path)
    return paths


def _format_excel(path: str) -> None:
    try:
        wb = load_workbook(path)
        ws = wb.active
        aplicar_formato_encabezado(ws)
        autoajustar_columnas(ws)
        agregar_filtros(ws)
        wb.save(path)
    except Exception:
        pass


if __name__ == "__main__":
    rutas = ensure_example_excels()
    for k, v in rutas.items():
        print(f"{k}: {v}")
