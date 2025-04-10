import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import mss
from tkinter import font
import logging # Asegúrate que esta importación esté presente

# --- Constantes del proyecto ---
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")
OCR_MAPPING_FILE_PATH = os.path.join(CONFIG_DIR, "ocr_regions.json")
TEMPLATE_MAPPING_FILE_PATH = os.path.join(CONFIG_DIR, "templates_mapping.json")
MAX_PREVIEW_WIDTH = 800
PREVIEW_THUMBNAIL_SIZE = (600, 500)
DEFAULT_FONT_SIZE = 11

# --- <<< AÑADIR CONSTANTES DE TAMAÑO MÍNIMO >>> ---
MIN_WINDOW_WIDTH = 850 # Ajusta según sea necesario
MIN_WINDOW_HEIGHT = 750 # Ajusta según sea necesario
MIN_CANVAS_WIDTH = 300
MIN_CANVAS_HEIGHT = 200
# ----------------------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper function to load template mapping dictionary ---
def load_template_mapping_dict():
    """Carga el mapping de plantillas desde el archivo JSON."""
    try:
        os.makedirs(os.path.dirname(TEMPLATE_MAPPING_FILE_PATH), exist_ok=True) # Crear dir si no existe
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

# --- load_ocr_mapping, save_ocr_mapping, capture_screen ---
# --- tk_select_ocr_region, tk_select_monitor_region ---
# (Estas funciones se mantienen igual que en la versión anterior que funcionaba)

def load_ocr_mapping():
    """Carga el mapping de zonas OCR desde el archivo JSON."""
    try:
        os.makedirs(os.path.dirname(OCR_MAPPING_FILE_PATH), exist_ok=True)
        with open(OCR_MAPPING_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Archivo {OCR_MAPPING_FILE_PATH} no encontrado. Creando uno nuevo.")
        return {}
    except json.JSONDecodeError:
        messagebox.showerror("Error", f"Error al leer el archivo JSON {OCR_MAPPING_FILE_PATH}. Puede estar corrupto.")
        return {}
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado al cargar el mapping OCR: {e}")
        return {}

def save_ocr_mapping(mapping):
    """Guarda el mapping de zonas OCR en el archivo JSON."""
    try:
        os.makedirs(os.path.dirname(OCR_MAPPING_FILE_PATH), exist_ok=True)
        with open(OCR_MAPPING_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar el mapping OCR: {e}")

def capture_screen(region=None, monitor=1):
    """Captura la pantalla (o una región específica) usando mss."""
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if monitor < 1 or monitor >= len(monitors):
                 messagebox.showerror("Error", f"Monitor {monitor} no válido. Monitores disponibles: 1 a {len(monitors)-1}")
                 return None
            if region is None:
                region = monitors[monitor]
            sct_img = sct.grab(region)
            img = np.array(sct_img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr
    except Exception as e:
        messagebox.showerror("Error", f"Error al capturar la pantalla: {e}")
        return None

def tk_select_ocr_region(root, image, max_width=MAX_PREVIEW_WIDTH):
    """Permite al usuario seleccionar una región en la imagen."""
    # (Código de tk_select_ocr_region sin cambios)
    orig_height, orig_width = image.shape[:2]
    scale = 1.0
    if orig_width > max_width:
        scale = MAX_PREVIEW_WIDTH / orig_width # Usar constante
        resized_img = cv2.resize(image, (int(orig_width * scale), int(orig_height * scale)))
    else:
        resized_img = image.copy()
    img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    tk_img = ImageTk.PhotoImage(pil_img)
    sel_win = tk.Toplevel(root)
    sel_win.title("Seleccione Región OCR")
    sel_win.grab_set()
    sel_win.minsize(400, 300)
    canvas_frame = ttk.Frame(sel_win)
    canvas_frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(canvas_frame, width=tk_img.width(), height=tk_img.height(), cursor="cross")
    canvas.pack(padx=5, pady=5, fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    selection = {"x1": None, "y1": None, "x2": None, "y2": None}
    rect = None
    coord_label_var = tk.StringVar(value="Coordenadas: ")
    coord_label = ttk.Label(sel_win, textvariable=coord_label_var)
    coord_label.pack()
    def update_coord_label(x, y): coord_label_var.set(f"Coordenadas (Resize): x={x}, y={y}")
    def on_button_press(event):
        selection["x1"] = event.x
        selection["y1"] = event.y
        nonlocal rect
        if rect: canvas.delete(rect)
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="green", width=2)
        update_coord_label(event.x, event.y)
    def on_move_press(event):
        if rect:
            canvas.coords(rect, selection["x1"], selection["y1"], event.x, event.y)
            update_coord_label(event.x, event.y)
    def on_button_release(event):
        if rect:
            selection["x2"] = event.x
            selection["y2"] = event.y
            update_coord_label(event.x, event.y)
    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)
    canvas.bind("<Motion>", lambda event: update_coord_label(event.x, event.y))
    button_frame = ttk.Frame(sel_win)
    button_frame.pack(pady=5)
    def confirm_selection(): sel_win.destroy()
    def cancel_selection(): selection["x1"] = None; sel_win.destroy()
    confirm_btn = ttk.Button(button_frame, text="Confirmar Selección", command=confirm_selection)
    confirm_btn.pack(side="left", padx=5)
    cancel_btn = ttk.Button(button_frame, text="Cancelar Selección", command=cancel_selection)
    cancel_btn.pack(side="left", padx=5)
    root.wait_window(sel_win)
    if None not in (selection["x1"], selection["y1"], selection["x2"], selection["y2"]):
        x1, y1 = selection["x1"], selection["y1"]
        x2, y2 = selection["x2"], selection["y2"]
        left_resized = int(min(x1, x2))
        top_resized = int(min(y1, y2))
        width_resized = int(abs(x2 - x1))
        height_resized = int(abs(y2 - y1))
        left_orig = int(left_resized / scale)
        top_orig = int(top_resized / scale)
        width_orig = int(width_resized / scale)
        height_orig = int(height_resized / scale)
        return {"left": left_orig, "top": top_orig, "width": width_orig, "height": height_orig}
    return None

def tk_select_monitor_region(root, monitor_img):
    """Permite al usuario seleccionar una región del monitor."""
    # (Código de tk_select_monitor_region sin cambios)
    orig_height, orig_width = monitor_img.shape[:2]
    scale = 1.0
    max_sel_width = 1200
    if orig_width > max_sel_width:
        scale = max_sel_width / orig_width
        resized_img = cv2.resize(monitor_img, (int(orig_width * scale), int(orig_height * scale)))
    else:
        resized_img = monitor_img.copy()
    img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    tk_img = ImageTk.PhotoImage(pil_img)
    sel_win = tk.Toplevel(root)
    sel_win.title("Seleccione Región del Monitor")
    sel_win.grab_set()
    sel_win.attributes('-fullscreen', True)
    sel_win.attributes('-alpha', 0.3)
    sel_win.configure(cursor="cross")
    canvas = tk.Canvas(sel_win, width=tk_img.width(), height=tk_img.height(), highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    selection = {"x1": None, "y1": None, "x2": None, "y2": None}
    rect = None
    confirmed_region = None
    def on_button_press(event):
        selection["x1"] = event.x
        selection["y1"] = event.y
        nonlocal rect
        if rect: canvas.delete(rect)
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="blue", width=2, fill='blue', stipple='gray12')
    def on_move_press(event):
        if rect:
            canvas.coords(rect, selection["x1"], selection["y1"], event.x, event.y)
    def on_button_release(event):
        if rect:
            selection["x2"] = event.x
            selection["y2"] = event.y
            confirm_selection()
    def confirm_selection():
        nonlocal confirmed_region
        if None not in (selection["x1"], selection["y1"], selection["x2"], selection["y2"]):
            x1, y1 = selection["x1"], selection["y1"]
            x2, y2 = selection["x2"], selection["y2"]
            left_resized = int(min(x1, x2))
            top_resized = int(min(y1, y2))
            width_resized = int(abs(x2 - x1))
            height_resized = int(abs(y2 - y1))
            monitor_info = root.monitors_info[root.monitor_var.get()]
            left_orig = monitor_info['left'] + int(left_resized / scale)
            top_orig = monitor_info['top'] + int(top_resized / scale)
            width_orig = int(width_resized / scale)
            height_orig = int(height_resized / scale)
            confirmed_region = {"left": left_orig, "top": top_orig, "width": width_orig, "height": height_orig}
        sel_win.destroy()
    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)
    sel_win.bind("<Escape>", lambda e: sel_win.destroy())
    root.wait_window(sel_win)
    return confirmed_region


class TemplateManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Zonas OCR y Plantillas")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT) # <<< Aplicar tamaño mínimo >>>

        self.captured_image = None
        self.selected_image_path = None
        self.ocr_regions = []
        self.ocr_region_rects = []
        self.current_template_name = None
        self.template_names_mapping = {}
        self.ocr_regions_mapping = {}
        self.monitors_info = self.detect_monitors()

        # --- Configuración de fuente y estilo ---
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=DEFAULT_FONT_SIZE)
        style = ttk.Style(self)
        style.configure('.', font=self.default_font)
        style.configure('TLabelframe.Label', font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE, 'bold'))

        self.create_widgets()
        self.load_template_names_from_json()
        self.load_ocr_regions_from_json()
        # No cargar last image source aquí, depende de la selección

    def detect_monitors(self):
        """Detecta los monitores existentes usando mss."""
        try:
            with mss.mss() as sct:
                # Devolver la lista completa, el índice 0 es 'all screens'
                return sct.monitors
        except Exception as e:
            logging.error(f"Error detectando monitores: {e}")
            return [{}] # Devuelve una lista con un diccionario vacío si falla

    def load_template_data(self):
        """Carga nombres de plantillas y regiones OCR al inicio."""
        self.load_template_names_from_json()
        self.load_ocr_regions_from_json()

    def load_ocr_regions_from_json(self):
        """Carga las regiones OCR desde ocr_regions.json."""
        self.ocr_regions_mapping = load_ocr_mapping()

    def create_widgets(self):
        # Configurar grid principal
        self.grid_rowconfigure(2, weight=1) # Fila de los frames centrales se expande
        self.grid_columnconfigure(0, weight=1) # Columna principal se expande

        self.create_capture_frame()
        self.create_template_selection_frame()

        center_frame = ttk.Frame(self)
        center_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        center_frame.grid_columnconfigure(1, weight=1)

        self.create_preview_frame(center_frame)
        self.create_ocr_config_frame(center_frame)

        self.create_status_label()

    def create_capture_frame(self):
        """Crea el frame para capturar nuevas plantillas."""
        capture_frame = ttk.LabelFrame(self, text="Capturar Nueva Plantilla", padding=(10, 5))
        capture_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        self.capture_type_var = tk.StringVar(value="monitor")
        capture_type_frame = ttk.Frame(capture_frame)
        capture_type_frame.pack(anchor="w", padx=5, pady=2)
        ttk.Radiobutton(capture_type_frame, text="Monitor Completo", variable=self.capture_type_var, value="monitor").pack(side="left", padx=5)
        ttk.Radiobutton(capture_type_frame, text="Región del Monitor", variable=self.capture_type_var, value="region").pack(side="left", padx=5)

        self.monitor_var = tk.IntVar(value=1)
        monitor_frame = ttk.Frame(capture_frame)
        monitor_frame.pack(anchor="w", padx=5, pady=2)
        ttk.Label(monitor_frame, text="Monitor:").pack(side="left", padx=5)
        num_monitors = len(self.monitors_info) - 1 if len(self.monitors_info) > 1 else 1
        self.monitor_spinbox = ttk.Spinbox(monitor_frame, from_=1, to=num_monitors, textvariable=self.monitor_var, width=5)
        self.monitor_spinbox.pack(side="left", padx=5)

        ttk.Button(capture_frame, text="Capturar Pantalla", command=self.capture_new_template).pack(anchor="w", padx=5, pady=5)

        self.new_template_name_var = tk.StringVar()
        name_frame = ttk.Frame(capture_frame)
        name_frame.pack(anchor="w", padx=5, pady=2)
        ttk.Label(name_frame, text="Nombre Nueva Plantilla:").pack(side="left", padx=5)
        ttk.Entry(name_frame, textvariable=self.new_template_name_var, width=30).pack(side="left", padx=5)

        ttk.Button(capture_frame, text="Guardar Nueva Plantilla", command=self.save_new_template).pack(anchor="w", padx=5, pady=5)


    def create_template_selection_frame(self):
        """Crea el frame para seleccionar plantillas existentes."""
        template_frame = ttk.LabelFrame(self, text="Seleccionar Plantilla Existente", padding=(10, 5))
        template_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        combo_frame = ttk.Frame(template_frame)
        combo_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(combo_frame, text="Plantilla Existente:").pack(side="left", padx=5, pady=5)
        self.template_name_var = tk.StringVar()
        self.template_name_combobox = ttk.Combobox(combo_frame, textvariable=self.template_name_var, width=30)
        self.template_name_combobox.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.template_name_combobox.bind("<<ComboboxSelected>>", self.on_template_name_selected)

        ttk.Button(combo_frame, text="Refrescar Lista", command=self.load_template_names_from_json).pack(side="left", padx=5, pady=5)

    def create_preview_frame(self, parent_frame):
        """Crea el frame de previsualización de la imagen."""
        preview_frame = ttk.LabelFrame(parent_frame, text="Previsualización de la Imagen", padding=(10, 5))
        preview_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_label = tk.Canvas(preview_frame, width=MIN_CANVAS_WIDTH, height=MIN_CANVAS_HEIGHT, bg="lightgrey")
        self.preview_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_label.bind("<Configure>", lambda event: self.show_preview())

    def create_ocr_config_frame(self, parent_frame):
        """Crea el frame para la configuración de zonas OCR."""
        config_frame = ttk.LabelFrame(parent_frame, text="Configuración de Zona OCR", padding=(10, 5))
        config_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        config_frame.grid_columnconfigure(0, weight=1)

        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=0, column=0, pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(button_frame, text="Marcar Región OCR", command=self.mark_ocr_region).pack(pady=2)
        ttk.Button(button_frame, text="Limpiar Zonas OCR", command=self.clear_ocr_regions).pack(pady=2)

        self.region_label = ttk.Label(config_frame, text="Zonas OCR: Ninguna definida", anchor="center")
        self.region_label.grid(row=1, column=0, pady=5, sticky="ew")

        save_button = ttk.Button(config_frame, text="Guardar Zonas OCR", command=self.save_ocr_regions)
        save_button.grid(row=2, column=0, padx=5, pady=5)

    def create_status_label(self):
        """Crea el label para mensajes de estado."""
        self.status_label_var = tk.StringVar(value="Listo.")
        self.status_label = ttk.Label(self, textvariable=self.status_label_var, anchor="w")
        self.status_label.grid(row=4, column=0, padx=10, pady=(5, 10), sticky="ew")

    # --- CORRECCIÓN: Indentación de load_template_names_from_json ---
    def load_template_names_from_json(self):
        """Carga nombres de plantillas desde templates_mapping.json y actualiza el Combobox."""
        try:
            mapping = load_template_mapping_dict()
            self.template_names_mapping = mapping
            template_names = sorted(list(self.template_names_mapping.keys())) # Ordenar
            self.template_name_combobox['values'] = template_names
            self.status_message("Lista de plantillas refrescada.")
        except Exception as e:
            logging.error(f"Error inesperado al cargar nombres de plantillas: {e}")
            messagebox.showerror("Error", f"Error inesperado al cargar nombres de plantillas: {e}")


    def on_template_name_selected(self, event):
        """Se llama al seleccionar un nombre de plantilla del Combobox."""
        selected_name = self.template_name_var.get()
        if selected_name:
            self.clear_ocr_regions()
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
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al cargar imagen para '{selected_name}': {e}")
                        self.status_message("Error al cargar imagen.")
                        self.captured_image = None
                else:
                    messagebox.showwarning("Advertencia", f"Archivo de imagen '{first_image_file}' no encontrado para '{selected_name}'.")
                    self.captured_image = None
            else:
                 messagebox.showwarning("Advertencia", f"No hay archivos de imagen listados para '{selected_name}'.")
                 self.captured_image = None

            if self.captured_image is not None:
                self.status_message(f"Plantilla '{selected_name}' cargada.")
            else:
                self.status_message(f"Error o no se encontró imagen para '{selected_name}'.")

            if selected_name in self.ocr_regions_mapping:
                self.ocr_regions = self.ocr_regions_mapping[selected_name]
                self.status_message(f"Regiones OCR cargadas para '{selected_name}'.")
            else:
                self.ocr_regions = []
                if self.captured_image is not None:
                    self.status_message(f"Plantilla '{selected_name}' seleccionada. No hay regiones OCR guardadas.")

            self.update_region_label()
            self.show_preview()


    def capture_new_template(self):
        """Captura una nueva plantilla desde la pantalla, según el tipo seleccionado."""
        self.status_message("Capturando pantalla...")
        capture_type = self.capture_type_var.get()
        monitor_idx = self.monitor_var.get() # 1-based index

        monitor_index_in_list = monitor_idx # Ajustar para el índice real de mss.monitors
        if monitor_index_in_list < 1 or monitor_index_in_list >= len(self.monitors_info):
             messagebox.showerror("Error", f"Índice de monitor {monitor_idx} no válido.")
             self.status_message("Error: Índice de monitor inválido.")
             return

        target_monitor_info = self.monitors_info[monitor_index_in_list]

        if capture_type == "monitor":
             self.captured_image = capture_screen(monitor=monitor_idx)
        elif capture_type == "region":
            self.withdraw()
            self.update_idletasks()
            tk.Tk().after(200, lambda: self._capture_region_after_delay(monitor_idx))
            return

        if self.captured_image is not None:
            self.selected_image_path = None
            self.show_preview()
            self.status_message("Pantalla capturada. Previsualizando...")
        else:
            self.status_message("Captura cancelada o fallida.")


    def _capture_region_after_delay(self, monitor_idx):
        """Función auxiliar para capturar región tras un delay."""
        monitor_image = capture_screen(monitor=monitor_idx)
        self.deiconify()
        if monitor_image is not None:
            region = tk_select_monitor_region(self, monitor_image)
            if region:
                self.captured_image = capture_screen(region=region, monitor=monitor_idx)
            else:
                self.captured_image = None
        else:
            self.captured_image = None

        if self.captured_image is not None:
            self.selected_image_path = None
            self.show_preview()
            self.status_message("Región capturada. Previsualizando...")
        else:
            self.status_message("Captura de región cancelada o fallida.")


    # --- CORRECCIÓN: Indentación correcta de save_new_template ---
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

            # --- CORRECCIÓN: Usar helper para cargar mapping ---
            mapping = load_template_mapping_dict()
            if template_name in mapping:
                if isinstance(mapping[template_name], list):
                    mapping[template_name].append(image_filename)
                else:
                    mapping[template_name] = [mapping[template_name], image_filename]
                logging.info(f"Añadiendo imagen {image_filename} a plantilla existente '{template_name}'.")
            else:
                mapping[template_name] = [image_filename]
                logging.info(f"Creando nueva plantilla '{template_name}' con imagen {image_filename}.")

            # Guardar el mapping actualizado
            try:
                os.makedirs(os.path.dirname(TEMPLATE_MAPPING_FILE_PATH), exist_ok=True)
                with open(TEMPLATE_MAPPING_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(mapping, f, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar {TEMPLATE_MAPPING_FILE_PATH}: {e}")
                logging.error(f"Error al guardar {TEMPLATE_MAPPING_FILE_PATH}: {e}")
                return

            self.load_template_names_from_json()
            self.template_name_var.set(template_name)
            self.on_template_name_selected(None)
            self.new_template_name_var.set("")

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la plantilla: {e}")
            # --- CORRECCIÓN: Usar logging si está importado ---
            logging.error(f"Error al guardar la plantilla: {e}")
            self.status_message("Error al guardar plantilla.")


    def load_image(self):
        """Carga la imagen desde archivo."""
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
            # Asociar con plantilla existente si el nombre base coincide
            base_filename = os.path.basename(file_path)
            found_template_name = None
            for name, files in self.template_names_mapping.items():
                if base_filename in files:
                    found_template_name = name
                    break
            if found_template_name:
                 self.template_name_var.set(found_template_name)
                 self.on_template_name_selected(None) # Cargar regiones OCR
            else:
                 self.template_name_var.set("") # Limpiar selección si no coincide
                 self.show_preview()

            self.status_message("Imagen cargada desde archivo.")
            self.display_image_path()
        else:
            self.status_message("Carga de imagen desde archivo cancelada.")

    def display_image_path(self):
        """Muestra la ruta del archivo de imagen en el label de estado."""
        if self.selected_image_path:
            self.status_message(f"Imagen cargada desde: {self.selected_image_path}")
        # Ya no tenemos captura directa en esta GUI


    def show_preview(self):
        """Muestra la imagen en el canvas de previsualización y dibuja regiones OCR."""
        # (Código de show_preview sin cambios respecto a la versión anterior con redimensionamiento)
        try:
            canvas_width = self.preview_label.winfo_width()
            canvas_height = self.preview_label.winfo_height()
        except tk.TclError:
            canvas_width = MIN_CANVAS_WIDTH
            canvas_height = MIN_CANVAS_HEIGHT

        if canvas_width < MIN_CANVAS_WIDTH: canvas_width = MIN_CANVAS_WIDTH
        if canvas_height < MIN_CANVAS_HEIGHT: canvas_height = MIN_CANVAS_HEIGHT

        self.preview_label.delete("all")

        if self.captured_image is None:
            self.preview_label.config(width=canvas_width, height=canvas_height)
            self.preview_label.create_text(canvas_width/2, canvas_height/2, text="No hay imagen cargada", fill="grey", font=self.default_font)
            return

        img_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        img_aspect = pil_img.width / pil_img.height
        canvas_aspect = canvas_width / canvas_height
        if img_aspect > canvas_aspect:
            new_width = canvas_width
            new_height = int(new_width / img_aspect)
        else:
            new_height = canvas_height
            new_width = int(new_height * img_aspect)
        new_width = max(1, min(new_width, canvas_width))
        new_height = max(1, min(new_height, canvas_height))
        try: resample_method = Image.Resampling.LANCZOS
        except AttributeError: resample_method = Image.ANTIALIAS
        pil_img = pil_img.resize((new_width, new_height), resample_method)
        self.tk_img = ImageTk.PhotoImage(pil_img)
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2
        self.preview_label.create_image(x_offset, y_offset, anchor="nw", image=self.tk_img)
        self.ocr_region_rects = []
        scale_x = new_width / self.captured_image.shape[1]
        scale_y = new_height / self.captured_image.shape[0]
        for region in self.ocr_regions:
            try:
                x1 = int(region['region']['left'] * scale_x) + x_offset # <<< ACCEDER A 'region' >>>
                y1 = int(region['region']['top'] * scale_y) + y_offset
                x2 = int((region['region']['left'] + region['region']['width']) * scale_x) + x_offset
                y2 = int((region['region']['top'] + region['region']['height']) * scale_y) + y_offset
                # Cambiar color si tiene texto esperado
                outline_color = "purple" if region.get('expected_text') else "red"
                rect_id = self.preview_label.create_rectangle(x1, y1, x2, y2, outline=outline_color, width=2, tags="ocr_region")
                self.ocr_region_rects.append(rect_id)
            except KeyError:
                logging.warning(f"Región OCR mal formada encontrada: {region}")
            except Exception as e:
                logging.error(f"Error dibujando región OCR {region}: {e}")
        self.preview_label.config(width=canvas_width, height=canvas_height)

    def mark_ocr_region(self):
        """Abre ventana para seleccionar región OCR y la añade a la lista."""
        if self.captured_image is None:
            messagebox.showerror("Error", "Primero carga o captura una imagen.")
            return
        region_coords = tk_select_ocr_region(self, self.captured_image, max_width=MAX_PREVIEW_WIDTH)
        if region_coords:
            # Añadir la región con la nueva estructura
            self.ocr_regions.append({"region": region_coords, "expected_text": []})
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
            messagebox.showerror("Error", "Debes seleccionar un nombre de plantilla existente del Combobox.")
            return
        if not self.ocr_regions:
            # Permitir guardar una lista vacía para eliminar regiones de una plantilla
            if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar TODAS las zonas OCR para '{template_name}'?"):
                 logging.info(f"Eliminando todas las regiones OCR para '{template_name}'.")
            else:
                 self.status_message("Guardado de zonas OCR cancelado.")
                 return

        mapping = load_ocr_mapping()
        mapping[template_name] = self.ocr_regions # Guardar la lista actual (puede estar vacía)
        save_ocr_mapping(mapping) # Usar la función global
        messagebox.showinfo("Éxito", f"Zonas OCR guardadas para '{template_name}'.")
        self.status_message(f"Zonas OCR guardadas para '{template_name}'.")
        self.current_template_name = template_name
        # Actualizar el mapping en memoria
        self.ocr_regions_mapping[template_name] = self.ocr_regions
        # No limpiar automáticamente, el usuario puede querer seguir modificando
        # self.clear_ocr_regions()


    def status_message(self, message):
        """Actualiza el mensaje en el label de estado."""
        self.status_label_var.set(message)
        self.update_idletasks()

if __name__ == "__main__":
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    app = TemplateManagerGUI()
    app.bind("<Configure>", lambda event: app.show_preview() if hasattr(app, 'preview_label') and app.preview_label.winfo_exists() else None)
    app.mainloop()