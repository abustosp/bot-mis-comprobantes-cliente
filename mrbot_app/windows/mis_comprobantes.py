import contextlib
import io
import json
import os
import sys
from typing import Dict, Optional

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bin.consulta import consulta_mc_csv
from mrbot_app.config import DEFAULT_API_KEY, DEFAULT_BASE_URL, DEFAULT_EMAIL
from mrbot_app.files import open_with_default_app
from mrbot_app.helpers import build_headers, ensure_trailing_slash, safe_get
from mrbot_app.windows.base import BaseWindow


class GuiDescargaMC(BaseWindow):
    def __init__(self, master=None, config_pane: Optional[ttk.Frame] = None, example_paths: Optional[Dict[str, str]] = None):
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
        if not path:
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if not open_with_default_app(path):
            messagebox.showerror("Error", "No se pudo abrir el Excel de ejemplo.")

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
