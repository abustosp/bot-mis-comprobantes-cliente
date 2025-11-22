import os
import tkinter as tk
from tkinter import ttk, messagebox

from mrbot_app.config import ENV_FILE
from mrbot_app.constants import BG, FG
from mrbot_app.examples import ensure_example_excels
from mrbot_app.files import open_with_default_app
from mrbot_app.windows import (
    ApocrifosWindow,
    CcmaWindow,
    ConsultaCuitWindow,
    GuiDescargaMC,
    RcelWindow,
    SctWindow,
    UsuarioWindow,
)
from mrbot_app.windows.base import ConfigPane


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Herramientas API Mr Bot")
        try:
            self.iconbitmap(os.path.join("bin", "ABP-blanco-en-fondo-negro.ico"))
        except Exception:
            pass
        self.configure(background=BG)
        self.resizable(False, False)

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

        btn_width = 28

        env_btns = ttk.Frame(self, padding=(10, 0))
        env_btns.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Button(env_btns, text="Editar .env", width=btn_width, command=self.open_env_file).grid(row=0, column=0, padx=4, pady=2, sticky="nsew")
        ttk.Button(env_btns, text="Recargar .env", width=btn_width, command=self.reload_env_values).grid(row=0, column=1, padx=4, pady=2, sticky="nsew")
        env_btns.columnconfigure((0, 1), weight=1, uniform="env")

        btns = ttk.Frame(self, padding=10)
        btns.pack(fill="both", expand=True)

        ttk.Button(btns, text="Descarga Mis Comprobantes", width=btn_width, command=self.open_mis_comprobantes).grid(row=0, column=0, padx=6, pady=4, sticky="nsew")
        ttk.Button(btns, text="Comprobantes en Linea (RCEL)", width=btn_width, command=self.open_rcel).grid(row=0, column=1, padx=6, pady=4, sticky="nsew")
        ttk.Button(btns, text="Sistema de Cuentas Tributarias (SCT)", width=btn_width, command=self.open_sct).grid(row=1, column=0, padx=6, pady=4, sticky="nsew")
        ttk.Button(btns, text="Cuenta Corriente (CCMA)", width=btn_width, command=self.open_ccma).grid(row=1, column=1, padx=6, pady=4, sticky="nsew")
        ttk.Button(btns, text="Consulta Apocrifos", width=btn_width, command=self.open_apoc).grid(row=2, column=0, padx=6, pady=4, sticky="nsew")
        ttk.Button(btns, text="Consulta de CUIT", width=btn_width, command=self.open_cuit).grid(row=2, column=1, padx=6, pady=4, sticky="nsew")
        ttk.Button(btns, text="Usuarios", width=btn_width, command=self.open_usuario).grid(row=3, column=0, columnspan=2, padx=6, pady=4, sticky="nsew")

        btns.columnconfigure((0, 1), weight=1, uniform="menu")
        for r in range(4):
            btns.rowconfigure(r, weight=1)

    def current_config(self) -> tuple[str, str, str]:
        return self.config_pane.get_config()

    def open_env_file(self) -> None:
        env_path = os.path.abspath(ENV_FILE)
        if not os.path.exists(env_path):
            try:
                with open(env_path, "w", encoding="utf-8") as fh:
                    fh.write("# URL=https://api-bots.mrbot.com.ar/\n# API_KEY=\n# MAIL=\n")
            except Exception as exc:
                messagebox.showerror("Error", f"No se pudo crear {env_path}: {exc}")
                return
        if not open_with_default_app(env_path):
            messagebox.showerror("Error", f"No se pudo abrir {env_path}. Edita el archivo manualmente.")

    def reload_env_values(self) -> None:
        base_url, api_key, email = self.config_pane.load_from_env()
        messagebox.showinfo(
            "Configuración recargada",
            f"Se recargaron valores de {os.path.abspath(ENV_FILE)}.\n\nURL: {base_url}\nMail: {email}\n(API_KEY oculto)",
        )

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

    def open_usuario(self) -> None:
        UsuarioWindow(self, self.current_config)


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
