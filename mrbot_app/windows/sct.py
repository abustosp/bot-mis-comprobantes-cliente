import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bin.consulta import descargar_archivo_minio
from mrbot_app.files import open_with_default_app
from mrbot_app.helpers import (
    build_headers,
    df_preview,
    ensure_trailing_slash,
    parse_bool_cell,
    safe_post,
)
from mrbot_app.windows.base import BaseWindow


class SctWindow(BaseWindow):
    def __init__(self, master=None, config_provider=None, example_paths: Optional[Dict[str, str]] = None):
        super().__init__(master, title="Sistema de Cuentas Tributarias (SCT)")
        try:
            self.iconbitmap(os.path.join("bin", "ABP-blanco-en-fondo-negro.ico"))
        except Exception:
            pass
        self.config_provider = config_provider
        self.example_paths = example_paths or {}
        self.sct_df: Optional[pd.DataFrame] = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        self.add_section_label(container, "Sistema de Cuentas Tributarias (SCT)")
        self.add_info_label(container, "Consulta individual o masiva. Formatos disponibles: Excel/CSV/PDF en base64 o subida a MinIO.")

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
        ttk.Checkbutton(opts, text="Excel base64", variable=self.opt_excel_b64, state="disabled").grid(row=0, column=1, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="CSV MinIO", variable=self.opt_csv_minio).grid(row=1, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="CSV base64", variable=self.opt_csv_b64, state="disabled").grid(row=1, column=1, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="PDF MinIO", variable=self.opt_pdf_minio).grid(row=2, column=0, padx=4, pady=2, sticky="w")
        ttk.Checkbutton(opts, text="PDF base64", variable=self.opt_pdf_b64, state="disabled").grid(row=2, column=1, padx=4, pady=2, sticky="w")
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
        path = self.example_paths.get("sct.xlsx")
        if not path:
            messagebox.showerror("Error", "No se encontro el Excel de ejemplo.")
            return
        if not open_with_default_app(path):
            messagebox.showerror("Error", "No se pudo abrir el Excel de ejemplo.")

    def clear_logs(self) -> None:
        if not hasattr(self, "log_text") or self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def _format_log_line(self, text: str, prefix: str, style: Optional[str]) -> str:
        body = f"{prefix}{text}".rstrip("\n")
        main_sep = "=" * 64
        sub_sep = "-" * 64

        if style == "header":
            return f"\n{main_sep}\n{body}\n{main_sep}\n"
        if style == "section":
            return f"\n{sub_sep}\n{body}\n"
        if style == "bullet":
            return f"  - {body}\n"
        if style == "success":
            return f"  [OK] {body}\n"
        if style == "error":
            return f"  [ERROR] {body}\n{sub_sep}\n"
        if style == "raw":
            return body
        return body + ("\n" if not body.endswith("\n") else "")

    def append_log(self, text: str, prefix: str = "", style: Optional[str] = None) -> None:
        if not text:
            return
        formatted = self._format_log_line(text, prefix, style)
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, formatted)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self.log_text.update_idletasks()

    def _redact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        safe = dict(payload)
        if "clave" in safe:
            safe["clave"] = "***"
        return safe

    def _ensure_extension(self, name: str, ext: str) -> str:
        clean = (name or "").strip()
        if not clean:
            clean = "reporte"
        if not clean.lower().endswith(f".{ext}"):
            clean = f"{clean}.{ext}"
        return clean

    def _sanitize_identifier(self, value: str, fallback: str = "desconocido") -> str:
        cleaned = re.sub(r"[^0-9A-Za-z._-]", "_", (value or "").strip())
        cleaned = cleaned.strip("_")
        return cleaned or fallback

    def _is_writable_dir(self, path: str) -> bool:
        try:
            if not path:
                return False
            os.makedirs(path, exist_ok=True)
            probe = os.path.join(path, ".mrbot_write_test")
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write("ok")
            os.remove(probe)
            return True
        except Exception:
            return False

    def _prepare_dir(self, desired_path: str, base_name: str, cuit_representado: str, cuit_login: str) -> str:
        return (desired_path or "").strip()

    def _download_variant(
        self,
        data: Dict[str, Any],
        outputs: Dict[str, bool],
        prefix: str,
        fmt: str,
        dest_dir: str,
        base_name: str,
        cuit_repr: str,
    ) -> Tuple[bool, Optional[str]]:
        ext_map = {"excel": "xlsx", "csv": "csv", "pdf": "pdf"}
        ext = ext_map[fmt]
        minio_flag = outputs.get(f"{prefix}_{fmt}_minio")
        if not minio_flag:
            return False, None

        minio_keys = [f"{prefix}_{fmt}_minio_url", f"{prefix}_{fmt}_url_minio"]
        url = None
        for key in minio_keys:
            candidate = data.get(key)
            if isinstance(candidate, str):
                candidate = candidate.strip()
            if candidate:
                url = candidate
                break
        if not url:
            return False, f"Link inexistente o vacío ({' / '.join(minio_keys)})"

        filename = self._ensure_extension(base_name, ext)
        desired_dir = (dest_dir or "").strip()
        candidate_dirs: List[Tuple[str, bool]] = []
        dir_errors: List[str] = []

        if desired_dir:
            if self._is_writable_dir(desired_dir):
                candidate_dirs.append((desired_dir, False))
            else:
                dir_errors.append(f"No se pudo usar el directorio indicado '{desired_dir}'")

        fallback_dir = os.path.join("descargas", "SCT", self._sanitize_identifier(cuit_repr or "desconocido"))
        if fallback_dir not in {d for d, _ in candidate_dirs}:
            if self._is_writable_dir(fallback_dir):
                candidate_dirs.append((fallback_dir, True))
            else:
                dir_errors.append(f"No se pudo preparar el directorio fallback '{fallback_dir}'")

        if not candidate_dirs:
            return False, "; ".join(dir_errors) if dir_errors else "No hay rutas disponibles para descargar"

        last_error: Optional[str] = None
        for target_dir, _is_fallback in candidate_dirs:
            target_path = os.path.join(target_dir, filename)
            res = descargar_archivo_minio(url, target_path)
            if res.get("success"):
                return True, None
            last_error = res.get("error") or f"Error al descargar en {target_path}"

        error_msgs = dir_errors.copy()
        if last_error:
            error_msgs.append(last_error)
        return False, "; ".join(error_msgs) if error_msgs else "No se pudo completar la descarga"

    def _process_downloads_per_block(
        self,
        data: Dict[str, Any],
        outputs: Dict[str, bool],
        block_config: Dict[str, Dict[str, str]],
        cuit_repr: str,
        cuit_login: str,
    ) -> Tuple[int, List[str]]:
        total_downloaded = 0
        errors: List[str] = []
        for prefix, cfg in block_config.items():
            if not cfg.get("enabled"):
                continue
            dest_dir = self._prepare_dir(cfg.get("path", ""), cfg.get("name", ""), cuit_repr, cuit_login)
            for fmt in ("excel", "csv", "pdf"):
                success, err = self._download_variant(data, outputs, prefix, fmt, dest_dir, cfg.get("name", prefix), cuit_repr)
                if success:
                    total_downloaded += 1
                elif err:
                    errors.append(f"{prefix}-{fmt}: {err}")
        return total_downloaded, errors

    def _filter_procesar_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        if "procesar" not in df.columns:
            return df
        mask = df["procesar"].astype(str).str.lower().isin(["si", "sí", "yes", "y", "1"])
        return df[mask]

    def _row_format_flags(self, row: Optional[pd.Series] = None, prefer_row: bool = False) -> Tuple[bool, bool, bool]:
        excel_enabled = bool(self.opt_excel_minio.get())
        csv_enabled = bool(self.opt_csv_minio.get())
        pdf_enabled = bool(self.opt_pdf_minio.get())

        if row is not None:
            def pick(key: str, current: bool) -> bool:
                if key in row:
                    value = row.get(key)
                    if value is None or str(value).strip() == "":
                        return current if not prefer_row else False
                    return parse_bool_cell(value, default=current if not prefer_row else False)
                return current if not prefer_row else current

            excel_enabled = pick("excel", excel_enabled)
            csv_enabled = pick("csv", csv_enabled)
            pdf_enabled = pick("pdf", pdf_enabled)

        return excel_enabled, csv_enabled, pdf_enabled

    def build_output_flags(
        self,
        include_deuda: bool,
        include_vencimientos: bool,
        include_ddjj: bool,
        excel_enabled: bool,
        csv_enabled: bool,
        pdf_enabled: bool,
    ) -> Tuple[Dict[str, bool], bool]:
        outputs: Dict[str, bool] = {
            "vencimientos_excel_minio": False,
            "vencimientos_csv_minio": False,
            "vencimientos_pdf_minio": False,
            "deudas_excel_minio": False,
            "deudas_csv_minio": False,
            "deudas_pdf_minio": False,
            "ddjj_pendientes_excel_minio": False,
            "ddjj_pendientes_csv_minio": False,
            "ddjj_pendientes_pdf_minio": False,
        }

        selected = False

        def apply(prefix: str, enabled: bool) -> None:
            nonlocal selected
            if not enabled:
                return
            if excel_enabled:
                outputs[f"{prefix}_excel_minio"] = True
                selected = True
            if csv_enabled:
                outputs[f"{prefix}_csv_minio"] = True
                selected = True
            if pdf_enabled:
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
        excel_fmt, csv_fmt, pdf_fmt = self._row_format_flags()
        outputs, has_outputs = self.build_output_flags(include_deuda, include_vencimientos, include_ddjj, excel_fmt, csv_fmt, pdf_fmt)
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
        self.clear_logs()
        self.append_log("Consulta individual SCT", style="header")
        self.append_log(f"Payload: {json.dumps(self._redact(payload), ensure_ascii=False)}", style="bullet")
        resp = safe_post(url, headers, payload)
        self.append_log(f"HTTP {resp.get('http_status')}: {json.dumps(resp.get('data'), ensure_ascii=False)}", style="section")
        self.set_preview(self.result_box, json.dumps(resp, indent=2, ensure_ascii=False))

    def cargar_excel(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        try:
            df = pd.read_excel(filename, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            df = self._filter_procesar_rows(df)
            if df.empty:
                self.sct_df = None
                self.set_preview(self.preview, "Sin filas marcadas con procesar=SI en el Excel seleccionado.")
                messagebox.showwarning("Sin filas a procesar", "No hay filas marcadas con procesar=SI en el Excel.")
                return
            self.sct_df = df
            self.set_preview(self.preview, df_preview(df, rows=min(20, len(df))))
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el Excel: {exc}")

    def procesar_excel(self) -> None:
        if self.sct_df is None or self.sct_df.empty:
            messagebox.showerror("Error", "Carga un Excel primero.")
            return
        base_url, api_key, email = self.config_provider()
        headers = build_headers(api_key, email)
        url = ensure_trailing_slash(base_url) + "api/v1/sct/consulta"
        rows: List[Dict[str, Any]] = []
        df_to_process = self.sct_df
        if "procesar" in df_to_process.columns:
            df_to_process = df_to_process[df_to_process["procesar"].str.lower().isin(["si", "sí", "yes", "y", "1"])]
        if df_to_process is None or df_to_process.empty:
            messagebox.showwarning("Sin filas a procesar", "No hay filas marcadas con procesar=SI.")
            return

        self.clear_logs()
        self.append_log(f"Procesando {len(df_to_process)} filas SCT", style="header")
        for _, row in df_to_process.iterrows():
            include_deuda = parse_bool_cell(row.get("deuda"), default=self.opt_deuda.get()) if "deuda" in row else bool(self.opt_deuda.get())
            include_venc = (
                parse_bool_cell(row.get("vencimientos"), default=self.opt_vencimientos.get()) if "vencimientos" in row else bool(self.opt_vencimientos.get())
            )
            include_ddjj = (
                parse_bool_cell(row.get("presentacion_ddjj"), default=self.opt_presentacion.get())
                if "presentacion_ddjj" in row
                else bool(self.opt_presentacion.get())
            )
            excel_fmt, csv_fmt, pdf_fmt = self._row_format_flags(row, prefer_row=True)
            outputs, has_outputs = self.build_output_flags(include_deuda, include_venc, include_ddjj, excel_fmt, csv_fmt, pdf_fmt)
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
            self.append_log(f"Fila {payload['cuit_representado']}", style="section")
            self.append_log(f"Bloques activos -> deuda={include_deuda}, vencimientos={include_venc}, ddjj={include_ddjj}", style="bullet")
            self.append_log(f"Salidas solicitadas -> {json.dumps(outputs, ensure_ascii=False)}", style="bullet")
            resp = safe_post(url, headers, payload)
            data = resp.get("data", {})
            self.append_log(f"HTTP {resp.get('http_status')}: {json.dumps(data, ensure_ascii=False)}", style="bullet")
            downloads = 0
            download_errors: List[str] = []
            if isinstance(data, dict):
                downloads, download_errors = self._process_downloads_per_block(
                    data, outputs, block_config, payload["cuit_representado"], payload["cuit_login"]
                )
            if downloads:
                self.append_log(f"Descargas completadas: {downloads}", style="success")
            for err in download_errors:
                self.append_log(f"Descarga con error: {err}", style="error")
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
