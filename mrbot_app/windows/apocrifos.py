import json
from typing import Any, Dict, List, Optional
import os

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from mrbot_app.files import open_with_default_app
from mrbot_app.helpers import build_headers, df_preview, ensure_trailing_slash, safe_get
from mrbot_app.windows.base import BaseWindow


class ApocrifosWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Consulta de Apocrifos")
        try:
            self.iconbitmap(os.path.join("bin", "ABP-blanco-en-fondo-negro.ico"))
        except Exception:
            pass
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
