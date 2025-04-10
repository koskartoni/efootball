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

# --- Importar lo necesario desde screen_recognizer ---
from screen_recognizer import (
    ScreenRecognizer,
    save_json_mapping,
    load_json_mapping,
    OCR_MAPPING_FILE,
    TEMPLATE_MAPPING_FILE, # Necesario para recargar
    #DEFAULT_FONT_SIZE,
    PROJECT_DIR, # Importar PROJECT_DIR si está definido globalmente
    IMAGES_DIR   # Importar IMAGES_DIR si está definido globalmente
)

# --- Definir constantes locales ---
DEFAULT_FONT_SIZE = 11 # Comentado si se importa
MIN_WINDOW_WIDTH = 850
MIN_WINDOW_HEIGHT = 750 # Un poco más de alto para la nueva sección
MIN_CANVAS_WIDTH = 300
MIN_CANVAS_HEIGHT = 200
LOG_FILE = "tester_log.log"

# --- Configuración del Logging ---
# (Misma configuración que antes)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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

        self.captured_image = None # El tester no captura directamente
        self.selected_image_path = None
        self.ocr_regions = [] # Regiones del estado actualmente mostrado/validado
        self.ocr_region_rects = []
        self.current_template_name = None

        self.recognizer = ScreenRecognizer(monitor=1, threshold=0.75, ocr_fallback_threshold=0.65)
        self.monitors_info = self.recognizer.monitors_info if hasattr(self.recognizer, 'monitors_info') else self.detect_monitors()

        self.last_recognition_result = None

        # --- Configuración de fuente ---
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=DEFAULT_FONT_SIZE)
        style = ttk.Style(self)
        style.configure('.', font=self.default_font)
        style.configure('TLabelframe.Label', font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE, 'bold'))
        style.configure("Result.TLabel", font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE + 2, 'bold'))
        style.configure("Confirm.TButton", font=self.default_font)
        style.configure("Deny.TButton", font=self.default_font)

        self.create_widgets()
        self.recognizer._load_all_data() # Cargar datos iniciales en el recognizer

        logging.info("Tester GUI inicializado.")

    def detect_monitors(self):
        """Detecta los monitores existentes usando mss (fallback)."""
        try:
            with mss.mss() as sct:
                monitors = [m for i, m in enumerate(sct.monitors) if i > 0]
                return monitors
        except Exception as e:
            logging.error(f"Error detectando monitores: {e}")
            return []

    def create_widgets(self):
        self.grid_rowconfigure(2, weight=0) # Fila corrección fija
        self.grid_rowconfigure(3, weight=1) # Fila OCR (si aparece) se expande
        self.grid_columnconfigure(0, weight=1)

        self.create_control_frame()

        # --- Frame de Resultados ---
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

        # --- Botones de Confirmación/Negación ---
        validation_frame = ttk.Frame(result_frame)
        validation_frame.grid(row=4, column=0, columnspan=2, pady=5)
        self.confirm_button = ttk.Button(validation_frame, text="👍 Confirmar Detección", style="Confirm.TButton", command=self.confirm_detection, state="disabled")
        self.confirm_button.pack(side="left", padx=10)
        self.deny_button = ttk.Button(validation_frame, text="👎 Negar Detección", style="Deny.TButton", command=self.deny_detection, state="disabled")
        self.deny_button.pack(side="left", padx=10)
        self.launch_capture_button = ttk.Button(validation_frame, text="Abrir Gestor Plantillas", command=self.launch_template_manager, state="disabled")
        self.launch_capture_button.pack(side="left", padx=10)


        # --- Frame de Corrección Manual (se muestra al negar) ---
        self.correction_frame = ttk.LabelFrame(self, text="Corrección Manual", padding=(10, 5))
        # No usar grid aquí inicialmente
        self.correction_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.correction_frame, text="Estado Correcto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.correct_state_var = tk.StringVar()
        self.correct_state_combo = ttk.Combobox(self.correction_frame, textvariable=self.correct_state_var, width=35)
        self.correct_state_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        # Llenar el combobox de corrección (se hará después de crear widgets)
        self._populate_correction_combobox()

        self.log_correction_button = ttk.Button(self.correction_frame, text="Registrar Corrección", command=self.log_correct_state)
        self.log_correction_button.grid(row=0, column=2, padx=10, pady=5)


        # --- Frame de Detalles y Edición OCR (se muestra/oculta) ---
        self.ocr_frame = ttk.LabelFrame(self, text="Detalles y Edición OCR", padding=(10, 5))
        self.ocr_frame.grid_rowconfigure(1, weight=1)
        self.ocr_frame.grid_columnconfigure(0, weight=1)
        # Widgets internos (Text, Entry, Botones) - Sin cambios en la creación

        ttk.Label(self.ocr_frame, text="Texto Extraído por Región:").grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        self.ocr_text_display = tk.Text(self.ocr_frame, height=6, width=60, wrap="word", state="disabled", font=self.default_font)
        self.ocr_text_display.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        ocr_scrollbar = ttk.Scrollbar(self.ocr_frame, orient="vertical", command=self.ocr_text_display.yview)
        ocr_scrollbar.grid(row=1, column=2, sticky="ns")
        self.ocr_text_display['yscrollcommand'] = ocr_scrollbar.set

        ttk.Label(self.ocr_frame, text="Texto Correcto Esperado (separar con '|' si hay varios):").grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        self.ocr_edit_var = tk.StringVar()
        self.ocr_edit_entry = ttk.Entry(self.ocr_frame, textvariable=self.ocr_edit_var, width=60)
        self.ocr_edit_entry.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        ocr_button_frame = ttk.Frame(self.ocr_frame)
        ocr_button_frame.grid(row=4, column=0, columnspan=2, pady=5)
        self.confirm_ocr_button = ttk.Button(ocr_button_frame, text="Confirmar Texto Extraído", command=self.confirm_ocr_text)
        self.confirm_ocr_button.pack(side="left", padx=10)
        self.save_edited_button = ttk.Button(ocr_button_frame, text="Guardar Texto Editado", command=self.save_edited_ocr_text)
        self.save_edited_button.pack(side="left", padx=10)


        self.create_status_label()

    def _populate_correction_combobox(self):
        """Llena el combobox de corrección con los nombres ordenados."""
        try:
             # Cargar nombres directamente desde el archivo para asegurar frescura
            mapping = load_json_mapping(TEMPLATE_MAPPING_FILE, "plantillas")
            template_names = sorted(list(mapping.keys()))
            self.correct_state_combo['values'] = template_names
        except Exception as e:
            logging.error(f"Error al poblar combobox de corrección: {e}")
            self.correct_state_combo['values'] = []


    def create_control_frame(self):
        control_frame = ttk.LabelFrame(self, text="Control", padding=(10, 5))
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1) # Dos columnas para botones

        self.test_button = ttk.Button(control_frame, text="Reconocer Pantalla Actual", command=self.run_test)
        self.test_button.grid(row=0, column=0, pady=5, padx=5, sticky="e") # Alinear a la derecha

        self.reload_button = ttk.Button(control_frame, text="Recargar Datos Reconocedor", command=self.reload_recognizer_data)
        self.reload_button.grid(row=0, column=1, pady=5, padx=5, sticky="w") # Alinear a la izquierda


    def reload_recognizer_data(self):
        """Llama al método de recarga del reconocedor."""
        self.status_message("Recargando datos del reconocedor...")
        try:
            self.recognizer.reload_data() # Llamar al método añadido en ScreenRecognizer
            self._populate_correction_combobox() # Actualizar combobox de corrección
            self.status_message("Datos del reconocedor recargados.")
            logging.info("Datos del reconocedor recargados manualmente.")
        except AttributeError:
             messagebox.showerror("Error", "La clase ScreenRecognizer no tiene el método 'reload_data'.")
             logging.error("Intento de recarga fallido: método reload_data() no encontrado.")
        except Exception as e:
             messagebox.showerror("Error", f"Error al recargar datos: {e}")
             logging.error(f"Error al recargar datos: {e}")


    def create_status_label(self):
        """Crea el label para mensajes de estado."""
        self.status_label_var = tk.StringVar(value="Listo. Inicia el juego y pulsa 'Reconocer Pantalla'.")
        self.status_label = ttk.Label(self, textvariable=self.status_label_var, anchor="w")
        self.status_label.grid(row=4, column=0, padx=10, pady=(5, 10), sticky="ew") # Fila 4 inicial

    def run_test(self):
        """Ejecuta el reconocimiento y actualiza la GUI."""
        self.status_message("Reconociendo pantalla...")
        self.confirm_button.config(state="disabled")
        self.deny_button.config(state="disabled")
        self.launch_capture_button.config(state="disabled")
        self.ocr_frame.grid_forget()
        self.correction_frame.grid_forget() # Ocultar corrección al inicio del test

        start_time = time.time()
        self.last_recognition_result = self.recognizer.recognize_screen_for_test()
        end_time = time.time()
        detection_time = end_time - start_time

        result = self.last_recognition_result

        method = result['method'].upper() if result['method'] != 'unknown' else 'Desconocido'
        state = result['state'] if result['state'] != 'unknown' else 'N/A'
        confidence = f"{result['confidence']:.3f}" if result['confidence'] is not None else "N/A"
        time_str = f"{detection_time:.3f} seg"

        self.method_var.set(method)
        self.state_var.set(state)
        self.confidence_var.set(confidence)
        self.time_var.set(time_str)

        log_data = result.copy()
        log_data['detection_time_s'] = detection_time
        logging.info(f"Resultado Reconocimiento: {log_data}")

        self.ocr_text_display.config(state="normal")
        self.ocr_text_display.delete("1.0", tk.END)
        self.ocr_edit_var.set("")

        status_row = 3 # Fila por defecto para status (debajo de corrección y ocr)

        if result['state'] != 'unknown':
            self.confirm_button.config(state="normal")
            self.deny_button.config(state="normal")

            if result['method'] == 'ocr':
                 self.ocr_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew") # Mostrar frame OCR en fila 3
                 status_row = 4 # Status va en fila 4

                 ocr_display_text = ""
                 if result['ocr_results']:
                     for idx, data in result['ocr_results'].items():
                         ocr_display_text += f"Región {idx}: '{data['text']}'\n"
                     self.ocr_text_display.insert(tk.END, ocr_display_text)
                 else:
                     self.ocr_text_display.insert(tk.END, "No se encontraron resultados OCR específicos.")
                 self.ocr_text_display.config(state="disabled")
                 self.confirm_ocr_button.config(state="normal")
                 self.save_edited_button.config(state="normal")
                 self.ocr_edit_entry.config(state="normal")
                 self.status_message("Reconocido por OCR. Valida la detección o edita el texto esperado.")
            else: # Método Template
                self.status_message(f"Reconocido por Template. Valida la detección.")
                # OCR frame ya está oculto
                status_row = 2 # Status justo debajo de resultados si no hay OCR
        else: # No reconocido
            self.launch_capture_button.config(state="normal")
            self.correction_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew") # Mostrar corrección
            status_row = 3 # Status debajo de corrección
            self.status_message("Pantalla NO RECONOCIDA. Selecciona la correcta o abre el gestor.")

        self.status_label.grid(row=status_row, column=0, padx=10, pady=(5, 10), sticky="ew")


    def confirm_detection(self):
        """Registra la confirmación del usuario."""
        detected_state = self.state_var.get()
        if detected_state != "N/A":
            logging.info(f"CONFIRMACIÓN USUARIO: Detección de '{detected_state}' es CORRECTA.")
            self.status_message(f"Detección de '{detected_state}' confirmada.")
            self.confirm_button.config(state="disabled")
            self.deny_button.config(state="disabled")
            self.launch_capture_button.config(state="disabled")
            self.correction_frame.grid_forget() # Ocultar si estaba visible
        else:
            messagebox.showwarning("Advertencia", "No hay detección válida para confirmar.")

    def deny_detection(self):
        """Registra la negación y muestra opciones de corrección/captura."""
        detected_state = self.state_var.get()
        if detected_state != "N/A" or self.last_recognition_result['method'] == 'unknown': # Permitir negar incluso si fue 'unknown'
            logging.warning(f"NEGACIÓN USUARIO: Detección de '{detected_state}' es INCORRECTA.")
            self.status_message(f"Detección negada. Selecciona estado correcto o abre el gestor.")
            self.confirm_button.config(state="disabled")
            self.deny_button.config(state="disabled")
            # Mostrar frame de corrección y habilitar botón de lanzar gestor
            self.correction_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
            self.launch_capture_button.config(state="normal")
            self.ocr_frame.grid_forget()
            self.status_label.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew") # Ajustar fila status
            self._populate_correction_combobox() # Asegurar que el combo esté actualizado
        else:
            messagebox.showwarning("Advertencia", "No hay detección válida para negar.")

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
        self.status_label.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew") # Ajustar fila status


    def launch_template_manager(self):
        """Lanza la GUI template_manager_gui.py en un proceso separado."""
        logging.info(f"Intentando lanzar: {TEMPLATE_MANAGER_SCRIPT_PATH}")
        self.status_message("Abriendo Gestor de Plantillas...")
        try:
            process = subprocess.Popen([sys.executable, TEMPLATE_MANAGER_SCRIPT_PATH])
            logging.info(f"Gestor de Plantillas lanzado con PID: {process.pid}")
            self.status_message("Gestor de Plantillas abierto. Recarga datos cuando termines.")
            # No deshabilitar, permitir abrir múltiples veces si es necesario
            # self.launch_capture_button.config(state="disabled")
        except FileNotFoundError:
             logging.error(f"Error: No se encontró el script '{TEMPLATE_MANAGER_SCRIPT_PATH}'. Verifica la ruta.")
             messagebox.showerror("Error", f"No se pudo encontrar el script:\n{TEMPLATE_MANAGER_SCRIPT_PATH}")
             self.status_message("Error al abrir el gestor.")
        except Exception as e:
             logging.error(f"Error al lanzar el gestor de plantillas: {e}")
             messagebox.showerror("Error", f"Ocurrió un error al abrir el gestor:\n{e}")
             self.status_message("Error al abrir el gestor.")


    def confirm_ocr_text(self):
        """Confirma que el texto extraído por OCR es correcto y lo guarda como esperado."""
        # (Sin cambios en la lógica interna, sigue usando load_json_mapping y save_json_mapping)
        if not self.last_recognition_result or self.last_recognition_result['method'] != 'ocr':
            messagebox.showwarning("Advertencia", "No hay resultado OCR válido para confirmar.")
            return
        if not self.last_recognition_result['ocr_results']:
            messagebox.showinfo("Información", "No hay texto OCR específico extraído para guardar.")
            return

        state_name = self.last_recognition_result['state']
        ocr_results = self.last_recognition_result['ocr_results']

        all_ocr_mappings = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")

        if state_name not in all_ocr_mappings or not isinstance(all_ocr_mappings[state_name], list):
            if state_name not in all_ocr_mappings:
                 logging.info(f"Creando nueva entrada para '{state_name}' en el mapping OCR.")
                 all_ocr_mappings[state_name] = []
            else:
                 messagebox.showerror("Error", f"La entrada para '{state_name}' en el archivo OCR no es una lista válida.")
                 logging.error(f"Entrada inválida para '{state_name}' en {OCR_MAPPING_FILE} al confirmar texto.")
                 return

        updated = False
        for idx, data in ocr_results.items():
            extracted_text = data['text']
            region_coords = data['region']

            if extracted_text:
                try:
                    region_entry = None
                    existing_index = -1
                    for i, entry in enumerate(all_ocr_mappings[state_name]):
                        # Buscar por coordenadas de región
                        if isinstance(entry, dict) and 'region' in entry and entry['region'] == region_coords:
                            region_entry = entry
                            existing_index = i
                            break

                    if region_entry is None:
                         logging.warning(f"No se encontró la región exacta {region_coords} para '{state_name}' al confirmar texto. Creando nueva entrada de región.")
                         region_entry = {'region': region_coords, 'expected_text': []}
                         all_ocr_mappings[state_name].append(region_entry)
                         existing_index = len(all_ocr_mappings[state_name]) - 1

                    if 'expected_text' not in region_entry or not isinstance(region_entry['expected_text'], list):
                        region_entry['expected_text'] = []

                    if extracted_text not in region_entry['expected_text']:
                        region_entry['expected_text'].append(extracted_text)
                        updated = True
                        logging.info(f"Confirmando texto esperado '{extracted_text}' para la región {existing_index} de '{state_name}'")

                except Exception as e:
                    logging.error(f"Error procesando región {idx} para '{state_name}' al confirmar: {e}")
                    messagebox.showerror("Error", f"Error procesando región {idx} para '{state_name}': {e}")
                    return

        if updated:
            if save_json_mapping(all_ocr_mappings, OCR_MAPPING_FILE, "regiones OCR"):
                self.recognizer.reload_data() # Recargar datos en el recognizer
                logging.info(f"Texto(s) esperado(s) guardado(s) para '{state_name}' vía confirmación.")
                messagebox.showinfo("Éxito", f"Texto(s) esperado(s) guardado(s) para las regiones de '{state_name}'.")
                self.status_message("Texto esperado confirmado y guardado.")
            else:
                 logging.error(f"Falló al guardar {OCR_MAPPING_FILE} durante confirmación OCR.")
                 messagebox.showerror("Error", f"Falló al guardar {OCR_MAPPING_FILE}.")
        else:
            logging.info(f"Confirmación OCR para '{state_name}': No se añadió nuevo texto esperado.")
            messagebox.showinfo("Información", "El texto extraído ya estaba presente como texto esperado o no se extrajo texto significativo.")
            self.status_message("No se realizaron cambios en el texto esperado.")


    def save_edited_ocr_text(self):
        """Guarda el texto editado manualmente como el texto esperado para las regiones."""
        # (Sin cambios en la lógica interna, sigue usando load_json_mapping y save_json_mapping)
        if not self.last_recognition_result or self.last_recognition_result['method'] != 'ocr':
            messagebox.showwarning("Advertencia", "No hay resultado OCR válido asociado.")
            return
        if not self.last_recognition_result['ocr_results']:
             messagebox.showinfo("Información", "No hay resultados OCR específicos a los que asociar el texto editado.")
             return

        state_name = self.last_recognition_result['state']
        edited_text_str = self.ocr_edit_var.get().strip()

        if not edited_text_str:
            messagebox.showwarning("Entrada Vacía", "Introduce el texto correcto esperado en el campo de edición.")
            return

        expected_texts = [text.strip() for text in edited_text_str.split('|') if text.strip()]
        if not expected_texts:
             messagebox.showwarning("Entrada Vacía", "Introduce al menos un texto válido esperado.")
             return

        all_ocr_mappings = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")

        if state_name not in all_ocr_mappings or not isinstance(all_ocr_mappings[state_name], list):
             if state_name not in all_ocr_mappings:
                  logging.info(f"Creando nueva entrada para '{state_name}' en el mapping OCR para guardar texto editado.")
                  all_ocr_mappings[state_name] = []
             else:
                  messagebox.showerror("Error", f"La entrada para '{state_name}' en el archivo OCR no es una lista válida.")
                  logging.error(f"Entrada inválida para '{state_name}' en {OCR_MAPPING_FILE} al guardar texto editado.")
                  return

        updated = False
        if self.last_recognition_result['ocr_results']:
             detected_indices = list(self.last_recognition_result['ocr_results'].keys())
             detected_regions_coords = [res['region'] for res in self.last_recognition_result['ocr_results'].values()]

             for i, entry in enumerate(all_ocr_mappings[state_name]):
                  # Actualizar solo si la región coincide con una de las detectadas
                  if isinstance(entry, dict) and 'region' in entry and entry['region'] in detected_regions_coords:
                       try:
                            entry['expected_text'] = expected_texts # Sobreescribir/Crear
                            updated = True
                            logging.info(f"Estableciendo texto esperado (editado) {expected_texts} para región {i} de '{state_name}'")
                       except Exception as e:
                            logging.error(f"Error actualizando región {i} para '{state_name}' al guardar texto editado: {e}")
                            messagebox.showerror("Error", f"Error actualizando región {i} para '{state_name}': {e}")
                            return

        if updated:
            if save_json_mapping(all_ocr_mappings, OCR_MAPPING_FILE, "regiones OCR"):
                self.recognizer.reload_data() # Recargar
                logging.info(f"Texto(s) esperado(s) editado(s) guardado(s) para '{state_name}'.")
                messagebox.showinfo("Éxito", f"Texto(s) esperado(s) editado(s) guardado(s) para las regiones detectadas de '{state_name}'.")
                self.status_message("Texto esperado editado y guardado.")
                self.ocr_edit_var.set("")
            else:
                 logging.error(f"Falló al guardar {OCR_MAPPING_FILE} al guardar texto OCR editado.")
                 messagebox.showerror("Error", f"Falló al guardar {OCR_MAPPING_FILE}.")
        else:
             logging.warning(f"No se encontraron regiones coincidentes (detectadas en el último test) para actualizar para '{state_name}' al guardar texto editado.")
             messagebox.showinfo("Información", f"No se encontraron regiones coincidentes (detectadas en el último test) para actualizar para '{state_name}'.")


    def status_message(self, message):
        """Actualiza el mensaje en el label de estado."""
        self.status_label_var.set(message)
        self.update_idletasks()


if __name__ == "__main__":
    app = ScreenTesterGUI()
    app.mainloop()