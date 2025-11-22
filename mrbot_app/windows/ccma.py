import json
from typing import Any, Dict, List, Optional
import os

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from mrbot_app.files import open_with_default_app
from mrbot_app.helpers import build_headers, df_preview, ensure_trailing_slash, safe_post
from mrbot_app.windows.base import BaseWindow


class CcmaWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Cuenta Corriente (CCMA)")
        try:
            self.iconbitmap(os.path.join("bin", "ABP-blanco-en-fondo-negro.ico"))
        except Exception:
            pass
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
        ttk.Button(btns, text="Previsualizar Excel", command=lambda: self.open_df_preview((self.ccma_df[self.ccma_df["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]) if (self.ccma_df is not None and "procesar" in self.ccma_df.columns) else self.ccma_df, "Previsualización CCMA")).grid(row=0, column=3, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Procesar Excel", command=self.procesar_excel).grid(row=1, column=0, columnspan=4, padx=4, pady=6, sticky="ew")
        btns.columnconfigure((0, 1, 2, 3), weight=1)

        self.preview = self.add_preview(container, height=8, show=False)
        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.preview, "Excel no cargado o sin previsualizar. Usa 'Previsualizar Excel'.")

        log_frame = ttk.LabelFrame(container, text="Logs de ejecución")
        log_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.log_text = tk.Text(
            log_frame,
            height=12,
            wrap="word",
            background="#1b1b1b",
            foreground="#dcdcdc",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def abrir_ejemplo(self) -> None:
        path = self.example_paths.get("ccma.xlsx")
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
        if df_to_process is None or df_to_process.empty:
            messagebox.showwarning("Sin filas a procesar", "No hay filas marcadas con procesar=SI.")
            return

        for _, row in df_to_process.iterrows():
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
