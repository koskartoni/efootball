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
import time
import logging
import subprocess
import sys
import re # Importar re para limpieza si es necesario (aunque la limpieza principal está en recognizer)

# --- Importar lo necesario desde screen_recognizer ---
# Importar la clase, la función de GUARDADO genérica, la función de CARGA genérica,
# y las constantes de RUTA necesarias.
from screen_recognizer import (
    ScreenRecognizer,
    save_json_mapping,      # <<< Función genérica de guardado >>>
    load_json_mapping,      # <<< Función genérica de carga >>>
    OCR_MAPPING_FILE,       # <<< Constante de ruta OCR >>>
    TEMPLATE_MAPPING_FILE,  # <<< Constante de ruta Templates >>>
    DEFAULT_FONT_SIZE,      # <<< Constante de fuente (si está allí) >>>
    PROJECT_DIR,            # <<< Constante de ruta Proyecto >>>
    IMAGES_DIR              # <<< Constante de ruta Imágenes >>>
)

# --- Definir constantes locales (si no se importan) ---
# DEFAULT_FONT_SIZE = 11 # Comentado si se importa
MIN_WINDOW_WIDTH = 850
MIN_WINDOW_HEIGHT = 750
MIN_CANVAS_WIDTH = 300
MIN_CANVAS_HEIGHT = 200
LOG_FILE = "tester_log.log" # Nombre del archivo de log

# --- Configuración del Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Ruta al script de la GUI de gestión de plantillas
TEMPLATE_MANAGER_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "template_manager_gui.py")


class ScreenTesterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tester Interactivo - Screen Recognizer")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # --- Inicializar atributos ---
        self.captured_image = None # El tester no gestiona captura directa
        self.selected_image_path = None
        self.ocr_regions = [] # Regiones del estado actualmente mostrado/validado por el tester
        self.ocr_region_rects = []
        self.current_template_name = None # Nombre del estado seleccionado en el combo de corrección
        self.last_recognition_result = None # Último resultado del recognizer

        # --- Instancia del Reconocedor ---
        # Se asume que ScreenRecognizer carga sus propios mappings en su __init__
        self.recognizer = ScreenRecognizer(monitor=1, threshold=0.75, ocr_fallback_threshold=0.65)
        # Obtener info de monitores desde la instancia (o detectar como fallback)
        self.monitors_info = self.recognizer.monitors_info if hasattr(self.recognizer, 'monitors_info') else self._detect_monitors_fallback()

        # --- Configuración de fuente y estilo ---
        self.setup_fonts_and_styles()

        # --- Crear Widgets ---
        self.create_widgets()

        logging.info("Tester GUI inicializado.")

    def setup_fonts_and_styles(self):
        """Configura la fuente y los estilos ttk."""
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=DEFAULT_FONT_SIZE)
        style = ttk.Style(self)
        style.configure('.', font=self.default_font)
        style.configure('TLabelframe.Label', font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE, 'bold'))
        style.configure("Result.TLabel", font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE + 2, 'bold'))
        style.configure("Confirm.TButton", font=self.default_font)
        style.configure("Deny.TButton", font=self.default_font)

    def _detect_monitors_fallback(self):
        """Detecta los monitores existentes usando mss (si no está en recognizer)."""
        logging.warning("Intentando detectar monitores desde el Tester GUI (fallback).")
        try:
            with mss.mss() as sct:
                monitors = [m for i, m in enumerate(sct.monitors) if i > 0]
                return monitors
        except Exception as e:
            logging.error(f"Error detectando monitores (fallback): {e}")
            return []

    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        self.grid_rowconfigure(3, weight=1) # Fila OCR/Corrección se expande
        self.grid_columnconfigure(0, weight=1)

        self.create_control_frame()
        self.create_result_frame()
        self.create_correction_frame() # Crear pero no mostrar inicialmente
        self.create_ocr_details_frame() # Crear pero no mostrar inicialmente
        self.create_status_label()

        # Poblar combobox de corrección inicialmente
        self._populate_correction_combobox()


    def create_control_frame(self):
        """Crea el frame con los botones de control."""
        control_frame = ttk.LabelFrame(self, text="Control", padding=(10, 5))
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)

        self.test_button = ttk.Button(control_frame, text="Reconocer Pantalla Actual", command=self.run_test)
        self.test_button.grid(row=0, column=0, pady=5, padx=5, sticky="e")

        self.reload_button = ttk.Button(control_frame, text="Recargar Datos Reconocedor", command=self.reload_recognizer_data)
        self.reload_button.grid(row=0, column=1, pady=5, padx=5, sticky="w")

    def create_result_frame(self):
        """Crea el frame para mostrar los resultados del reconocimiento."""
        result_frame = ttk.LabelFrame(self, text="Resultado del Reconocimiento", padding=(10, 5))
        result_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        result_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(result_frame, text="Método:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.method_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.method_var, style="Result.TLabel").grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(result_frame, text="Estado Detectado:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.state_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.state_var, style="Result.TLabel").grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(result_frame, text="Confianza (Template):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.confidence_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.confidence_var).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(result_frame, text="Tiempo Detección:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.time_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.time_var).grid(row=3, column=1, padx=5, pady=2, sticky="w")

        # --- Botones de Confirmación/Negación/Lanzar ---
        validation_frame = ttk.Frame(result_frame)
        validation_frame.grid(row=4, column=0, columnspan=2, pady=5)
        self.confirm_button = ttk.Button(validation_frame, text="👍 Confirmar Detección", style="Confirm.TButton", command=self.confirm_detection, state="disabled")
        self.confirm_button.pack(side="left", padx=10)
        self.deny_button = ttk.Button(validation_frame, text="👎 Negar Detección", style="Deny.TButton", command=self.deny_detection, state="disabled")
        self.deny_button.pack(side="left", padx=10)
        self.launch_capture_button = ttk.Button(validation_frame, text="Abrir Gestor Plantillas", command=self.launch_template_manager, state="disabled")
        self.launch_capture_button.pack(side="left", padx=10)

    def create_correction_frame(self):
        """Crea el frame para la corrección manual (inicialmente oculto)."""
        self.correction_frame = ttk.LabelFrame(self, text="Corrección Manual", padding=(10, 5))
        self.correction_frame.grid_columnconfigure(1, weight=1)
        # No hacer grid aquí, se hará en deny_detection o run_test

        ttk.Label(self.correction_frame, text="Estado Correcto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.correct_state_var = tk.StringVar()
        self.correct_state_combo = ttk.Combobox(self.correction_frame, textvariable=self.correct_state_var, width=35, state="readonly") # readonly para evitar escritura manual
        self.correct_state_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.log_correction_button = ttk.Button(self.correction_frame, text="Registrar Corrección", command=self.log_correct_state)
        self.log_correction_button.grid(row=0, column=2, padx=10, pady=5)

    def create_ocr_details_frame(self):
        """Crea el frame para detalles y edición OCR (inicialmente oculto)."""
        self.ocr_frame = ttk.LabelFrame(self, text="Detalles y Edición OCR", padding=(10, 5))
        self.ocr_frame.grid_rowconfigure(1, weight=1)
        self.ocr_frame.grid_columnconfigure(0, weight=1)
        # No hacer grid aquí, se hará en run_test

        ttk.Label(self.ocr_frame, text="Resultados OCR por Región:").grid(row=0, column=0, columnspan=3, padx=5, pady=2, sticky="w")

        self.ocr_tree = ttk.Treeview(self.ocr_frame, columns=("RegionIdx", "Extracted", "Expected", "Match"), show="headings", height=5)
        self.ocr_tree.heading("RegionIdx", text="Región #")
        self.ocr_tree.heading("Extracted", text="Texto Extraído")
        self.ocr_tree.heading("Expected", text="Texto Esperado")
        self.ocr_tree.heading("Match", text="Coincide")
        self.ocr_tree.column("RegionIdx", width=60, anchor="center")
        self.ocr_tree.column("Extracted", width=200)
        self.ocr_tree.column("Expected", width=200)
        self.ocr_tree.column("Match", width=70, anchor="center")
        self.ocr_tree.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        ocr_scrollbar = ttk.Scrollbar(self.ocr_frame, orient="vertical", command=self.ocr_tree.yview)
        ocr_scrollbar.grid(row=1, column=2, sticky="ns")
        self.ocr_tree['yscrollcommand'] = ocr_scrollbar.set

        ttk.Label(self.ocr_frame, text="Texto Correcto Esperado (p/ Selección, separar con '|'):").grid(row=2, column=0, columnspan=3, padx=5, pady=2, sticky="w")
        self.ocr_edit_var = tk.StringVar()
        self.ocr_edit_entry = ttk.Entry(self.ocr_frame, textvariable=self.ocr_edit_var, width=60)
        self.ocr_edit_entry.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        ocr_button_frame = ttk.Frame(self.ocr_frame)
        ocr_button_frame.grid(row=4, column=0, columnspan=3, pady=5)
        self.confirm_ocr_button = ttk.Button(ocr_button_frame, text="Confirmar Texto(s) Extraído(s) p/ Selección", command=self.confirm_ocr_text)
        self.confirm_ocr_button.pack(side="left", padx=10)
        self.save_edited_button = ttk.Button(ocr_button_frame, text="Guardar Texto Editado p/ Selección", command=self.save_edited_ocr_text)
        self.save_edited_button.pack(side="left", padx=10)

    def create_status_label(self):
        """Crea el label para mensajes de estado."""
        self.status_label_var = tk.StringVar(value="Listo. Inicia el juego y pulsa 'Reconocer Pantalla'.")
        self.status_label = ttk.Label(self, textvariable=self.status_label_var, anchor="w")
        self.status_label.grid(row=4, column=0, padx=10, pady=(5, 10), sticky="ew") # Fila 4 inicial

    def _populate_correction_combobox(self):
        """Llena el combobox de corrección con los nombres ordenados."""
        try:
            # Cargar nombres desde la instancia del recognizer (que ya los cargó)
            mapping = self.recognizer.template_names_mapping if hasattr(self.recognizer, 'template_names_mapping') else {}
            template_names = sorted(list(mapping.keys()))
            self.correct_state_combo['values'] = template_names
        except Exception as e:
            logging.error(f"Error al poblar combobox de corrección: {e}")
            self.correct_state_combo['values'] = []

    def reload_recognizer_data(self):
        """Llama al método de recarga del reconocedor."""
        self.status_message("Recargando datos del reconocedor...")
        try:
            self.recognizer.reload_data()
            self._populate_correction_combobox() # Actualizar combobox
            self.status_message("Datos del reconocedor recargados.")
            logging.info("Datos del reconocedor recargados manualmente.")
        except AttributeError:
             logging.error("Intento de recarga fallido: método reload_data() no encontrado en ScreenRecognizer.")
             messagebox.showerror("Error", "La clase ScreenRecognizer no tiene el método 'reload_data'.")
        except Exception as e:
             logging.error(f"Error al recargar datos: {e}")
             messagebox.showerror("Error", f"Error al recargar datos: {e}")

    def run_test(self):
        """Ejecuta el reconocimiento y actualiza la GUI."""
        self.status_message("Reconociendo pantalla...")
        # Deshabilitar y ocultar frames de acción/detalle
        self.confirm_button.config(state="disabled")
        self.deny_button.config(state="disabled")
        self.launch_capture_button.config(state="disabled")
        self.ocr_frame.grid_forget()
        self.correction_frame.grid_forget()

        start_time = time.time()
        self.last_recognition_result = self.recognizer.recognize_screen_for_test()
        end_time = time.time()
        detection_time = end_time - start_time

        result = self.last_recognition_result
        method = result['method'].upper() if result['method'] != 'unknown' else 'Desconocido'
        state = result['state'] if result['state'] != 'unknown' else 'N/A'
        confidence = f"{result['confidence']:.3f}" if result['confidence'] is not None else "N/A"
        time_str = f"{detection_time:.3f} seg"

        # Actualizar labels de resultado
        self.method_var.set(method)
        self.state_var.set(state)
        self.confidence_var.set(confidence)
        self.time_var.set(time_str)

        log_data = result.copy()
        log_data['detection_time_s'] = detection_time
        logging.info(f"Resultado Reconocimiento: {log_data}")

        # Limpiar Treeview OCR y campo de edición
        for item in self.ocr_tree.get_children():
            self.ocr_tree.delete(item)
        self.ocr_edit_var.set("")

        status_row = 2 # Fila por defecto para status (debajo de resultados)

        if result['state'] != 'unknown': # Detección OK (Template u OCR)
            self.confirm_button.config(state="normal")
            self.deny_button.config(state="normal")
            if result['method'] == 'ocr':
                self.ocr_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew") # Mostrar frame OCR en fila 2
                status_row = 3 # Status va debajo de OCR
                self.populate_ocr_tree(result['ocr_results']) # Llenar tabla
                self.confirm_ocr_button.config(state="normal")
                self.save_edited_button.config(state="normal")
                self.ocr_edit_entry.config(state="normal")
                self.status_message("Reconocido por OCR. Valida la detección o edita el texto esperado.")
            else: # Método Template
                self.status_message(f"Reconocido por Template. Valida la detección.")
                # status_row se queda en 2
        else: # No reconocido ('unknown')
            self.launch_capture_button.config(state="normal")
            self.correction_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew") # Mostrar corrección en fila 2
            status_row = 3 # Status va debajo de corrección
            self.status_message("Pantalla NO RECONOCIDA. Selecciona la correcta o abre el gestor.")

        # Asegurar posición del status label
        self.status_label.grid(row=status_row, column=0, padx=10, pady=(5, 10), sticky="ew")

    def populate_ocr_tree(self, ocr_results):
        """Llena el Treeview con los resultados detallados del OCR."""
        for item in self.ocr_tree.get_children():
            self.ocr_tree.delete(item)

        if ocr_results:
            for idx, data in ocr_results.items():
                extracted = data['text']
                expected_list = data.get('expected', [])
                expected_str = "|".join(expected_list)
                match_str = "Sí" if data.get('match_expected') else "No"
                self.ocr_tree.insert("", tk.END, values=(idx, extracted, expected_str, match_str))
        else:
            self.ocr_tree.insert("", tk.END, values=("N/A", "No se encontraron resultados OCR.", "", "N/A"))


    def confirm_detection(self):
        """Registra la confirmación del usuario."""
        detected_state = self.state_var.get()
        if detected_state != "N/A":
            logging.info(f"CONFIRMACIÓN USUARIO: Detección de '{detected_state}' es CORRECTA.")
            self.status_message(f"Detección de '{detected_state}' confirmada.")
            self.confirm_button.config(state="disabled")
            self.deny_button.config(state="disabled")
            self.launch_capture_button.config(state="disabled")
            self.correction_frame.grid_forget()
            self.ocr_frame.grid_forget()
            self.status_label.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        else:
            messagebox.showwarning("Advertencia", "No hay detección válida para confirmar.")


    def deny_detection(self):
        """Registra la negación y muestra opciones de corrección/captura."""
        detected_state = self.state_var.get()
        # Permitir negar incluso si fue 'unknown'
        logging.warning(f"NEGACIÓN USUARIO: Detección de '{detected_state}' es INCORRECTA.")
        self.status_message(f"Detección negada. Selecciona estado correcto o abre el gestor.")
        self.confirm_button.config(state="disabled")
        self.deny_button.config(state="disabled")
        # Mostrar frame de corrección y habilitar botón de lanzar gestor
        self.correction_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew") # Fila 2
        self.launch_capture_button.config(state="normal")
        self.ocr_frame.grid_forget()
        self.status_label.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew") # Fila 3
        self._populate_correction_combobox() # Asegurar que el combo esté actualizado


    def log_correct_state(self):
        """Registra el estado que el usuario indica como correcto."""
        correct_state = self.correct_state_var.get()
        last_detected = self.state_var.get() if self.state_var.get() != "N/A" else "unknown"

        if not correct_state:
            messagebox.showwarning("Selección Vacía", "Selecciona el estado correcto del Combobox.")
            return

        logging.info(f"CORRECCIÓN USUARIO: Detección fue '{last_detected}', estado correcto indicado: '{correct_state}'.")
        self.status_message(f"Corrección registrada: '{correct_state}'.")
        # Ocultar frame de corrección después de loggear
        self.correction_frame.grid_forget()
        self.launch_capture_button.config(state="disabled") # Deshabilitar de nuevo
        self.status_label.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew") # Ajustar fila status


    def launch_template_manager(self):
        """Lanza la GUI template_manager_gui.py en un proceso separado."""
        logging.info(f"Intentando lanzar: {TEMPLATE_MANAGER_SCRIPT_PATH}")
        self.status_message("Abriendo Gestor de Plantillas...")
        try:
            process = subprocess.Popen([sys.executable, TEMPLATE_MANAGER_SCRIPT_PATH])
            logging.info(f"Gestor de Plantillas lanzado con PID: {process.pid}")
            self.status_message("Gestor de Plantillas abierto. Recarga datos cuando termines.")
        except FileNotFoundError:
             logging.error(f"Error: No se encontró el script '{TEMPLATE_MANAGER_SCRIPT_PATH}'. Verifica la ruta.")
             messagebox.showerror("Error", f"No se pudo encontrar el script:\n{TEMPLATE_MANAGER_SCRIPT_PATH}")
             self.status_message("Error al abrir el gestor.")
        except Exception as e:
             logging.error(f"Error al lanzar el gestor de plantillas: {e}")
             messagebox.showerror("Error", f"Ocurrió un error al abrir el gestor:\n{e}")
             self.status_message("Error al abrir el gestor.")

    # --- confirm_ocr_text y save_edited_ocr_text (usando la lógica corregida de la respuesta anterior) ---
    def confirm_ocr_text(self):
        """Confirma el texto extraído para la(s) región(es) seleccionada(s)."""
        if not self.last_recognition_result or self.last_recognition_result['method'] != 'ocr' or not self.last_recognition_result['ocr_results']:
            messagebox.showwarning("Advertencia", "No hay resultado OCR válido para confirmar.")
            return

        selected_items = self.ocr_tree.selection()
        if not selected_items:
            if not messagebox.askyesno("Confirmar Todas", "No hay región seleccionada.\n¿Confirmar texto para TODAS las regiones con texto extraído?"): return
            target_indices = [int(self.ocr_tree.item(item, 'values')[0]) for item in self.ocr_tree.get_children() if self.ocr_tree.item(item, 'values')[1]]
        else:
            target_indices = [int(self.ocr_tree.item(item_id, 'values')[0]) for item_id in selected_items if self.ocr_tree.item(item_id, 'values')[1]]

        if not target_indices:
            messagebox.showinfo("Información", "No se seleccionaron regiones con texto extraído válido.")
            return

        state_name = self.last_recognition_result['state']
        ocr_results_map = self.last_recognition_result['ocr_results']
        all_ocr_mappings = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")

        if state_name not in all_ocr_mappings or not isinstance(all_ocr_mappings[state_name], list):
            if state_name not in all_ocr_mappings: all_ocr_mappings[state_name] = []
            else: messagebox.showerror("Error", f"Entrada inválida para '{state_name}'."); return

        updated = False
        for idx in target_indices:
            if idx in ocr_results_map:
                extracted_text = ocr_results_map[idx]['text']
                region_coords = ocr_results_map[idx]['region']
                if extracted_text:
                    try:
                        entry_found = False
                        for i, entry in enumerate(all_ocr_mappings[state_name]):
                            if isinstance(entry, dict) and entry.get('region') == region_coords:
                                if 'expected_text' not in entry or not isinstance(entry['expected_text'], list): entry['expected_text'] = []
                                if extracted_text not in entry['expected_text']:
                                    entry['expected_text'].append(extracted_text)
                                    updated = True
                                    logging.info(f"Confirmando texto '{extracted_text}' para región {i} de '{state_name}'")
                                entry_found = True
                                break
                        if not entry_found:
                             logging.warning(f"No se encontró región exacta {region_coords} para '{state_name}'. Creando nueva entrada.")
                             all_ocr_mappings[state_name].append({'region': region_coords, 'expected_text': [extracted_text]})
                             updated = True
                    except Exception as e: messagebox.showerror("Error", f"Error procesando región {idx}: {e}"); return

        if updated:
            if save_json_mapping(all_ocr_mappings, OCR_MAPPING_FILE, "regiones OCR"):
                self.recognizer.reload_data()
                logging.info(f"Texto(s) esperado(s) guardado(s) para '{state_name}' (confirmación).")
                messagebox.showinfo("Éxito", "Texto(s) esperado(s) guardado(s).")
                self.status_message("Texto esperado confirmado y guardado.")
                self.refresh_ocr_tree_display()
            else: logging.error(f"Falló guardado OCR."); messagebox.showerror("Error", f"Falló al guardar {OCR_MAPPING_FILE}.")
        else: messagebox.showinfo("Información", "Texto ya existía o no había texto nuevo para confirmar."); self.status_message("Sin cambios en texto esperado.")


    def save_edited_ocr_text(self):
        """Guarda el texto editado para la(s) región(es) seleccionada(s)."""
        if not self.last_recognition_result or self.last_recognition_result['method'] != 'ocr': messagebox.showwarning("Advertencia", "."); return
        selected_items = self.ocr_tree.selection()
        if not selected_items: messagebox.showwarning("Selección Vacía", "Selecciona región(es) en la tabla."); return

        state_name = self.last_recognition_result['state']
        edited_text_str = self.ocr_edit_var.get().strip()
        if not edited_text_str: messagebox.showwarning("Entrada Vacía", "Introduce texto esperado."); return
        expected_texts = [text.strip() for text in edited_text_str.split('|') if text.strip()]
        if not expected_texts: messagebox.showwarning("Entrada Vacía", "Introduce texto válido."); return

        all_ocr_mappings = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")
        if state_name not in all_ocr_mappings or not isinstance(all_ocr_mappings[state_name], list):
             if state_name not in all_ocr_mappings: all_ocr_mappings[state_name] = []
             else: messagebox.showerror("Error", f"Entrada inválida para '{state_name}'."); return

        updated = False
        target_regions_coords = []
        indices_in_results = [] # Para saber qué región del resultado original corresponde
        for item_id in selected_items:
             values = self.ocr_tree.item(item_id, 'values')
             if values and values[0] != "N/A" and self.last_recognition_result.get('ocr_results'):
                 idx = int(values[0])
                 if idx in self.last_recognition_result['ocr_results']:
                      target_regions_coords.append(self.last_recognition_result['ocr_results'][idx]['region'])
                      indices_in_results.append(idx)

        if not target_regions_coords: messagebox.showinfo("Información", "."); return

        for i, entry in enumerate(all_ocr_mappings[state_name]):
             if isinstance(entry, dict) and entry.get('region') in target_regions_coords:
                  try:
                       entry['expected_text'] = expected_texts
                       updated = True
                       logging.info(f"Estableciendo texto esperado (editado) {expected_texts} para región {i} de '{state_name}'")
                  except Exception as e: messagebox.showerror("Error", f"Error actualizando región {i}: {e}"); return

        if updated:
            if save_json_mapping(all_ocr_mappings, OCR_MAPPING_FILE, "regiones OCR"):
                self.recognizer.reload_data()
                logging.info(f"Texto(s) esperado(s) editado(s) guardado(s) para '{state_name}'.")
                messagebox.showinfo("Éxito", "Texto(s) esperado(s) editado(s) guardado(s).")
                self.status_message("Texto esperado editado y guardado.")
                self.ocr_edit_var.set("")
                self.refresh_ocr_tree_display()
            else: logging.error(f"Falló guardado OCR editado."); messagebox.showerror("Error", f"Falló al guardar {OCR_MAPPING_FILE}.")
        else: logging.warning(f"No se encontraron regiones para actualizar para '{state_name}'."); messagebox.showinfo("Información", f"No se encontraron regiones coincidentes para actualizar.")


    def refresh_ocr_tree_display(self):
        """Actualiza el Treeview con los datos del último resultado OCR y los datos guardados."""
        if not self.last_recognition_result or self.last_recognition_result['method'] != 'ocr':
            return

        for item in self.ocr_tree.get_children(): self.ocr_tree.delete(item)

        state_name = self.last_recognition_result['state']
        # Cargar mapping actualizado directamente desde el archivo para asegurar frescura
        current_ocr_mappings = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")
        current_regions_data_list = current_ocr_mappings.get(state_name, [])

        if self.last_recognition_result['ocr_results']:
            for idx, data in self.last_recognition_result['ocr_results'].items():
                extracted = data['text']
                region_coords = data['region']
                expected_list = []
                # Buscar en la lista actual del archivo por coordenadas
                for entry in current_regions_data_list:
                     if isinstance(entry, dict) and entry.get('region') == region_coords:
                          expected_list = entry.get('expected_text', [])
                          break
                expected_str = "|".join(expected_list)
                # Recalcular match
                match_expected = False
                if extracted and expected_list:
                    for expected in expected_list:
                        if expected.lower() == extracted.lower(): match_expected = True; break
                match_str = "Sí" if match_expected else "No"
                self.ocr_tree.insert("", tk.END, values=(idx, extracted, expected_str, match_str))
        else:
            self.ocr_tree.insert("", tk.END, values=("N/A", "No se encontraron resultados.", "", "N/A"))


    def status_message(self, message):
        """Actualiza el mensaje en el label de estado."""
        self.status_label_var.set(message)
        self.update_idletasks()

if __name__ == "__main__":
    app = ScreenTesterGUI()
    app.mainloop()