#!/usr/bin/python3
import os
import sys
import json
import io
import base64
import contextlib
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from dotenv import load_dotenv
from bin.consulta import consulta_mc_csv
from bin.consulta import crear_directorio_seguro, descargar_archivo_minio

# Cargar variables de entorno para valores por defecto
load_dotenv()


# =========================
# Configuracion y helpers
# =========================
DEFAULT_BASE_URL = os.getenv("URL", "https://api-bots.mrbot.com.ar/")
DEFAULT_API_KEY = os.getenv("API_KEY", "")
DEFAULT_EMAIL = os.getenv("MAIL", "")

BG = "#2e2e2e"
FG = "#ffffff"
ACCENT = "#d35400"
EXAMPLE_DIR = "ejemplos_api"


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
                # Si falla el parseo, dejar como texto original
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
    with pd.ExcelWriter(
        os.devnull if sys.platform == "win32" else "/tmp/ignore.xlsx",  # placeholder, buffer below
        engine="openpyxl"
    ) as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    # La forma mas sencilla en este contexto es usar un buffer en memoria
    from io import BytesIO

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


# =========================
# Ejemplos de Excel
# =========================
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
                },
                {
                    "procesar": "NO",
                    "cuit_representante": "20111111111",
                    "nombre_rcel": "Ejemplo NO",
                    "representado_cuit": "20999999999",
                    "clave": "clave_no",
                    "desde": "01/01/2024",
                    "hasta": "31/12/2024",
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
            except Exception:
                pass
    return paths


# =========================
# Ventanas base y utilidades UI
# =========================
class BaseWindow(tk.Toplevel):
    def __init__(self, master=None, title: str = ""):
        super().__init__(master)
        self.configure(background=BG)
        self.title(title)
        self.resizable(False, False)

    def add_section_label(self, parent, text: str) -> None:
        lbl = ttk.Label(parent, text=text, foreground=FG, background=BG, font=("Arial", 11, "bold"))
        lbl.pack(anchor="w", pady=(8, 2))

    def add_info_label(self, parent, text: str) -> ttk.Label:
        lbl = ttk.Label(parent, text=text, foreground=FG, background=BG, wraplength=420, justify="left")
        lbl.pack(anchor="w", pady=2)
        return lbl

    def add_preview(self, parent, height: int = 10, show: bool = True) -> tk.Text:
        txt = tk.Text(parent, height=height, width=70, wrap="none", background="#1e1e1e", foreground=FG)
        if show:
            txt.pack(anchor="w", pady=4, padx=2, fill="both", expand=False)
        txt.configure(state="disabled")
        return txt

    def set_preview(self, widget: Optional[tk.Text], content: str) -> None:
        if widget is None:
            return
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="disabled")

    def open_df_preview(self, df: Optional[pd.DataFrame], title: str = "Previsualización de Excel", max_rows: int = 50) -> None:
        if df is None or df.empty:
            messagebox.showwarning("Sin datos", "No hay datos para previsualizar.")
            return
        top = tk.Toplevel(self)
        top.title(title)
        top.configure(background="#f5f5f5")
        df_display = _format_dates_str(df.head(max_rows).copy())
        tk.Label(
            top,
            text=f"Registros: {len(df)} | Columnas: {len(df.columns)}",
            background="#f5f5f5",
            foreground="#000000",
            font=("Arial", 11, "bold"),
        ).pack(anchor="w", padx=8, pady=(8, 4))
        txt = tk.Text(
            top,
            height=20,
            width=120,
            wrap="none",
            background="#ffffff",
            foreground="#000000",
            font=("Courier New", 10),
        )
        txt.pack(fill="both", expand=True, padx=8, pady=4)
        txt.insert(tk.END, df_display.to_string(index=False))
        txt.configure(state="disabled")
        ttk.Button(top, text="Cerrar", command=top.destroy).pack(pady=8)


class ConfigPane(ttk.Frame):
    """
    Panel de configuracion compartido (base URL, API key, email).
    """

    def __init__(self, master):
        super().__init__(master, padding=8)
        self.base_url_var = tk.StringVar(value=DEFAULT_BASE_URL)
        self.api_key_var = tk.StringVar(value=DEFAULT_API_KEY)
        self.email_var = tk.StringVar(value=DEFAULT_EMAIL)

        ttk.Label(self, text="Base URL").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(self, textvariable=self.base_url_var, width=40).grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(self, text="API Key").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(self, textvariable=self.api_key_var, width=40, show="*").grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(self, text="Mail").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        ttk.Entry(self, textvariable=self.email_var, width=40).grid(row=2, column=1, sticky="ew", padx=4, pady=2)

        self.columnconfigure(1, weight=1)

    def get_config(self) -> Tuple[str, str, str]:
        return self.base_url_var.get().strip(), self.api_key_var.get().strip(), self.email_var.get().strip()


# =========================
# Ventana Mis Comprobantes (reutiliza logica existente)
# =========================
class GuiDescargaMC(BaseWindow):
    def __init__(self, master=None, config_pane: Optional[ConfigPane] = None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Descarga de Mis Comprobantes")
        self.config_pane = config_pane
        self.example_paths = example_paths or {}
        self.mc_df: Optional[pd.DataFrame] = None
        self.processing = False

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        self.add_section_label(container, "Modulo para descarga masiva")
        self.add_info_label(
            container,
            "Descarga de Mis Comprobantes basada en un Excel con contribuyentes. "
            "Admite columnas opcionales: procesar (SI/NO), desde, hasta, ubicacion_emitidos, nombre_emitidos, "
            "ubicacion_recibidos, nombre_recibidos. Se pueden editar variables de entorno "
            "desde el boton inferior.",
        )

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=8)

        ttk.Button(btn_frame, text="Seleccionar Excel", command=self.open_excel_file).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Requests restantes", command=self.show_requests).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Ver ejemplo", command=self.open_example).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Previsualizar Excel", command=self.preview_excel).grid(row=0, column=3, padx=4, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Descargar Mis Comprobantes", command=self.confirmar).grid(row=1, column=0, columnspan=4, padx=4, pady=6, sticky="ew")

        btn_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.preview = self.add_preview(container, height=8, show=False)
        self.set_preview(self.preview, "Selecciona un Excel y presiona 'Previsualizar Excel' para ver los datos.")

        log_frame = ttk.LabelFrame(container, text="Logs de ejecución")
        log_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.log_text = tk.Text(
            log_frame,
            height=16,
            wrap="word",
            background="#1b1b1b",
            foreground="#dcdcdc",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        self.selected_excel: Optional[str] = None

    def open_excel_file(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        self.selected_excel = filename
        try:
            df = pd.read_excel(filename, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            if "procesar" in df.columns:
                df = df[df["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
            self.mc_df = df
            self.set_preview(self.preview, "Excel cargado. Usa 'Previsualizar Excel' para ver los datos.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")
            self.mc_df = None

    def preview_excel(self) -> None:
        self.open_df_preview(self.mc_df, title="Previsualización Mis Comprobantes")

    def clear_logs(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def append_log(self, text: str) -> None:
        if not text:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self.log_text.update_idletasks()

    def _create_log_writer(self) -> io.TextIOBase:
        gui = self

        class _TkTextWriter(io.TextIOBase):
            def write(self, message: str) -> int:
                if not message:
                    return 0
                gui.append_log(message)
                try:
                    sys.__stdout__.write(message)
                except Exception:
                    pass
                return len(message)

            def flush(self) -> None:
                try:
                    sys.__stdout__.flush()
                except Exception:
                    pass

        return _TkTextWriter()

    def open_example(self) -> None:
        path = self.example_paths.get("mis_comprobantes.xlsx")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    def show_requests(self) -> None:
        _, api_key, email = self.config_pane.get_config() if self.config_pane else ("", "", "")
        base_url, _, _ = self.config_pane.get_config() if self.config_pane else (DEFAULT_BASE_URL, DEFAULT_API_KEY, DEFAULT_EMAIL)
        headers = build_headers(api_key, email)
        url = ensure_trailing_slash(base_url) + f"api/v1/user/consultas/{email}"
        resp = safe_get(url, headers)
        messagebox.showinfo("Requests restantes", json.dumps(resp.get("data"), indent=2, ensure_ascii=False))

    def confirmar(self) -> None:
        excel_to_use = self.selected_excel or self.example_paths.get("mis_comprobantes.xlsx")
        if not excel_to_use:
            messagebox.showerror("Error", "Primero selecciona un Excel o usa el ejemplo de mis_comprobantes.xlsx.")
            return
        if not os.path.exists(excel_to_use):
            messagebox.showerror("Error", f"No se encontró el archivo seleccionado: {excel_to_use}")
            return
        if self.processing:
            messagebox.showinfo("Proceso en curso", "Ya hay un proceso ejecutándose. Espera a que finalice.")
            return
        answer = messagebox.askyesno("Confirmar", "Esta accion enviara las consultas. Continuar?")
        if answer:
            try:
                self.processing = True
                self.clear_logs()
                self.append_log(f"Iniciando proceso con: {excel_to_use}\n\n")
                writer = self._create_log_writer()
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    consulta_mc_csv(excel_to_use)
                messagebox.showinfo("Proceso finalizado", f"Consulta finalizada con {excel_to_use}. Revisa los logs en la ventana.")
            except Exception as exc:
                messagebox.showerror("Error", f"No se pudo ejecutar consulta_mc_csv: {exc}")
                self.append_log(f"\nError: {exc}\n")
            finally:
                self.processing = False


# =========================
# Ventana RCEL
# =========================
class RcelWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Comprobantes en Linea (RCEL)")
        self.config_provider = config_provider
        self.example_paths = example_paths or {}
        self.rcel_df: Optional[pd.DataFrame] = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        self.add_section_label(container, "Descarga de Comprobantes en Linea (RCEL)")
        self.add_info_label(
            container,
            "Permite consultas individuales o masivas basadas en un Excel. "
            "Debe incluir cuit_representante, nombre_rcel, representado_cuit y clave. "
            "Opcionalmente, puedes agregar columnas desde y hasta (DD/MM/AAAA) por fila y procesar (SI/NO).",
        )

        dates_frame = ttk.Frame(container)
        dates_frame.pack(fill="x", pady=2)
        ttk.Label(dates_frame, text="Desde (DD/MM/AAAA)").grid(row=0, column=0, padx=4, pady=2, sticky="w")
        ttk.Label(dates_frame, text="Hasta (DD/MM/AAAA)").grid(row=0, column=1, padx=4, pady=2, sticky="w")
        self.desde_var = tk.StringVar(value=f"01/01/{date.today().year}")
        self.hasta_var = tk.StringVar(value=make_today_str())
        ttk.Entry(dates_frame, textvariable=self.desde_var, width=15).grid(row=1, column=0, padx=4, pady=2, sticky="w")
        ttk.Entry(dates_frame, textvariable=self.hasta_var, width=15).grid(row=1, column=1, padx=4, pady=2, sticky="w")

        inputs = ttk.Frame(container)
        inputs.pack(fill="x", pady=4)
        ttk.Label(inputs, text="CUIT representante").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="Nombre RCEL").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="CUIT representado").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="Clave fiscal").grid(row=3, column=0, sticky="w", padx=4, pady=2)

        self.cuit_rep_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.cuit_repr_var = tk.StringVar()
        self.clave_var = tk.StringVar()
        ttk.Entry(inputs, textvariable=self.cuit_rep_var, width=25).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.nombre_var, width=25).grid(row=1, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.cuit_repr_var, width=25).grid(row=2, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.clave_var, width=25, show="*").grid(row=3, column=1, padx=4, pady=2, sticky="ew")
        inputs.columnconfigure(1, weight=1)

        opts = ttk.Frame(container)
        opts.pack(fill="x", pady=4)
        self.b64_var = tk.BooleanVar(value=False)
        self.minio_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="PDF en base64", variable=self.b64_var).grid(row=0, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="Subir a MinIO", variable=self.minio_var).grid(row=0, column=1, padx=4, pady=2, sticky="w")

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Consultar individual", command=self.consulta_individual).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Seleccionar Excel", command=self.cargar_excel).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Ejemplo Excel", command=self.abrir_ejemplo).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Previsualizar Excel", command=lambda: self.open_df_preview(self.rcel_df, "Previsualización RCEL")).grid(row=0, column=3, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Procesar Excel", command=self.procesar_excel).grid(row=1, column=0, columnspan=4, padx=4, pady=6, sticky="ew")
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        self.preview = self.add_preview(container, height=8, show=False)
        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.preview, "Excel no cargado o sin previsualizar. Usa 'Previsualizar Excel'.")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("rcel.xlsx")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    def cargar_excel(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        try:
            self.rcel_df = pd.read_excel(filename, dtype=str).fillna("")
            self.rcel_df.columns = [c.strip().lower() for c in self.rcel_df.columns]
            df_preview_local = self.rcel_df
            if "procesar" in df_preview_local.columns:
                df_preview_local = df_preview_local[df_preview_local["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
            self.set_preview(self.preview, "Excel cargado. Usa 'Previsualizar Excel'.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")

    def consulta_individual(self) -> None:
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        payload = {
            "desde": self.desde_var.get().strip(),
            "hasta": self.hasta_var.get().strip(),
            "cuit_representante": self.cuit_rep_var.get().strip(),
            "nombre_rcel": self.nombre_var.get().strip(),
            "representado_cuit": self.cuit_repr_var.get().strip(),
            "clave": self.clave_var.get(),
            "b64_pdf": bool(self.b64_var.get()),
            "minio_upload": bool(self.minio_var.get()),
        }
        url = ensure_trailing_slash(base_url) + "api/v1/rcel/consulta"
        resp = safe_post(url, headers, payload)
        self.set_preview(self.result_box, json.dumps(resp, indent=2, ensure_ascii=False))

    def procesar_excel(self) -> None:
        if self.rcel_df is None or self.rcel_df.empty:
            messagebox.showerror("Error", "Carga un Excel primero.")
            return
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        url = ensure_trailing_slash(base_url) + "api/v1/rcel/consulta"
        rows: List[Dict[str, Any]] = []
        df_to_process = self.rcel_df
        if "procesar" in df_to_process.columns:
            df_to_process = df_to_process[df_to_process["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
        if df_to_process.empty:
            messagebox.showwarning("Sin filas a procesar", "No hay filas marcadas con procesar=SI.")
            return

        for _, row in df_to_process.iterrows():
            desde = str(row.get("desde", "")).strip() or self.desde_var.get().strip()
            hasta = str(row.get("hasta", "")).strip() or self.hasta_var.get().strip()
            payload = {
                "desde": desde,
                "hasta": hasta,
                "cuit_representante": str(row.get("cuit_representante", "")).strip(),
                "nombre_rcel": str(row.get("nombre_rcel", "")).strip(),
                "representado_cuit": str(row.get("representado_cuit", "")).strip(),
                "clave": str(row.get("clave", "")),
                "b64_pdf": bool(self.b64_var.get()),
                "minio_upload": bool(self.minio_var.get()),
            }
            resp = safe_post(url, headers, payload)
            data = resp.get("data", {})
            rows.append(
                {
                    "representado_cuit": payload["representado_cuit"],
                    "http_status": resp.get("http_status"),
                    "success": data.get("success") if isinstance(data, dict) else None,
                    "message": data.get("message") if isinstance(data, dict) else None,
                }
            )
        out_df = pd.DataFrame(rows)
        self.set_preview(self.result_box, df_preview(out_df, rows=min(20, len(out_df))))


# =========================
# Ventana SCT
# =========================
class SctWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Sistema de Cuentas Tributarias (SCT)")
        self.config_provider = config_provider
        self.example_paths = example_paths or {}
        self.sct_df: Optional[pd.DataFrame] = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        self.add_section_label(container, "Sistema de Cuentas Tributarias (SCT)")
        self.add_info_label(
            container,
            "Consulta individual o masiva. Formatos disponibles: Excel/CSV/PDF en base64 o subida a MinIO.",
        )

        inputs = ttk.Frame(container)
        inputs.pack(fill="x", pady=4)
        ttk.Label(inputs, text="CUIT login").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="Clave").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="CUIT representado").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        self.sct_login_var = tk.StringVar()
        self.sct_clave_var = tk.StringVar()
        self.sct_repr_var = tk.StringVar()
        ttk.Entry(inputs, textvariable=self.sct_login_var, width=25).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.sct_clave_var, width=25, show="*").grid(row=1, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.sct_repr_var, width=25).grid(row=2, column=1, padx=4, pady=2, sticky="ew")
        inputs.columnconfigure(1, weight=1)

        opts = ttk.Frame(container)
        opts.pack(fill="x", pady=2)
        self.opt_excel_minio = tk.BooleanVar(value=True)
        self.opt_excel_b64 = tk.BooleanVar(value=False)
        self.opt_csv_minio = tk.BooleanVar(value=False)
        self.opt_csv_b64 = tk.BooleanVar(value=False)
        self.opt_pdf_minio = tk.BooleanVar(value=False)
        self.opt_pdf_b64 = tk.BooleanVar(value=False)
        self.opt_proxy = tk.BooleanVar(value=False)
        self.opt_deuda = tk.BooleanVar(value=True)
        self.opt_vencimientos = tk.BooleanVar(value=True)
        self.opt_presentacion = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Excel MinIO", variable=self.opt_excel_minio).grid(row=0, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="Excel base64", variable=self.opt_excel_b64).grid(row=0, column=1, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="CSV MinIO", variable=self.opt_csv_minio).grid(row=1, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="CSV base64", variable=self.opt_csv_b64).grid(row=1, column=1, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="PDF MinIO", variable=self.opt_pdf_minio).grid(row=2, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="PDF base64", variable=self.opt_pdf_b64).grid(row=2, column=1, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="proxy_request", variable=self.opt_proxy).grid(row=3, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="Incluir deuda", variable=self.opt_deuda).grid(row=4, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="Incluir vencimientos", variable=self.opt_vencimientos).grid(row=4, column=1, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="Incluir presentacion DDJJ", variable=self.opt_presentacion).grid(row=5, column=0, padx=4, pady=2, sticky="w")

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Consultar individual", command=self.consulta_individual).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Seleccionar Excel", command=self.cargar_excel).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Ejemplo Excel", command=self.abrir_ejemplo).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Previsualizar Excel", command=lambda: self.open_df_preview(self.sct_df, "Previsualización SCT")).grid(row=0, column=3, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Procesar Excel", command=self.procesar_excel).grid(row=1, column=0, columnspan=4, padx=4, pady=6, sticky="ew")
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        self.preview = self.add_preview(container, height=8, show=False)
        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.preview, "Excel no cargado o sin previsualizar. Usa 'Previsualizar Excel'.")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("sct.xlsx")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    def _ensure_extension(self, name: str, ext: str) -> str:
        clean = (name or "").strip()
        if not clean:
            clean = "reporte"
        if not clean.lower().endswith(f".{ext}"):
            clean = f"{clean}.{ext}"
        return clean

    def _prepare_dir(self, desired_path: str, base_name: str, cuit_representado: str, cuit_login: str) -> str:
        return crear_directorio_seguro(
            desired_path,
            nombre_representado=cuit_representado or "Representado",
            representado_cuit=cuit_representado or "",
            nombre_archivo=base_name or "reporte",
            cuit_representante=cuit_login or None,
        )

    def _save_b64_file(self, content_b64: str, dest_path: str) -> Tuple[bool, Optional[str]]:
        try:
            data = base64.b64decode(content_b64)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(data)
            return True, None
        except Exception as exc:
            return False, str(exc)

    def _download_variant(
        self,
        data: Dict[str, Any],
        outputs: Dict[str, bool],
        prefix: str,
        fmt: str,
        dest_dir: str,
        base_name: str,
    ) -> Tuple[bool, Optional[str]]:
        ext_map = {"excel": "xlsx", "csv": "csv", "pdf": "pdf"}
        ext = ext_map[fmt]
        minio_flag = outputs.get(f"{prefix}_{fmt}_minio")
        b64_flag = outputs.get(f"{prefix}_{fmt}_b64")
        if not minio_flag and not b64_flag:
            return False, None

        minio_key = f"{prefix}_{fmt}_url_minio"
        b64_key = f"{prefix}_{fmt}_b64"
        filename = self._ensure_extension(base_name, ext)
        dest_path = os.path.join(dest_dir, filename)

        if minio_flag and data.get(minio_key):
            res = descargar_archivo_minio(data.get(minio_key), dest_path)
            return res.get("success", False), res.get("error")
        if b64_flag and data.get(b64_key):
            ok, err = self._save_b64_file(data.get(b64_key), dest_path)
            return ok, err

        return False, "No se recibió contenido para descargar."

    def _process_downloads_per_block(
        self,
        data: Dict[str, Any],
        outputs: Dict[str, bool],
        block_config: Dict[str, Dict[str, str]],
        cuit_repr: str,
        cuit_login: str,
    ) -> Tuple[int, List[str]]:
        """
        Descarga archivos de cada bloque (deudas, vencimientos, ddjj) según outputs.
        Retorna cantidad descargada y lista de errores.
        """
        total_downloaded = 0
        errors: List[str] = []
        for prefix, cfg in block_config.items():
            if not cfg.get("enabled"):
                continue
            dest_dir = self._prepare_dir(cfg.get("path", ""), cfg.get("name", ""), cuit_repr, cuit_login)
            for fmt in ("excel", "csv", "pdf"):
                success, err = self._download_variant(data, outputs, prefix, fmt, dest_dir, cfg.get("name", prefix))
                if success:
                    total_downloaded += 1
                elif err:
                    errors.append(f"{prefix}-{fmt}: {err}")
        return total_downloaded, errors

    def build_output_flags(self, include_deuda: bool, include_vencimientos: bool, include_ddjj: bool) -> Tuple[Dict[str, bool], bool]:
        """
        Mapea las selecciones de la UI a los flags reales del endpoint SCT.
        Devuelve el payload parcial y si al menos una salida quedó habilitada.
        """
        outputs: Dict[str, bool] = {
            "vencimientos_excel_b64": False,
            "vencimientos_csv_b64": False,
            "vencimientos_pdf_b64": False,
            "vencimientos_excel_minio": False,
            "vencimientos_csv_minio": False,
            "vencimientos_pdf_minio": False,
            "deudas_excel_b64": False,
            "deudas_csv_b64": False,
            "deudas_pdf_b64": False,
            "deudas_excel_minio": False,
            "deudas_csv_minio": False,
            "deudas_pdf_minio": False,
            "ddjj_pendientes_excel_b64": False,
            "ddjj_pendientes_csv_b64": False,
            "ddjj_pendientes_pdf_b64": False,
            "ddjj_pendientes_excel_minio": False,
            "ddjj_pendientes_csv_minio": False,
            "ddjj_pendientes_pdf_minio": False,
        }

        selected = False

        def apply(prefix: str, enabled: bool) -> None:
            nonlocal selected
            if not enabled:
                return
            if self.opt_excel_b64.get():
                outputs[f"{prefix}_excel_b64"] = True
                selected = True
            if self.opt_csv_b64.get():
                outputs[f"{prefix}_csv_b64"] = True
                selected = True
            if self.opt_pdf_b64.get():
                outputs[f"{prefix}_pdf_b64"] = True
                selected = True
            if self.opt_excel_minio.get():
                outputs[f"{prefix}_excel_minio"] = True
                selected = True
            if self.opt_csv_minio.get():
                outputs[f"{prefix}_csv_minio"] = True
                selected = True
            if self.opt_pdf_minio.get():
                outputs[f"{prefix}_pdf_minio"] = True
                selected = True

        apply("deudas", include_deuda)
        apply("vencimientos", include_vencimientos)
        apply("ddjj_pendientes", include_ddjj)

        return outputs, selected

    def consulta_individual(self) -> None:
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        include_deuda = bool(self.opt_deuda.get())
        include_vencimientos = bool(self.opt_vencimientos.get())
        include_ddjj = bool(self.opt_presentacion.get())
        outputs, has_outputs = self.build_output_flags(include_deuda, include_vencimientos, include_ddjj)
        if not has_outputs:
            messagebox.showwarning(
                "Falta salida",
                "Selecciona un formato de salida (Excel/CSV/PDF) y habilita al menos un bloque (Deuda/Vencimientos/DDJJ).",
            )
            return
        payload = {
            "cuit_login": self.sct_login_var.get().strip(),
            "clave": self.sct_clave_var.get(),
            "cuit_representado": self.sct_repr_var.get().strip(),
            "proxy_request": bool(self.opt_proxy.get()),
        }
        payload.update(outputs)
        url = ensure_trailing_slash(base_url) + "api/v1/sct/consulta"
        resp = safe_post(url, headers, payload)
        self.set_preview(self.result_box, json.dumps(resp, indent=2, ensure_ascii=False))

    def cargar_excel(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        try:
            self.sct_df = pd.read_excel(filename, dtype=str).fillna("")
            self.sct_df.columns = [c.strip().lower() for c in self.sct_df.columns]
            df_prev = self.sct_df
            if "procesar" in df_prev.columns:
                df_prev = df_prev[df_prev["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
            self.set_preview(self.preview, "Excel cargado. Usa 'Previsualizar Excel'.")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")

    def procesar_excel(self) -> None:
        if self.sct_df is None or self.sct_df.empty:
            messagebox.showerror("Error", "Carga un Excel primero.")
            return
        # Verificación global por si ninguna salida está elegida
        _, has_outputs_default = self.build_output_flags(
            bool(self.opt_deuda.get()), bool(self.opt_vencimientos.get()), bool(self.opt_presentacion.get())
        )
        if not has_outputs_default:
            messagebox.showwarning(
                "Falta salida",
                "Selecciona un formato de salida (Excel/CSV/PDF) y habilita al menos un bloque (Deuda/Vencimientos/DDJJ).",
            )
            return

        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        url = ensure_trailing_slash(base_url) + "api/v1/sct/consulta"
        rows: List[Dict[str, Any]] = []
        df_to_process = self.sct_df
        if "procesar" in df_to_process.columns:
            df_to_process = df_to_process[df_to_process["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
        if df_to_process is None or df_to_process.empty:  # type: ignore[truthy-bool]
            messagebox.showwarning("Sin filas a procesar", "No hay filas marcadas con procesar=SI.")
            return

        for _, row in df_to_process.iterrows():  # type: ignore[union-attr]
            include_deuda = parse_bool_cell(row.get("deuda"), default=self.opt_deuda.get()) if "deuda" in row else bool(self.opt_deuda.get())
            include_venc = (
                parse_bool_cell(row.get("vencimientos"), default=self.opt_vencimientos.get()) if "vencimientos" in row else bool(self.opt_vencimientos.get())
            )
            include_ddjj = (
                parse_bool_cell(row.get("presentacion_ddjj"), default=self.opt_presentacion.get())
                if "presentacion_ddjj" in row
                else bool(self.opt_presentacion.get())
            )
            outputs, has_outputs = self.build_output_flags(include_deuda, include_venc, include_ddjj)
            if not has_outputs:
                rows.append(
                    {
                        "cuit_representado": str(row.get("cuit_representado", "")).strip(),
                        "http_status": None,
                        "status": "sin_salida",
                        "error_message": "Sin formato de salida seleccionado para esta fila",
                    }
                )
                continue
            # Configuración de nombres/rutas para archivos
            block_config = {
                "deudas": {
                    "enabled": include_deuda,
                    "path": str(row.get("ubicacion_deuda") or row.get("ubicacion_deudas") or ""),
                    "name": str(row.get("nombre_deuda") or row.get("nombre_deudas") or "Deudas"),
                },
                "vencimientos": {
                    "enabled": include_venc,
                    "path": str(row.get("ubicacion_vencimientos") or ""),
                    "name": str(row.get("nombre_vencimientos") or "Vencimientos"),
                },
                "ddjj_pendientes": {
                    "enabled": include_ddjj,
                    "path": str(row.get("ubicacion_ddjj") or row.get("ubicacion_presentacion_ddjj") or ""),
                    "name": str(row.get("nombre_ddjj") or row.get("nombre_presentacion_ddjj") or "DDJJ"),
                },
            }
            payload = {
                "cuit_login": str(row.get("cuit_login", "")).strip(),
                "clave": str(row.get("clave", "")),
                "cuit_representado": str(row.get("cuit_representado", "")).strip(),
                "proxy_request": bool(self.opt_proxy.get()),
            }
            payload.update(outputs)
            resp = safe_post(url, headers, payload)
            data = resp.get("data", {})
            downloads = 0
            download_errors: List[str] = []
            if isinstance(data, dict):
                downloads, download_errors = self._process_downloads_per_block(
                    data, outputs, block_config, payload["cuit_representado"], payload["cuit_login"]
                )
            rows.append(
                {
                    "cuit_representado": payload["cuit_representado"],
                    "http_status": resp.get("http_status"),
                    "status": data.get("status") if isinstance(data, dict) else None,
                    "error_message": data.get("error_message") if isinstance(data, dict) else None,
                    "descargas": downloads,
                    "errores_descarga": "; ".join(download_errors) if download_errors else None,
                }
            )
        out_df = pd.DataFrame(rows)
        self.set_preview(self.result_box, df_preview(out_df, rows=min(20, len(out_df))))


# =========================
# Ventana CCMA
# =========================
class CcmaWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Cuenta Corriente (CCMA)")
        self.config_provider = config_provider
        self.example_paths = example_paths or {}
        self.ccma_df: Optional[pd.DataFrame] = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        self.add_section_label(container, "Cuenta Corriente de Monotributistas y Autonomos (CCMA)")
        self.add_info_label(container, "Consulta individual o masiva basada en Excel.")

        inputs = ttk.Frame(container)
        inputs.pack(fill="x", pady=4)
        ttk.Label(inputs, text="CUIT representante").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="Clave representante").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(inputs, text="CUIT representado").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        self.cuit_rep_var = tk.StringVar()
        self.clave_rep_var = tk.StringVar()
        self.cuit_repr_var = tk.StringVar()
        ttk.Entry(inputs, textvariable=self.cuit_rep_var, width=25).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.clave_rep_var, width=25, show="*").grid(row=1, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(inputs, textvariable=self.cuit_repr_var, width=25).grid(row=2, column=1, padx=4, pady=2, sticky="ew")
        inputs.columnconfigure(1, weight=1)

        self.opt_proxy = tk.BooleanVar(value=False)
        ttk.Checkbutton(container, text="proxy_request", variable=self.opt_proxy).pack(anchor="w", pady=2)

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Consultar individual", command=self.consulta_individual).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Seleccionar Excel", command=self.cargar_excel).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Ejemplo Excel", command=self.abrir_ejemplo).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Previsualizar Excel", command=lambda: self.open_df_preview(self.ccma_df, "Previsualización CCMA")).grid(row=0, column=3, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Procesar Excel", command=self.procesar_excel).grid(row=1, column=0, columnspan=4, padx=4, pady=6, sticky="ew")
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        self.preview = self.add_preview(container, height=8, show=False)
        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.preview, "Excel no cargado o sin previsualizar. Usa 'Previsualizar Excel'.")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("ccma.xlsx")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    def cargar_excel(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        try:
            self.ccma_df = pd.read_excel(filename, dtype=str).fillna("")
            self.ccma_df.columns = [c.strip().lower() for c in self.ccma_df.columns]
            df_prev = self.ccma_df
            if "procesar" in df_prev.columns:
                df_prev = df_prev[df_prev["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
            self.set_preview(self.preview, df_preview(df_prev))
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")

    def consulta_individual(self) -> None:
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        payload = {
            "cuit_representante": self.cuit_rep_var.get().strip(),
            "clave_representante": self.clave_rep_var.get(),
            "cuit_representado": self.cuit_repr_var.get().strip(),
            "proxy_request": bool(self.opt_proxy.get()),
        }
        url = ensure_trailing_slash(base_url) + "api/v1/ccma/consulta"
        resp = safe_post(url, headers, payload)
        self.set_preview(self.result_box, json.dumps(resp, indent=2, ensure_ascii=False))

    def procesar_excel(self) -> None:
        if self.ccma_df is None or self.ccma_df.empty:
            messagebox.showerror("Error", "Carga un Excel primero.")
            return
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        url = ensure_trailing_slash(base_url) + "api/v1/ccma/consulta"
        rows: List[Dict[str, Any]] = []
        df_to_process = self.ccma_df
        if "procesar" in df_to_process.columns:
            df_to_process = df_to_process[df_to_process["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
        if df_to_process is None or df_to_process.empty:  # type: ignore[truthy-bool]
            messagebox.showwarning("Sin filas a procesar", "No hay filas marcadas con procesar=SI.")
            return

        for _, row in df_to_process.iterrows():  # type: ignore[union-attr]
            payload = {
                "cuit_representante": str(row.get("cuit_representante", "")).strip(),
                "clave_representante": str(row.get("clave_representante", "")),
                "cuit_representado": str(row.get("cuit_representado", "")).strip(),
                "proxy_request": bool(self.opt_proxy.get()),
            }
            resp = safe_post(url, headers, payload)
            data = resp.get("data", {})
            rows.append(
                {
                    "cuit_representado": payload["cuit_representado"],
                    "http_status": resp.get("http_status"),
                    "status": data.get("status") if isinstance(data, dict) else None,
                    "error_message": data.get("error_message") if isinstance(data, dict) else None,
                }
            )
        out_df = pd.DataFrame(rows)
        self.set_preview(self.result_box, df_preview(out_df, rows=min(20, len(out_df))))


# =========================
# Ventana Apocrifos
# =========================
class ApocrifosWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Consulta de Apocrifos")
        self.config_provider = config_provider
        self.example_paths = example_paths or {}
        self.apoc_df: Optional[pd.DataFrame] = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        self.add_section_label(container, "Consulta de Apocrifos")
        self.add_info_label(container, "Consulta individual o masiva de CUITs.")

        inputs = ttk.Frame(container)
        inputs.pack(fill="x", pady=4)
        ttk.Label(inputs, text="CUIT individual").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.cuit_var = tk.StringVar()
        ttk.Entry(inputs, textvariable=self.cuit_var, width=25).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        inputs.columnconfigure(1, weight=1)

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Consultar individual", command=self.consulta_individual).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Seleccionar Excel", command=self.cargar_excel).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Ejemplo Excel", command=self.abrir_ejemplo).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Procesar Excel", command=self.procesar_excel).grid(row=1, column=0, columnspan=3, padx=4, pady=6, sticky="ew")
        btns.columnconfigure((0, 1, 2), weight=1)

        self.preview = self.add_preview(container, height=8)
        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.preview, "Vista previa del Excel (primeras filas).")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("apocrifos.xlsx")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    def cargar_excel(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        try:
            self.apoc_df = pd.read_excel(filename, dtype=str).fillna("")
            self.set_preview(self.preview, df_preview(self.apoc_df))
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")

    def consulta_individual(self) -> None:
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        cuit = self.cuit_var.get().strip()
        url = ensure_trailing_slash(base_url) + f"api/v1/apoc/consulta/{cuit}"
        resp = safe_get(url, headers)
        self.set_preview(self.result_box, json.dumps(resp, indent=2, ensure_ascii=False))

    def procesar_excel(self) -> None:
        if self.apoc_df is None or self.apoc_df.empty:
            messagebox.showerror("Error", "Carga un Excel primero.")
            return
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        rows: List[Dict[str, Any]] = []
        for _, row in self.apoc_df.iterrows():
            cuit = str(row.get("cuit", "")).strip()
            url = ensure_trailing_slash(base_url) + f"api/v1/apoc/consulta/{cuit}"
            resp = safe_get(url, headers)
            data = resp.get("data", {})
            rows.append(
                {
                    "cuit": cuit,
                    "http_status": resp.get("http_status"),
                    "apoc": data.get("apoc") if isinstance(data, dict) else None,
                    "message": data.get("message") if isinstance(data, dict) else None,
                }
            )
        out_df = pd.DataFrame(rows)
        self.set_preview(self.result_box, df_preview(out_df, rows=min(20, len(out_df))))


# =========================
# Ventana Consulta de CUIT
# =========================
class ConsultaCuitWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Consulta de CUIT")
        self.config_provider = config_provider
        self.example_paths = example_paths or {}
        self.cuit_df: Optional[pd.DataFrame] = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        self.add_section_label(container, "Consulta de constancia de CUIT")
        self.add_info_label(container, "Consulta individual o masiva.")

        inputs = ttk.Frame(container)
        inputs.pack(fill="x", pady=4)
        ttk.Label(inputs, text="CUIT individual").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.cuit_var = tk.StringVar()
        ttk.Entry(inputs, textvariable=self.cuit_var, width=25).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        inputs.columnconfigure(1, weight=1)

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Consultar individual", command=self.consulta_individual).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Seleccionar Excel", command=self.cargar_excel).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Ejemplo Excel", command=self.abrir_ejemplo).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Procesar Excel", command=self.procesar_excel).grid(row=1, column=0, columnspan=3, padx=4, pady=6, sticky="ew")
        btns.columnconfigure((0, 1, 2), weight=1)

        self.preview = self.add_preview(container, height=8)
        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.preview, "Vista previa del Excel (primeras filas).")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("consulta_cuit.xlsx")
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

    def cargar_excel(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        try:
            self.cuit_df = pd.read_excel(filename, dtype=str).fillna("")
            self.set_preview(self.preview, df_preview(self.cuit_df))
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")

    def consulta_individual(self) -> None:
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        payload = {"cuit": self.cuit_var.get().strip()}
        url = ensure_trailing_slash(base_url) + "api/v1/consulta_cuit/individual"
        resp = safe_post(url, headers, payload)
        self.set_preview(self.result_box, json.dumps(resp, indent=2, ensure_ascii=False))

    def procesar_excel(self) -> None:
        if self.cuit_df is None or self.cuit_df.empty:
            messagebox.showerror("Error", "Carga un Excel primero.")
            return
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        url = ensure_trailing_slash(base_url) + "api/v1/consulta_cuit/masivo"
        cuits = [str(row.get("cuit", "")).strip() for _, row in self.cuit_df.iterrows() if str(row.get("cuit", "")).strip()]
        payload = {"cuits": cuits}
        resp = safe_post(url, headers, payload)
        data = resp.get("data", {})
        rows: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            # Si la API devuelve detalle por cuit, guardarlo
            detail = data.get("results") or data.get("data")
            if isinstance(detail, list):
                for item in detail:
                    rows.append(item if isinstance(item, dict) else {"item": item})
        out_df = pd.DataFrame(rows) if rows else pd.DataFrame([data])
        self.set_preview(self.result_box, df_preview(out_df, rows=min(20, len(out_df))))


# =========================
# Ventana principal
# =========================
class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Herramientas API Mr Bot")
        self.configure(background=BG)
        self.resizable(False, False)

        # Estilos oscuros para matchear el ejemplo
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TButton", foreground="#000000")
        style.configure("TCheckbutton", background=BG, foreground=FG)

        self.example_paths = ensure_example_excels()

        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        logo_path = os.path.join("bin", "MrBot.png")
        self.logo_img = None
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                tk.Label(header, image=self.logo_img, background=BG).pack(side="top", pady=(0, 8))
            except Exception:
                self.logo_img = None
        title_lbl = ttk.Label(header, text="MR BOT - Cliente API", font=("Arial", 16, "bold"), foreground=FG, background=BG)
        title_lbl.pack(anchor="center")
        subtitle = ttk.Label(header, text="Consultas y descargas de la API api-bots.mrbot.com.ar", foreground=FG, background=BG)
        subtitle.pack(anchor="center")

        self.config_pane = ConfigPane(self)
        self.config_pane.pack(fill="x", padx=10, pady=6)

        btns = ttk.Frame(self, padding=10)
        btns.pack(fill="both", expand=True)

        ttk.Button(btns, text="Descarga Mis Comprobantes", command=self.open_mis_comprobantes).grid(row=0, column=0, padx=6, pady=4, sticky="ew")
        ttk.Button(btns, text="Comprobantes en Linea (RCEL)", command=self.open_rcel).grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        ttk.Button(btns, text="Sistema de Cuentas Tributarias (SCT)", command=self.open_sct).grid(row=1, column=0, padx=6, pady=4, sticky="ew")
        ttk.Button(btns, text="Cuenta Corriente (CCMA)", command=self.open_ccma).grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        ttk.Button(btns, text="Consulta Apocrifos", command=self.open_apoc).grid(row=2, column=0, padx=6, pady=4, sticky="ew")
        ttk.Button(btns, text="Consulta de CUIT", command=self.open_cuit).grid(row=2, column=1, padx=6, pady=4, sticky="ew")

        btns.columnconfigure((0, 1), weight=1)

    def current_config(self) -> Tuple[str, str, str]:
        return self.config_pane.get_config()

    # Lanzadores de ventanas
    def open_mis_comprobantes(self) -> None:
        GuiDescargaMC(self, self.config_pane, self.example_paths)

    def open_rcel(self) -> None:
        RcelWindow(self, self.current_config, self.example_paths)

    def open_sct(self) -> None:
        SctWindow(self, self.current_config, self.example_paths)

    def open_ccma(self) -> None:
        CcmaWindow(self, self.current_config, self.example_paths)

    def open_apoc(self) -> None:
        ApocrifosWindow(self, self.current_config, self.example_paths)

    def open_cuit(self) -> None:
        ConsultaCuitWindow(self, self.current_config, self.example_paths)


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
