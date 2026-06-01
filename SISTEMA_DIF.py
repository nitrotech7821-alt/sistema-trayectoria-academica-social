import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from reportlab.pdfgen import canvas
from tkcalendar import DateEntry  # IMPORTANTE: pip install tkcalendar

class SistemaDIFOficial:
    def __init__(self, root):
        self.root = root
        self.root.title("DIF HERMOSILLO - SESIÓN: ADMIN")
        self.root.geometry("1200x850")
        
        # --- CONFIGURACIÓN DE FIREBASE ---
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("dif-hermosillo-firebase-adminsdk-fbsvc-b793685b2c.json")
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar con Firebase: {e}")

        # --- ENCABEZADO ---
        header = tk.Frame(root, bg="#1a252f", height=60)
        header.pack(fill="x")
        tk.Label(header, text="SISTEMA DIF | GESTIÓN SOCIAL COMPLETA", 
                 font=("Arial", 18, "bold"), fg="white", bg="#1a252f").pack(pady=15, padx=20, side="left")

        # --- CONTENEDOR PRINCIPAL DE DATOS ---
        f_datos = tk.LabelFrame(root, text="DATOS DEL BENEFICIARIO", font=("Arial", 10, "bold"))
        f_datos.pack(fill="x", padx=20, pady=10)

        # Fila 1: Nombres y Sexo
        tk.Label(f_datos, text="Nombre(s):").grid(row=0, column=0, sticky="w", padx=5)
        self.en_nom = tk.Entry(f_datos, width=25); self.en_nom.grid(row=1, column=0, padx=5, pady=5)
        self.en_nom.bind("<FocusOut>", lambda e: self.generar_curp_auto())
        
        tk.Label(f_datos, text="Ap. Paterno:").grid(row=0, column=1, sticky="w", padx=5)
        self.en_pat = tk.Entry(f_datos, width=25); self.en_pat.grid(row=1, column=1, padx=5, pady=5)
        self.en_pat.bind("<FocusOut>", lambda e: self.generar_curp_auto())
        
        tk.Label(f_datos, text="Ap. Materno:").grid(row=0, column=2, sticky="w", padx=5)
        self.en_mat = tk.Entry(f_datos, width=25); self.en_mat.grid(row=1, column=2, padx=5, pady=5)
        self.en_mat.bind("<FocusOut>", lambda e: self.generar_curp_auto())

        tk.Label(f_datos, text="Sexo:").grid(row=0, column=3, sticky="w", padx=5)
        self.cb_sexo = ttk.Combobox(f_datos, values=["MASCULINO", "FEMENINO"], width=15)
        self.cb_sexo.grid(row=1, column=3, padx=5, pady=5)

        # Fila 2: CALENDARIOS y CURP
        tk.Label(f_datos, text="Fecha Nacimiento:").grid(row=2, column=0, sticky="w", padx=5)
        # Este es el componente que muestra el calendario
        self.en_nac = DateEntry(f_datos, width=23, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.en_nac.grid(row=3, column=0, padx=5, pady=5)
        self.en_nac.bind("<<DateEntrySelected>>", lambda e: self.generar_curp_auto())

        tk.Label(f_datos, text="CURP (Auto):").grid(row=2, column=1, sticky="w", padx=5)
        self.en_curp = tk.Entry(f_datos, width=25, font=("Arial", 9, "bold"), fg="darkred")
        self.en_curp.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(f_datos, text="Colonia:").grid(row=2, column=2, sticky="w", padx=5)
        self.en_col = tk.Entry(f_datos, width=25); self.en_col.grid(row=3, column=2, padx=5, pady=5)

        tk.Label(f_datos, text="Atención:").grid(row=2, column=3, sticky="w", padx=5)
        self.cb_atn = ttk.Combobox(f_datos, values=["OFICINA", "DOMICILIO", "EVENTO"], width=15)
        self.cb_atn.grid(row=3, column=3, padx=5, pady=5); self.cb_atn.set("OFICINA")

        # Fila 3: Fecha entrega con Calendario
        tk.Label(f_datos, text="Fecha de Entrega:", fg="blue", font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="w", padx=5)
        self.en_fec = DateEntry(f_datos, width=23, background='blue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.en_fec.grid(row=5, column=0, padx=5, pady=5)

        # --- SECCIÓN DE APOYOS ---
        f_apoyos = tk.LabelFrame(root, text="APOYOS ENTREGADOS", font=("Arial", 10, "bold"))
        f_apoyos.pack(fill="x", padx=20, pady=5)
        self.vars = {}
        for op in ["Despensa", "Leche", "Pañales", "Cobijas", "Especies"]:
            v = tk.BooleanVar(); tk.Checkbutton(f_apoyos, text=op, variable=v).pack(side="left", padx=15)
            self.vars[op] = v

        # --- BOTONERA ---
        f_btns = tk.Frame(root)
        f_btns.pack(fill="x", padx=20, pady=10)
        
        tk.Button(f_btns, text="💾 GUARDAR", bg="#27ae60", fg="white", font=("Arial", 9, "bold"), padx=10, command=self.guardar_datos).pack(side="left", padx=2)
        tk.Button(f_btns, text="🔄 SINCRONIZAR", bg="#2980b9", fg="white", font=("Arial", 9, "bold"), padx=10, command=self.guardar_datos).pack(side="left", padx=2)
        tk.Button(f_btns, text="📊 REP. SEMANAL", bg="#f39c12", fg="white", font=("Arial", 9, "bold"), padx=10).pack(side="left", padx=2)
        tk.Button(f_btns, text="☁️ DESCARGAR NUBE", bg="#34495e", fg="white", font=("Arial", 9, "bold"), padx=10, command=self.descargar_todo_firebase).pack(side="left", padx=2)
        tk.Button(f_btns, text="🗑️ ELIMINAR", bg="#e74c3c", fg="white", font=("Arial", 9, "bold"), padx=10, command=self.eliminar_registro).pack(side="left", padx=2)
        tk.Button(f_btns, text="📄 PDF INDIVIDUAL", bg="#8e44ad", fg="white", font=("Arial", 9, "bold"), padx=10, command=self.generar_pdf).pack(side="left", padx=2)
        tk.Button(f_btns, text="🧹 LIMPIAR", bg="#7f8c8d", fg="white", font=("Arial", 9, "bold"), padx=10, command=self.limpiar).pack(side="left", padx=2)

        # --- TABLA DE REGISTROS ---
        self.tabla = ttk.Treeview(root, columns=("Fecha", "Nombre", "CURP", "Colonia", "Atención", "Apoyos"), show="headings")
        for c in ("Fecha", "Nombre", "CURP", "Colonia", "Atención", "Apoyos"): self.tabla.heading(c, text=c)
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)

    def generar_curp_auto(self):
        """Genera automáticamente los primeros 10 caracteres de la CURP"""
        try:
            nom = self.en_nom.get().strip().upper()
            pat = self.en_pat.get().strip().upper()
            mat = self.en_mat.get().strip().upper()
            fecha = self.en_nac.get_date() 

            if len(nom) > 0 and len(pat) > 0:
                # Lógica simplificada: P1 + VocalP + M1 + N1
                vocal_p = next((c for c in pat[1:] if c in "AEIOU"), "X")
                curp_base = (pat[0] + vocal_p + (mat[0] if mat else "X") + nom[0])
                # Año, Mes, Día
                f_str = fecha.strftime("%y%m%d")
                self.en_curp.delete(0, tk.END)
                self.en_curp.insert(0, curp_base.upper() + f_str)
        except:
            pass

    def guardar_datos(self):
        curp = self.en_curp.get().upper()
        if not self.en_nom.get() or not curp:
            messagebox.showerror("Error", "Nombre y CURP son obligatorios."); return

        nombre_completo = f"{self.en_nom.get()} {self.en_pat.get()} {self.en_mat.get()}".upper()
        apoyos_txt = ", ".join([k for k, v in self.vars.items() if v.get()])
        fec = self.en_fec.get()

        self.tabla.insert("", 0, values=(fec, nombre_completo, curp, self.en_col.get().upper(), self.cb_atn.get(), apoyos_txt))

        try:
            self.db.collection("asistencia_2026").document(curp).set({
                "NOMBRE (S)": self.en_nom.get().upper(),
                "APELLIDO 1": self.en_pat.get().upper(),
                "APELLIDO 2": self.en_mat.get().upper(),
                "CURP": curp,
                "FECHA NAC": self.en_nac.get(),
                "COLONIA": self.en_col.get().upper(),
                "SEXO": self.cb_sexo.get(),
                "APOYO": apoyos_txt,
                "REALIZO": "SISTEMA_DIF_HMO",
                "FECHA_CAP": fec
            })
            messagebox.showinfo("Éxito", "Sincronizado con la nube.")
            self.limpiar()
        except Exception as e:
            messagebox.showerror("Error Firebase", f"Error: {e}")

    def generar_pdf(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un registro."); return
        item = self.tabla.item(seleccion); v = item['values']
        nombre_pdf = f"Comprobante_{v[2]}.pdf"
        c = canvas.Canvas(nombre_pdf)
        c.drawString(100, 750, f"DIF HERMOSILLO - BENEFICIARIO: {v[1]}")
        c.drawString(100, 730, f"CURP: {v[2]} | Apoyo: {v[5]}")
        c.save()
        messagebox.showinfo("PDF", f"PDF Generado: {nombre_pdf}")

    def eliminar_registro(self):
        for item in self.tabla.selection(): self.tabla.delete(item)

    def descargar_todo_firebase(self):
        try:
            docs = self.db.collection("asistencia_2026").stream()
            datos = [doc.to_dict() for doc in docs]
            df = pd.DataFrame(datos)
            archivo = f"RESPALDO_DIF_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            df.to_excel(archivo, index=False)
            messagebox.showinfo("Excel", f"Guardado como: {archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo: {e}")

    def limpiar(self):
        for e in [self.en_nom, self.en_pat, self.en_mat, self.en_curp, self.en_col]: 
            e.delete(0, tk.END)
        for v in self.vars.values(): v.set(False)

if __name__ == "__main__":
    root = tk.Tk(); app = SistemaDIFOficial(root); root.mainloop()