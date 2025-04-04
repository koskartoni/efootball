import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import mss

# Rutas del proyecto (ajusta según tu estructura)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
OCR_MAPPING_FILE = os.path.join(PROJECT_DIR, "ocr_regions.json")

def load_ocr_mapping():
    """Carga el mapping de zonas OCR desde el archivo JSON."""
    if os.path.exists(OCR_MAPPING_FILE):
        with open(OCR_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_ocr_mapping(mapping):
    """Guarda el mapping de zonas OCR en el archivo JSON."""
    with open(OCR_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4)

def capture_screen(region=None, monitor=1):
    """
    Captura la pantalla (o una región específica) usando mss.

    Args:
        region (dict o None): Diccionario con 'left', 'top', 'width' y 'height'. Si es None, se captura el monitor completo.
        monitor (int): Número del monitor a capturar (1-indexado).

    Returns:
        Imagen capturada (numpy array en formato BGR).
    """
    with mss.mss() as sct:
        if region is None:
            region = sct.monitors[monitor]
        sct_img = sct.grab(region)
        img = np.array(sct_img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img_bgr

def tk_select_ocr_region(root, image, max_width=800):
    """
    Permite al usuario seleccionar una región en la imagen usando una ventana Toplevel con un Canvas.
    La imagen se redimensiona para que la ventana sea manejable y luego se convierten las
    coordenadas seleccionadas a la escala original. Se incluye un botón "Confirmar Selección"
    para finalizar la selección.

    Args:
        root: Ventana principal de Tkinter.
        image (np.array): Imagen original en formato BGR.
        max_width (int): Ancho máximo para la visualización interactiva.

    Returns:
        Diccionario con las coordenadas originales: {"left": int, "top": int, "width": int, "height": int}
        o None si se cancela.
    """
    orig_height, orig_width = image.shape[:2]
    scale = 1.0
    if orig_width > max_width:
        scale = max_width / orig_width
        resized_img = cv2.resize(image, (int(orig_width * scale), int(orig_height * scale)))
    else:
        resized_img = image.copy()

    # Convertir a imagen PIL y a imagen Tkinter
    img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    tk_img = ImageTk.PhotoImage(pil_img)

    # Crear ventana Toplevel para la selección
    sel_win = tk.Toplevel(root)
    sel_win.title("Seleccione Región OCR")
    sel_win.grab_set()  # Bloquea la ventana principal hasta confirmar

    canvas = tk.Canvas(sel_win, width=tk_img.width(), height=tk_img.height(), cursor="cross")
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    # Variables para almacenar la selección
    selection = {"x1": None, "y1": None, "x2": None, "y2": None}
    rect = None

    def on_button_press(event):
        selection["x1"] = event.x
        selection["y1"] = event.y
        nonlocal rect
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="green", width=2)

    def on_move_press(event):
        nonlocal rect
        canvas.coords(rect, selection["x1"], selection["y1"], event.x, event.y)

    def on_button_release(event):
        selection["x2"] = event.x
        selection["y2"] = event.y

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)

    # Botón de Confirmar para cerrar la ventana
    def confirm_selection():
        sel_win.destroy()

    confirm_btn = ttk.Button(sel_win, text="Confirmar Selección", command=confirm_selection)
    confirm_btn.pack(pady=5)

    root.wait_window(sel_win)

    # Verificar que se hayan seleccionado ambas esquinas
    if None not in (selection["x1"], selection["y1"], selection["x2"], selection["y2"]):
        x1, y1 = selection["x1"], selection["y1"]
        x2, y2 = selection["x2"], selection["y2"]
        left_resized = int(min(x1, x2))
        top_resized = int(min(y1, y2))
        width_resized = int(abs(x2 - x1))
        height_resized = int(abs(y2 - y1))
        # Convertir a coordenadas originales
        left_orig = int(left_resized / scale)
        top_orig = int(top_resized / scale)
        width_orig = int(width_resized / scale)
        height_orig = int(height_resized / scale)
        return {"left": left_orig, "top": top_orig, "width": width_orig, "height": height_orig}
    else:
        return None

class TemplateManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Zonas OCR - eFootball Automation")
        self.geometry("800x700")
        self.resizable(False, False)
        self.captured_image = None         # Imagen en formato BGR
        self.selected_image_path = None      # Ruta de imagen seleccionada desde el directorio
        self.ocr_regions = []              # Lista de regiones OCR seleccionadas

        self.create_widgets()

    def create_widgets(self):
        # Frame para seleccionar el origen de la imagen
        source_frame = ttk.LabelFrame(self, text="Origen de la Imagen")
        source_frame.pack(padx=10, pady=10, fill="x")

        self.source_var = tk.StringVar(value="capture")
        ttk.Radiobutton(source_frame, text="Capturar desde pantalla", variable=self.source_var, value="capture").pack(side="left", padx=5, pady=5)
        ttk.Radiobutton(source_frame, text="Seleccionar imagen existente", variable=self.source_var, value="file").pack(side="left", padx=5, pady=5)

        ttk.Button(source_frame, text="Cargar Imagen", command=self.load_image).pack(side="left", padx=5, pady=5)

        # Frame de previsualización
        preview_frame = ttk.LabelFrame(self, text="Previsualización de la Imagen")
        preview_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(padx=10, pady=10)

        # Botón para seleccionar la región OCR
        ttk.Button(self, text="Marcar Región OCR", command=self.mark_ocr_region).pack(pady=5)

        # Botón para limpiar zonas OCR marcadas
        ttk.Button(self, text="Limpiar Zonas OCR", command=self.clear_ocr_regions).pack(pady=5)

        # Label para mostrar las zonas OCR marcadas
        self.region_label = ttk.Label(self, text="Zonas OCR: Ninguna definida")
        self.region_label.pack(pady=5)

        # Frame para asignar nombre a la plantilla OCR
        name_frame = ttk.LabelFrame(self, text="Configuración de Zona OCR")
        name_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(name_frame, text="Nombre de la plantilla:").pack(side="left", padx=5, pady=5)
        self.template_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.template_name_var, width=30).pack(side="left", padx=5, pady=5)

        ttk.Button(name_frame, text="Guardar Zonas OCR", command=self.save_ocr_regions).pack(side="left", padx=5, pady=5)

    def load_image(self):
        source = self.source_var.get()
        if source == "capture":
            self.captured_image = capture_screen(monitor=1)
            self.selected_image_path = None
        elif source == "file":
            file_path = filedialog.askopenfilename(initialdir=IMAGES_DIR, title="Seleccionar Imagen",
                                                   filetypes=(("Archivos PNG", "*.png"), ("Todos los archivos", "*.*")))
            if file_path:
                self.selected_image_path = file_path
                self.captured_image = cv2.imread(file_path)
        else:
            messagebox.showerror("Error", "Debes seleccionar un origen de imagen.")
            return

        if self.captured_image is None:
            messagebox.showerror("Error", "No se pudo cargar la imagen.")
            return

        self.clear_ocr_regions()  # Reinicia las zonas al cargar una nueva imagen
        self.show_preview()

    def show_preview(self):
        img_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        pil_img.thumbnail((400, 300))
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_label.config(image=self.tk_img)
        self.preview_label.image = self.tk_img

    def mark_ocr_region(self):
        if self.captured_image is None:
            messagebox.showerror("Error", "Primero carga una imagen.")
            return
        region = tk_select_ocr_region(self, self.captured_image, max_width=800)
        if region:
            self.ocr_regions.append(region)
            self.update_region_label()
        else:
            messagebox.showinfo("Información", "No se seleccionó ninguna región.")

    def update_region_label(self):
        if self.ocr_regions:
            self.region_label.config(text=f"Zonas OCR: {self.ocr_regions}")
        else:
            self.region_label.config(text="Zonas OCR: Ninguna definida")

    def clear_ocr_regions(self):
        self.ocr_regions = []
        self.update_region_label()

    def save_ocr_regions(self):
        if not self.ocr_regions:
            messagebox.showerror("Error", "No se han definido zonas OCR.")
            return
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showerror("Error", "Debes introducir un nombre para la plantilla.")
            return

        mapping = load_ocr_mapping()
        # Si ya existe, se añaden las nuevas zonas; de lo contrario, se asigna la lista
        if template_name in mapping:
            if isinstance(mapping[template_name], list):
                mapping[template_name].extend(self.ocr_regions)
            else:
                mapping[template_name] = [mapping[template_name]] + self.ocr_regions
        else:
            mapping[template_name] = self.ocr_regions

        save_ocr_mapping(mapping)
        messagebox.showinfo("Éxito", f"Zonas OCR guardadas para '{template_name}'.")
        print("Mapping OCR actualizado:", mapping)
        self.clear_ocr_regions()

if __name__ == "__main__":
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    app = TemplateManagerGUI()
    app.mainloop()
