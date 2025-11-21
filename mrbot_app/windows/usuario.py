import json
from typing import Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from mrbot_app.config import DEFAULT_API_KEY, DEFAULT_BASE_URL, DEFAULT_EMAIL
from mrbot_app.helpers import build_headers, ensure_trailing_slash, safe_get, safe_post
from mrbot_app.windows.base import BaseWindow


class UsuarioWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None):
        super().__init__(master, title="Usuarios")
        self.config_provider = config_provider

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        self.add_section_label(container, "Gestión de usuarios")
        self.add_info_label(
            container,
            "Crear usuarios, resetear la API Key y consultar requests restantes usando el mail ingresado.",
        )

        mail_frame = ttk.Frame(container)
        mail_frame.pack(fill="x", pady=4)
        ttk.Label(mail_frame, text="Mail").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(mail_frame, text="API Key").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        self.email_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        ttk.Entry(mail_frame, textvariable=self.email_var, width=40).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Entry(mail_frame, textvariable=self.api_key_var, width=40, show="*").grid(row=1, column=1, padx=4, pady=2, sticky="ew")
        mail_frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Crear usuario", command=self.crear_usuario).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Resetear API Key", command=self.resetear_api_key).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(btns, text="Consultas restantes", command=self.consultas_restantes).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        btns.columnconfigure((0, 1, 2), weight=1)

        self.result_box = self.add_preview(container, height=12)
        self.set_preview(self.result_box, "Resultados de la API aparecerán aquí.")
        self._sync_with_config()

    def _sync_with_config(self) -> None:
        _, api_key, email = self._get_config()
        if email:
            self.email_var.set(email)
        if api_key:
            self.api_key_var.set(api_key)

    def _get_config(self) -> Tuple[str, str, str]:
        if self.config_provider:
            return self.config_provider()
        return DEFAULT_BASE_URL, DEFAULT_API_KEY, DEFAULT_EMAIL

    def _collect_inputs(self) -> Optional[Tuple[str, str, str]]:
        base_url, api_key_cfg, email_cfg = self._get_config()
        email = (self.email_var.get() or email_cfg).strip()
        api_key = (self.api_key_var.get() or api_key_cfg).strip()
        if not email:
            messagebox.showerror("Mail requerido", "Ingresa un mail para continuar.")
            return None
        clean_base = ensure_trailing_slash(base_url or DEFAULT_BASE_URL)
        self.email_var.set(email)
        self.api_key_var.set(api_key)
        return clean_base, api_key, email

    def _show_response(self, resp: dict) -> None:
        pretty = json.dumps(resp or {}, indent=2, ensure_ascii=False)
        self.set_preview(self.result_box, pretty)

    def crear_usuario(self) -> None:
        collected = self._collect_inputs()
        if not collected:
            return
        base_url, api_key, email = collected
        headers = build_headers(api_key, email)
        url = base_url + "api/v1/user/"
        payload = {"mail": email}
        resp = safe_post(url, headers, payload)
        self._show_response(resp)

    def resetear_api_key(self) -> None:
        collected = self._collect_inputs()
        if not collected:
            return
        base_url, api_key, email = collected
        headers = build_headers(api_key, email)
        url = base_url + f"api/v1/user/reset-key/?email={email}"
        resp = safe_post(url, headers, payload={})
        self._show_response(resp)

    def consultas_restantes(self) -> None:
        collected = self._collect_inputs()
        if not collected:
            return
        base_url, api_key, email = collected
        headers = build_headers(api_key, email)
        url = base_url + f"api/v1/user/consultas/{email}"
        resp = safe_get(url, headers)
        self._show_response(resp)
