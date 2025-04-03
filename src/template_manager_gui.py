import os
import json
import datetime
import mss
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# Configuración de rutas
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
TEMPLATES_MAPPING_FILE = os.path.join(PROJECT_DIR, "templates_mapping.json")

# Funciones para cargar y guardar el mapping de plantillas
def load_templates_mapping():
    if os.path.exists(TEMPLATES_MAPPING_FILE):
        with open(TEMPLATES_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_templates_mapping(mapping):
    with open(TEMPLATES_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4)

# Función de captura usando mss
def capture_screen(region=None, monitor=1):
    with mss.mss() as sct:
        if region is None:
            region = sct.monitors[monitor]
        sct_img = sct.grab(region)
        img = np.array(sct_img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img_bgr

# Clase de la aplicación GUI
class TemplateManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Plantillas - eFootball Automation")
        self.geometry("800x600")
        self.captured_image = None  # Guardará la imagen capturada (en formato BGR)

        # Variables de control
        self.capture_mode = tk.StringVar(value="full")  # "full" o "region"
        self.left_var = tk.StringVar(value="0")
        self.top_var = tk.StringVar(value="0")
        self.width_var = tk.StringVar(value="3840")  # Valores por defecto para un 4K
        self.height_var = tk.StringVar(value="2160")
        self.template_name_var = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        # Frame para seleccionar modo de captura
        mode_frame = ttk.LabelFrame(self, text="Modo de Captura")
        mode_frame.pack(padx=10, pady=10, fill="x")

        ttk.Radiobutton(mode_frame, text="Pantalla Completa", variable=self.capture_mode, value="full").pack(side="left", padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Captura de Región", variable=self.capture_mode, value="region").pack(side="left", padx=5, pady=5)

        # Frame para región de captura (visible solo si se selecciona "region")
        region_frame = ttk.LabelFrame(self, text="Parámetros de Región")
        region_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(region_frame, text="Left:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(region_frame, textvariable=self.left_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(region_frame, text="Top:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        ttk.Entry(region_frame, textvariable=self.top_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(region_frame, text="Width:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(region_frame, textvariable=self.width_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(region_frame, text="Height:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        ttk.Entry(region_frame, textvariable=self.height_var, width=10).grid(row=1, column=3, padx=5, pady=5)

        # Frame para la previsualización
        preview_frame = ttk.LabelFrame(self, text="Previsualización")
        preview_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(padx=10, pady=10)

        # Frame para el nombre de la plantilla y botones
        control_frame = ttk.Frame(self)
        control_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(control_frame, text="Nombre de la plantilla:").pack(side="left", padx=5)
        ttk.Entry(control_frame, textvariable=self.template_name_var, width=30).pack(side="left", padx=5)

        ttk.Button(control_frame, text="Capturar", command=self.update_preview).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Guardar", command=self.save_template).pack(side="left", padx=5)

    def update_preview(self):
        # Determina la región según el modo seleccionado
        if self.capture_mode.get() == "full":
            region = None
        else:
            try:
                region = {
                    "left": int(self.left_var.get()),
                    "top": int(self.top_var.get()),
                    "width": int(self.width_var.get()),
                    "height": int(self.height_var.get())
                }
            except ValueError:
                messagebox.showerror("Error", "Los parámetros de la región deben ser números enteros.")
                return

        # Captura la imagen
        self.captured_image = capture_screen(region=region, monitor=1)
        # Convierte la imagen para mostrarla en Tkinter (de BGR a RGB y luego a PIL)
        img_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        pil_img = pil_img.resize((400, 300))  # Redimensiona para la previsualización
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_label.config(image=self.tk_img)
        self.preview_label.image = self.tk_img

    def save_template(self):
        if self.captured_image is None:
            messagebox.showerror("Error", "No hay imagen capturada. Primero presiona 'Capturar'.")
            return

        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showerror("Error", "Debes introducir un nombre para la plantilla.")
            return

        # Genera un nombre de archivo único
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{template_name}_{timestamp}.png"
        file_path = os.path.join(IMAGES_DIR, file_name)

        # Guarda la imagen
        cv2.imwrite(file_path, self.captured_image)
        messagebox.showinfo("Éxito", f"Plantilla guardada en: {file_path}")

        # Actualiza el mapping de plantillas
        mapping = load_templates_mapping()
        if template_name in mapping:
            mapping[template_name].append(file_name)
        else:
            mapping[template_name] = [file_name]
        save_templates_mapping(mapping)
        print("Mapping actualizado:", mapping)

if __name__ == "__main__":
    # Asegúrate de que la carpeta 'images' exista
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

    app = TemplateManagerGUI()
    app.mainloop()
