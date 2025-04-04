import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import mss
from tkinter import font  # Import font module


# --- Constantes del proyecto ---
# Corrección de PROJECT_DIR: Subir solo dos niveles desde la ubicación de este script ('scr')
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
OCR_MAPPING_FILE_PATH = os.path.join(PROJECT_DIR, "config", "ocr_regions.json")
TEMPLATE_MAPPING_FILE_PATH = os.path.join(PROJECT_DIR, "config", "templates_mapping.json")
MAX_PREVIEW_WIDTH = 800
PREVIEW_THUMBNAIL_SIZE = (600, 500)
DEFAULT_FONT_SIZE = 16 # Ajusta este tamaño según tu preferencia


def load_ocr_mapping():
    """Carga el mapping de zonas OCR desde el archivo JSON."""
    try:
        with open(OCR_MAPPING_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Archivo {OCR_MAPPING_FILE_PATH} no encontrado. Creando uno nuevo.")
        return {}
    except json.JSONDecodeError:
        messagebox.showerror("Error", f"Error al leer el archivo JSON {OCR_MAPPING_FILE_PATH}. Puede estar corrupto.")
        return {}
    except Exception as e:  # Captura otras excepciones inesperadas
        messagebox.showerror("Error", f"Error inesperado al cargar el mapping OCR: {e}")
        return {}

# --- Helper function to load template mapping dictionary ---
def load_template_mapping_dict():
    """Carga el mapping de plantillas desde el archivo JSON."""
    try:
        with open(TEMPLATE_MAPPING_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Archivo {TEMPLATE_MAPPING_FILE_PATH} no encontrado. Creando uno nuevo.")
        return {}
    except json.JSONDecodeError:
        messagebox.showerror("Error", f"Error al leer el archivo JSON {TEMPLATE_MAPPING_FILE_PATH}.")
        return {}
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado al cargar el mapping de plantillas: {e}")
        return {}


def save_ocr_mapping(mapping):
    """Guarda el mapping de zonas OCR en el archivo JSON."""
    try:
        with open(OCR_MAPPING_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar el mapping OCR: {e}")


def capture_screen(region=None, monitor=1):
    """Captura la pantalla (o una región específica) usando mss."""
    try:
        with mss.mss() as sct:
            if region is None:
                # Asegurarse de que el índice del monitor sea válido
                if monitor < 1 or monitor >= len(sct.monitors):
                     messagebox.showerror("Error", f"Monitor {monitor} no válido. Monitores disponibles: 1 a {len(sct.monitors)-1}")
                     return None
                region = sct.monitors[monitor]
            sct_img = sct.grab(region)
            img = np.array(sct_img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr
    except Exception as e:
        messagebox.showerror("Error", f"Error al capturar la pantalla: {e}")
        return None


def tk_select_ocr_region(root, image, max_width=MAX_PREVIEW_WIDTH):
    """Permite al usuario seleccionar una región en la imagen usando una ventana Toplevel con un Canvas."""
    orig_height, orig_width = image.shape[:2]
    scale = 1.0
    if orig_width > max_width:
        # --- CORRECCIÓN: Usar MAX_PREVIEW_WIDTH ---
        scale = MAX_PREVIEW_WIDTH / orig_width
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
    sel_win.grab_set()

    canvas = tk.Canvas(sel_win, width=tk_img.width(), height=tk_img.height(), cursor="cross")
    canvas.pack(padx=5, pady=5, fill="both", expand=True) # Allow canvas to expand
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    # Variables para almacenar la selección y coordenadas mostradas
    selection = {"x1": None, "y1": None, "x2": None, "y2": None}
    rect = None
    coord_label_var = tk.StringVar(value="Coordenadas: ")
    coord_label = ttk.Label(sel_win, textvariable=coord_label_var)
    coord_label.pack()

    def update_coord_label(x, y):
        coord_label_var.set(f"Coordenadas (Resize): x={x}, y={y}")

    def on_button_press(event):
        selection["x1"] = event.x
        selection["y1"] = event.y
        nonlocal rect
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="green", width=2)
        update_coord_label(event.x, event.y)

    def on_move_press(event):
        nonlocal rect
        canvas.coords(rect, selection["x1"], selection["y1"], event.x, event.y)
        update_coord_label(event.x, event.y)

    def on_button_release(event):
        selection["x2"] = event.x
        selection["y2"] = event.y
        update_coord_label(event.x, event.y)

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)
    canvas.bind("<Motion>", lambda event: update_coord_label(event.x, event.y))

    # Frame para botones Confirmar y Cancelar
    button_frame = ttk.Frame(sel_win)
    button_frame.pack(pady=5)

    def confirm_selection():
        sel_win.destroy()

    def cancel_selection():
        selection["x1"] = None  # Indica cancelación
        sel_win.destroy()

    confirm_btn = ttk.Button(button_frame, text="Confirmar Selección", command=confirm_selection)
    confirm_btn.pack(side="left", padx=5)
    cancel_btn = ttk.Button(button_frame, text="Cancelar Selección", command=cancel_selection)
    cancel_btn.pack(side="left", padx=5)

    root.wait_window(sel_win)

    # Verificar que se hayan seleccionado ambas esquinas y no se haya cancelado
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


def tk_select_monitor_region(root, monitor_img):
    """
    Permite al usuario seleccionar una región del monitor usando una ventana Toplevel con un Canvas.
    Similar a tk_select_ocr_region pero para seleccionar una región del monitor completo.
    """
    orig_height, orig_width = monitor_img.shape[:2]
    scale = 1.0
    # --- CORRECCIÓN: Usar MAX_PREVIEW_WIDTH (o ajustar si se quiere otro límite) ---
    if orig_width > MAX_PREVIEW_WIDTH:
        scale = MAX_PREVIEW_WIDTH / orig_width
        resized_img = cv2.resize(monitor_img, (int(orig_width * scale), int(orig_height * scale)))
    else:
        resized_img = monitor_img.copy()

    # Convertir a imagen PIL y a imagen Tkinter
    img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    tk_img = ImageTk.PhotoImage(pil_img)

    # Crear ventana Toplevel para la selección
    sel_win = tk.Toplevel(root)
    sel_win.title("Seleccione Región del Monitor")
    sel_win.grab_set()

    canvas = tk.Canvas(sel_win, width=tk_img.width(), height=tk_img.height(), cursor="cross")
    canvas.pack(padx=5, pady=5, fill="both", expand=True) # Allow canvas to expand
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    # Variables para almacenar la selección
    selection = {"x1": None, "y1": None, "x2": None, "y2": None}
    rect = None

    def on_button_press(event):
        selection["x1"] = event.x
        selection["y1"] = event.y
        nonlocal rect
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="blue", width=2) # Color azul para región monitor

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

    cancel_btn = ttk.Button(sel_win, text="Confirmar Región", command=confirm_selection)
    cancel_btn.pack(pady=5)

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
        # Necesitamos obtener las coordenadas originales del monitor completo
        monitor_info = root.monitors_info[root.monitor_var.get()] # Obtener info del monitor seleccionado en la GUI principal
        left_orig = monitor_info['left'] + int(left_resized / scale)
        top_orig = monitor_info['top'] + int(top_resized / scale)
        width_orig = int(width_resized / scale)
        height_orig = int(height_resized / scale)
        return {"left": left_orig, "top": top_orig, "width": width_orig, "height": height_orig}
    return None # Retornar None si no se seleccionó región


class TemplateManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Zonas OCR - eFootball Automation")
        # self.geometry("950x800") # Removed fixed geometry to allow resizing
        # self.resizable(False, False) # Removed to allow resizing
        self.captured_image = None
        self.selected_image_path = None
        self.ocr_regions = []
        self.ocr_region_rects = []
        self.current_template_name = None
        self.template_names_mapping = {}
        self.ocr_regions_mapping = {}
        self.monitors_info = self.detect_monitors()

        # --- Establecer fuente por defecto para la GUI ---
        self.default_font = font.Font(family="Helvetica", size=DEFAULT_FONT_SIZE) # Guardar fuente para usarla explícitamente
        self.option_add("*Font", self.default_font) # Intento general
        style = ttk.Style(self)
        style.configure('.', font=self.default_font) # Configurar estilo ttk
        style.configure('TLabelframe.Label', font=self.default_font) # Estilo para etiquetas de LabelFrame

        self.create_widgets()
        self.load_template_names_from_json() # Cargar nombres PRIMERO
        self.load_last_image_source() # LUEGO cargar último origen
        self.load_ocr_regions_from_json() # Cargar regiones OCR


    def detect_monitors(self):
        """Detecta los monitores existentes usando mss."""
        with mss.mss() as sct:
            return sct.monitors


    def load_template_data(self):
        """Carga nombres de plantillas y regiones OCR al inicio."""
        self.load_template_names_from_json()
        self.load_ocr_regions_from_json()


    def load_ocr_regions_from_json(self):
        """Carga las regiones OCR desde ocr_regions.json."""
        self.ocr_regions_mapping = load_ocr_mapping()


    def create_widgets(self):
        self.create_capture_frame()
        self.create_template_selection_frame()
        self.create_preview_frame()
        self.create_ocr_config_frame()
        self.create_status_label()


    def create_capture_frame(self):
        """Crea el frame para capturar nuevas plantillas."""
        capture_frame = ttk.LabelFrame(self, text="Capturar Nueva Plantilla", labelwidget=ttk.Label(self, text="Capturar Nueva Plantilla", font=self.default_font))
        capture_frame.pack(padx=10, pady=10, fill="x")

        # Tipo de captura
        self.capture_type_var = tk.StringVar(value="monitor")
        capture_type_frame = ttk.Frame(capture_frame)
        capture_type_frame.pack(fill="x", padx=5, pady=2)
        ttk.Radiobutton(capture_type_frame, text="Monitor Completo", variable=self.capture_type_var, value="monitor").pack(side="left", padx=5)
        ttk.Radiobutton(capture_type_frame, text="Región del Monitor", variable=self.capture_type_var, value="region").pack(side="left", padx=5)

        # Selección de monitor
        self.monitor_var = tk.IntVar(value=1)
        monitor_frame = ttk.Frame(capture_frame)
        monitor_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(monitor_frame, text="Monitor:", font=self.default_font).pack(side="left", padx=5)
        self.monitor_spinbox = ttk.Spinbox(monitor_frame, from_=1, to=len(self.monitors_info) if self.monitors_info else 1, textvariable=self.monitor_var, width=5, font=self.default_font)
        self.monitor_spinbox.pack(side="left", padx=5)

        ttk.Button(capture_frame, text="Capturar Pantalla", command=self.capture_new_template).pack(pady=5)

        # Nombre para la nueva plantilla
        self.new_template_name_var = tk.StringVar()
        name_frame = ttk.Frame(capture_frame)
        name_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(name_frame, text="Nombre Nueva Plantilla:", font=self.default_font).pack(side="left", padx=5)
        ttk.Entry(name_frame, textvariable=self.new_template_name_var, width=30, font=self.default_font).pack(side="left", padx=5)

        ttk.Button(capture_frame, text="Guardar Nueva Plantilla", command=self.save_new_template).pack(pady=5)


    def create_template_selection_frame(self):
        """Crea el frame para seleccionar plantillas existentes."""
        template_frame = ttk.LabelFrame(self, text="Seleccionar Plantilla Existente", labelwidget=ttk.Label(self, text="Seleccionar Plantilla Existente", font=self.default_font))
        template_frame.pack(padx=10, pady=10, fill="x")

        combo_frame = ttk.Frame(template_frame)
        combo_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(combo_frame, text="Plantilla Existente:", font=self.default_font).pack(side="left", padx=5, pady=5)
        self.template_name_var = tk.StringVar()
        self.template_name_combobox = ttk.Combobox(combo_frame, textvariable=self.template_name_var, width=30, font=self.default_font)
        self.template_name_combobox.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.template_name_combobox.bind("<<ComboboxSelected>>", self.on_template_name_selected)

        ttk.Button(combo_frame, text="Refrescar Lista", command=self.load_template_names_from_json).pack(side="left", padx=5, pady=5)


    def create_preview_frame(self):
        """Crea el frame de previsualización de la imagen."""
        preview_frame = ttk.LabelFrame(self, text="Previsualización de la Imagen", labelwidget=ttk.Label(self, text="Previsualización de la Imagen", font=self.default_font))
        preview_frame.pack(padx=10, pady=10, fill="both", expand=True, side="left")

        self.preview_label = tk.Canvas(preview_frame, width=PREVIEW_THUMBNAIL_SIZE[0], height=PREVIEW_THUMBNAIL_SIZE[1])
        self.preview_label.pack(padx=10, pady=10, fill="both", expand=True)


    def create_ocr_config_frame(self):
        """Crea el frame para la configuración de zonas OCR."""
        config_frame = ttk.LabelFrame(self, text="Configuración de Zona OCR", labelwidget=ttk.Label(self, text="Configuración de Zona OCR", font=self.default_font))
        config_frame.pack(padx=10, pady=10, fill="both", expand=True, side="right")

        ttk.Button(config_frame, text="Marcar Región OCR", command=self.mark_ocr_region).pack(pady=5)
        ttk.Button(config_frame, text="Limpiar Zonas OCR", command=self.clear_ocr_regions).pack(pady=5)

        self.region_label = ttk.Label(config_frame, text="Zonas OCR: Ninguna definida", font=self.default_font)
        self.region_label.pack(pady=5)

        ttk.Button(config_frame, text="Guardar Zonas OCR", command=self.save_ocr_regions).pack(side="left", padx=5, pady=5)


    def create_status_label(self):
        """Crea el label para mensajes de estado."""
        self.status_label_var = tk.StringVar(value="Listo")
        status_label = ttk.Label(self, textvariable=self.status_label_var, anchor="w", font=self.default_font)
        status_label.pack(side="bottom", fill="x", padx=10, pady=5)


    def load_template_names_from_json(self):
        """Carga nombres de plantillas desde templates_mapping.json y actualiza el Combobox."""
        try:
            with open(TEMPLATE_MAPPING_FILE_PATH, "r", encoding="utf-8") as f:
                self.template_names_mapping = json.load(f)
                template_names = list(self.template_names_mapping.keys())
                self.template_name_combobox['values'] = template_names
                self.status_message("Lista de plantillas refrescada.")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Archivo {TEMPLATE_MAPPING_FILE_PATH} no encontrado en: {TEMPLATE_MAPPING_FILE_PATH}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Error al leer el archivo JSON {TEMPLATE_MAPPING_FILE_PATH}.")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado al cargar nombres de plantillas: {e}")


    def on_template_name_selected(self, event):
        """Se llama al seleccionar un nombre de plantilla del Combobox."""
        selected_name = self.template_name_var.get()
        if selected_name:
            # Cargar imagen automáticamente
            image_files = self.template_names_mapping.get(selected_name, [])
            if image_files:
                first_image_file = image_files[0]
                image_path = os.path.join(IMAGES_DIR, first_image_file)
                if os.path.exists(image_path):
                    try:
                        self.selected_image_path = image_path
                        self.captured_image = cv2.imread(image_path)
                        if self.captured_image is None:
                            raise Exception("No se pudo leer la imagen con OpenCV.")
                        self.show_preview()
                        self.status_message(f"Plantilla '{selected_name}' cargada.")
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al cargar imagen para '{selected_name}': {e}")
                        self.status_message("Error al cargar imagen.")
                        return

            # Cargar regiones OCR si existen
            if selected_name in self.ocr_regions_mapping:
                self.ocr_regions = self.ocr_regions_mapping[selected_name]
                self.update_region_label()
                self.show_preview()
                self.status_message(f"Regiones OCR cargadas para '{selected_name}'.")
            else:
                self.ocr_regions = []
                self.update_region_label()
                self.show_preview()
                self.status_message(f"Plantilla '{selected_name}' seleccionada. No hay regiones OCR guardadas.")


    def capture_new_template(self):
        """Captura una nueva plantilla desde la pantalla, según el tipo seleccionado."""
        self.status_message("Capturando pantalla...")
        capture_type = self.capture_type_var.get()
        monitor = self.monitor_var.get()

        if capture_type == "monitor":
            self.captured_image = capture_screen(monitor=monitor)
        elif capture_type == "region":
            monitor_image = capture_screen(monitor=monitor)
            if monitor_image is not None:
                region = tk_select_monitor_region(self, monitor_image) # Pasar self (root)
                if region:
                    self.captured_image = capture_screen(region=region, monitor=monitor)
                else:
                    self.captured_image = None
            else:
                self.captured_image = None

        if self.captured_image is not None:
            self.selected_image_path = None
            self.show_preview()
            self.status_message("Pantalla capturada. Previsualizando...")
        else:
            self.status_message("Captura cancelada o fallida.")


    def save_new_template(self):
        """Guarda la nueva plantilla capturada."""
        if self.captured_image is None:
            messagebox.showerror("Error", "No hay imagen capturada para guardar.")
            return
        template_name = self.new_template_name_var.get().strip()
        if not template_name:
            messagebox.showerror("Error", "Debes introducir un nombre para la nueva plantilla.")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"{template_name}_{timestamp}.png"
        image_path = os.path.join(IMAGES_DIR, image_filename)

        try:
            cv2.imwrite(image_path, self.captured_image)
            messagebox.showinfo("Éxito", f"Plantilla guardada como '{image_filename}'.")
            self.status_message(f"Plantilla guardada como '{image_filename}'.")

            # --- CORRECCIÓN: Cargar usando la función helper ---
            mapping = load_template_mapping_dict() # Cargar diccionario directamente
            if template_name in mapping:
                mapping[template_name].append(image_filename)
            else:
                mapping[template_name] = [image_filename]

            # Guardar templates_mapping.json actualizado
            try:
                with open(TEMPLATE_MAPPING_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(mapping, f, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar {TEMPLATE_MAPPING_FILE_PATH}: {e}")
                return

            self.load_template_names_from_json()
            self.template_name_var.set(template_name)
            self.on_template_name_selected(None)
            self.new_template_name_var.set("")


        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la plantilla: {e}")
            self.status_message("Error al guardar plantilla.")


    def load_image(self):
        """Carga la imagen desde archivo (mantiene funcionalidad original)."""
        self.status_message("Cargando imagen desde archivo...")
        file_path = filedialog.askopenfilename(initialdir=IMAGES_DIR, title="Seleccionar Imagen",
                                               filetypes=(("Archivos PNG", "*.png"), ("Todos los archivos", "*.*")))
        if file_path:
            try:
                self.selected_image_path = file_path
                self.captured_image = cv2.imread(file_path)
                if self.captured_image is None:
                    raise Exception("No se pudo leer la imagen con OpenCV.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar la imagen desde archivo: {e}")
                self.status_message("Error al cargar imagen desde archivo.")
                return

            self.clear_ocr_regions()
            self.show_preview()
            self.status_message("Imagen cargada desde archivo.")
            self.display_image_path()
        else:
            self.status_message("Carga de imagen desde archivo cancelada.")


    def display_image_path(self):
        """Muestra la ruta del archivo de imagen en el label de estado."""
        if self.selected_image_path:
            self.status_message(f"Imagen cargada desde: {self.selected_image_path}")
        elif self.source_var.get() == "capture":
            self.status_message("Imagen capturada desde pantalla.")


    def show_preview(self):
        """Muestra la imagen en el canvas de previsualización y dibuja regiones OCR."""
        if self.captured_image is None:
            self.preview_label.delete("all") # Limpiar si no hay imagen
            return

        img_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        pil_img.thumbnail(PREVIEW_THUMBNAIL_SIZE)
        self.tk_img = ImageTk.PhotoImage(pil_img)

        self.preview_label.config(width=self.tk_img.width(), height=self.tk_img.height())
        self.preview_label.delete("all")
        self.preview_label.create_image(0, 0, anchor="nw", image=self.tk_img)

        # Limpiar rectángulos anteriores
        self.ocr_region_rects = []

        # Dibujar regiones OCR
        scale_x = self.tk_img.width() / self.captured_image.shape[1]
        scale_y = self.tk_img.height() / self.captured_image.shape[0]
        for region in self.ocr_regions:
            x1 = int(region['left'] * scale_x)
            y1 = int(region['top'] * scale_y)
            x2 = int((region['left'] + region['width']) * scale_x)
            y2 = int((region['top'] + region['height']) * scale_y)
            rect_id = self.preview_label.create_rectangle(x1, y1, x2, y2, outline="red", width=2, tags="ocr_region")
            self.ocr_region_rects.append(rect_id)


    def mark_ocr_region(self):
        """Abre ventana para seleccionar región OCR y la añade a la lista."""
        if self.captured_image is None:
            messagebox.showerror("Error", "Primero carga una imagen.")
            return
        region = tk_select_ocr_region(self, self.captured_image, max_width=MAX_PREVIEW_WIDTH)
        if region:
            self.ocr_regions.append(region)
            self.update_region_label()
            self.show_preview()
        else:
            messagebox.showinfo("Información", "No se seleccionó ninguna región.")


    def update_region_label(self):
        """Actualiza el label que muestra las zonas OCR."""
        if self.ocr_regions:
            self.region_label.config(text=f"Zonas OCR: {len(self.ocr_regions)} definidas")
        else:
            self.region_label.config(text="Zonas OCR: Ninguna definida")


    def clear_ocr_regions(self):
        """Limpia lista de regiones OCR, previsualización y label."""
        self.ocr_regions = []
        self.update_region_label()
        self.show_preview()


    def save_ocr_regions(self):
        """Guarda regiones OCR en ocr_regions.json."""
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showerror("Error", "Debes seleccionar un nombre de plantilla.")
            return

        mapping = load_ocr_mapping()
        mapping[template_name] = self.ocr_regions
        save_ocr_mapping(mapping)
        messagebox.showinfo("Éxito", f"Zonas OCR guardadas para '{template_name}'.")
        self.status_message(f"Zonas OCR guardadas para '{template_name}'.")
        self.current_template_name = template_name
        self.clear_ocr_regions()


    def status_message(self, message):
        """Actualiza el mensaje en el label de estado."""
        self.status_label_var.set(message)
        self.update_idletasks()


    def save_last_image_source(self):
        """Guarda la opción de origen de imagen seleccionada."""
        config = {"last_image_source": self.source_var.get()}
        try:
            config_path = os.path.join(PROJECT_DIR, "config.json") # Guardar config.json en el directorio raíz
            with open(config_path, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error al guardar la configuración de origen de imagen: {e}")


    def load_last_image_source(self):
        """Carga la última opción de origen de imagen seleccionada al iniciar."""
        try:
            config_path = os.path.join(PROJECT_DIR, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    last_source = config.get("last_image_source")
                    if last_source in ("capture", "file"):
                        # --- Asegurar que self.source_var exista antes de usarla ---
                        if hasattr(self, 'source_var'):
                            self.source_var.set(last_source)
                        else:
                            # Crear la variable si aún no existe (puede pasar si se llama antes de create_widgets)
                            self.source_var = tk.StringVar(value=last_source)

        except Exception as e:
            print(f"Error al cargar la configuración de origen de imagen: {e}")


if __name__ == "__main__":
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    app = TemplateManagerGUI()
    app.mainloop()