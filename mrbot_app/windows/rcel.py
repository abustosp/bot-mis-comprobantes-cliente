import json
import os
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from mrbot_app.files import open_with_default_app
from mrbot_app.helpers import build_headers, df_preview, ensure_trailing_slash, make_today_str, safe_post
from mrbot_app.windows.base import BaseWindow


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
        ttk.Label(dates_frame, text="Hasta (DD/MM/AAAA)").grid(row=1, column=0, padx=4, pady=2, sticky="w")
        self.desde_var = tk.StringVar(value=f"01/01/{date.today().year}")
        self.hasta_var = tk.StringVar(value=make_today_str())
        ttk.Entry(dates_frame, textvariable=self.desde_var, width=15).grid(row=0, column=1, padx=4, pady=2, sticky="w")
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

        log_frame = ttk.LabelFrame(container, text="Logs de ejecución")
        log_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.log_text = tk.Text(
            log_frame,
            height=10,
            wrap="word",
            background="#1b1b1b",
            foreground="#dcdcdc",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("rcel.xlsx")
        if not path:
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if not open_with_default_app(path):
            messagebox.showerror("Error", "No se pudo abrir el Excel de ejemplo.")

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
            self.rcel_df = None

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

    def _redact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        safe = dict(payload)
        if "clave" in safe:
            safe["clave"] = "***"
        return safe

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
        self.clear_logs()
        self.append_log(f"Consulta individual RCEL: {json.dumps(self._redact(payload), ensure_ascii=False)}\n")
        resp = safe_post(url, headers, payload)
        self.append_log(f"Respuesta HTTP {resp.get('http_status')}: {json.dumps(resp.get('data'), ensure_ascii=False)}\n")
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

        self.clear_logs()
        self.append_log(f"Procesando {len(df_to_process)} filas RCEL\n")
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
            self.append_log(f"- Fila {payload['representado_cuit']}: payload {json.dumps(self._redact(payload), ensure_ascii=False)}\n")
            resp = safe_post(url, headers, payload)
            data = resp.get("data", {})
            self.append_log(f"  -> HTTP {resp.get('http_status')}: {json.dumps(data, ensure_ascii=False)}\n")
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
