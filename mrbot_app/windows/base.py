import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

import pandas as pd

from mrbot_app.config import DEFAULT_API_KEY, DEFAULT_BASE_URL, DEFAULT_EMAIL
from mrbot_app.constants import BG, FG
from mrbot_app.helpers import _format_dates_str


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

    def get_config(self) -> tuple[str, str, str]:
        return self.base_url_var.get().strip(), self.api_key_var.get().strip(), self.email_var.get().strip()
