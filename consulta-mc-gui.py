#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from bin.consulta import consulta_mc_csv
import os
import webbrowser
from dotenv import load_dotenv
from tkinter import messagebox

load_dotenv()

class GuiDescargaMC:
    def __init__(self, master=None):
        # build ui
        self.Toplevel_1 = tk.Tk() if master is None else tk.Toplevel(master)
        self.Toplevel_1.configure(
            background="#2e2e2e",
            cursor="arrow",
            height=250,
            width=325)

        try:
            self.Toplevel_1.iconbitmap("bin/ABP-blanco-en-fondo-negro.ico")
        except:
            pass

        self.Toplevel_1.overrideredirect("False")
        self.Toplevel_1.resizable(False, False)
        self.Toplevel_1.title("Consulta Mis Comprobantes")
        
        Label_3 = ttk.Label(self.Toplevel_1)
        self.img_ABPblancoenfondonegro111 = tk.PhotoImage(
            file="bin/ABP blanco sin fondo.png")
        Label_3.configure(
            background="#2e2e2e",
            image=self.img_ABPblancoenfondonegro111)
        Label_3.pack(side="top")

        Label_1 = ttk.Label(self.Toplevel_1)
        Label_1.configure(
            background="#2e2e2e",
            cursor="arrow",
            foreground="#ffffff",
            justify="center",
            takefocus=False,
            text='Consulta masiva de Mis Comprobantes en base a un Excel\n',
            wraplength=325)
        Label_1.pack(expand=True, side="top")

        Label_2 = ttk.Label(self.Toplevel_1)
        Label_2.configure(
            background="#2e2e2e",
            foreground="#ffffff",
            justify="center",
            text='por Agustín Bustos Piasentini\nhttps://www.Agustin-Bustos-Piasentini.com.ar/')
        Label_2.pack(expand=True, side="top")

        self.Configurar = ttk.Button(self.Toplevel_1)
        self.Configurar.configure(text='Abrir archivo de configuración', command=self.open_env_file)
        self.Configurar.pack(expand=True, pady=4, side="top")

        self.Excel = ttk.Button(self.Toplevel_1)
        self.Excel.configure(text='CSV de Descarga', command=self.open_csv_file)
        self.Excel.pack(expand=True, padx=0, pady=4, side="top")

        self.Enviar = ttk.Button(self.Toplevel_1)
        self.Enviar.configure(text='Descargar desde Mis Comprobantes', command=self.confirmar)
        self.Enviar.pack(expand=True, pady=4, side="top")

        self.Colaboraciones = ttk.Button(self.Toplevel_1)
        self.Colaboraciones.configure(text='Donaciones', command=self.donaciones)
        self.Colaboraciones.pack(expand=True, pady=4, side="top")

        # Main widget
        self.mainwindow = self.Toplevel_1

    def open_env_file(self):
        self.open_file_in_popup(".env")

    def open_csv_file(self):
        self.open_file_in_popup("Descarga-Mis-Comprobantes.csv")

    def open_file_in_popup(self, file_path):
        if os.path.exists(file_path):
            popup = tk.Toplevel(self.mainwindow)
            popup.title(f"Editar {file_path}")
            text_widget = tk.Text(popup, wrap=tk.WORD)
            text_widget.pack(expand=True, fill="both")
            with open(file_path, "r") as file:
                text_widget.insert(tk.END, file.read())

            def save_file():
                with open(file_path, "w") as file:
                    file.write(text_widget.get("1.0", tk.END))
                messagebox.showinfo("Información", f"{file_path} guardado con éxito.")
                popup.destroy()

            save_button = ttk.Button(popup, text='Guardar', command=save_file)
            save_button.pack(side=tk.BOTTOM, pady=5)

        else:
            messagebox.showerror("Error", f"El archivo {file_path} no existe.")

    def confirmar(self):
        respuesta = messagebox.askyesno("Confirmar Descarga", "¿Está seguro que desea descargar los Archivos de Mis Comprobantes?")
        if respuesta:
            load_dotenv(override=True)
            consulta_mc_csv()

    def donaciones(self):
        webbrowser.open("https://cafecito.app/abustos")

    def run(self):
        self.mainwindow.mainloop()

if __name__ == "__main__":
    app = GuiDescargaMC()
    app.run()