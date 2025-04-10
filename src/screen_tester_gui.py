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
import time # Para medir tiempo
import logging # Para logging
import subprocess # Para lanzar otro script
import sys # Para obtener el ejecutable de python

# --- Importar lo necesario desde screen_recognizer ---
from screen_recognizer import (
    ScreenRecognizer,
    save_json_mapping,
    load_json_mapping,
    OCR_MAPPING_FILE,
    # DEFAULT_FONT_SIZE,
    TEMPLATE_MAPPING_FILE # Necesario para la GUI anterior
)

# --- Constantes ---
DEFAULT_FONT_SIZE = 11 # Importado o definido en screen_recognizer
MIN_WINDOW_WIDTH = 850 # Aumentar un poco el mínimo
MIN_WINDOW_HEIGHT = 700
MIN_CANVAS_WIDTH = 300
MIN_CANVAS_HEIGHT = 200
LOG_FILE = "tester_log.log" # Nombre del archivo de log

# --- Configuración del Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'), # Escribir a archivo
        logging.StreamHandler() # También mostrar en consola
    ]
)

# --- Constantes de rutas ---
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
# Ruta al script de la GUI de gestión de plantillas
TEMPLATE_MANAGER_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "template_manager_gui.py")


class ScreenTesterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tester Interactivo - Screen Recognizer")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.captured_image = None
        self.selected_image_path = None
        self.ocr_regions = []
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
        style.configure("Confirm.TButton", font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE))
        style.configure("Deny.TButton", font=(self.default_font.actual()['family'], DEFAULT_FONT_SIZE))

        self.create_widgets()
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
        self.grid_rowconfigure(1, weight=0) # Fila resultados fija
        self.grid_rowconfigure(2, weight=1) # Fila OCR (si aparece) se expande
        self.grid_columnconfigure(0, weight=1)

        self.create_control_frame()

        # --- Frame de Resultados ---
        result_frame = ttk.LabelFrame(self, text="Resultado del Reconocimiento", padding=(10, 5))
        result_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        result_frame.grid_columnconfigure(1, weight=1) # Columna de valor se expande

        ttk.Label(result_frame, text="Método:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.method_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.method_var, style="Result.TLabel").grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(result_frame, text="Estado Detectado:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.state_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.state_var, style="Result.TLabel").grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(result_frame, text="Confianza (Template):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.confidence_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.confidence_var).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(result_frame, text="Tiempo Detección:").grid(row=3, column=0, padx=5, pady=2, sticky="w") # Label para tiempo
        self.time_var = tk.StringVar(value="N/A")
        ttk.Label(result_frame, textvariable=self.time_var).grid(row=3, column=1, padx=5, pady=2, sticky="w")

        # --- Botones de Confirmación/Negación ---
        validation_frame = ttk.Frame(result_frame)
        validation_frame.grid(row=4, column=0, columnspan=2, pady=5)
        self.confirm_button = ttk.Button(validation_frame, text="Confirmar Detección", style="Confirm.TButton", command=self.confirm_detection, state="disabled")
        self.confirm_button.pack(side="left", padx=10)
        self.deny_button = ttk.Button(validation_frame, text="Negar Detección", style="Deny.TButton", command=self.deny_detection, state="disabled")
        self.deny_button.pack(side="left", padx=10)
        # Botón para lanzar la GUI de captura (inicialmente oculto/deshabilitado)
        self.launch_capture_button = ttk.Button(validation_frame, text="Abrir Gestor Plantillas", command=self.launch_template_manager, state="disabled")
        self.launch_capture_button.pack(side="left", padx=10)

        # --- Frame de Detalles y Edición OCR ---
        self.ocr_frame = ttk.LabelFrame(self, text="Detalles y Edición OCR", padding=(10, 5))
        self.ocr_frame.grid_rowconfigure(1, weight=1)
        self.ocr_frame.grid_columnconfigure(0, weight=1)

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

    def create_control_frame(self):
        control_frame = ttk.LabelFrame(self, text="Control", padding=(10, 5))
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        self.test_button = ttk.Button(control_frame, text="Reconocer Pantalla Actual", command=self.run_test)
        self.test_button.pack(pady=5)

    def create_status_label(self):
        """Crea el label para mensajes de estado."""
        self.status_label_var = tk.StringVar(value="Listo. Inicia el juego y pulsa 'Reconocer Pantalla'.")
        self.status_label = ttk.Label(self, textvariable=self.status_label_var, anchor="w")
        # Posición inicial, se ajustará en run_test
        self.status_label.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")

    def run_test(self):
        """Ejecuta el reconocimiento y actualiza la GUI."""
        self.status_message("Reconociendo pantalla...")
        self.confirm_button.config(state="disabled") # Deshabilitar botones mientras se procesa
        self.deny_button.config(state="disabled")
        self.launch_capture_button.config(state="disabled")
        self.ocr_frame.grid_forget() # Ocultar detalles OCR

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
        self.time_var.set(time_str) # Mostrar tiempo

        log_data = result.copy() # Copiar para log
        log_data['detection_time_s'] = detection_time # Añadir tiempo al log
        logging.info(f"Resultado Reconocimiento: {log_data}") # Loggear el resultado completo

        # Limpiar y mostrar/ocultar frame OCR
        self.ocr_text_display.config(state="normal")
        self.ocr_text_display.delete("1.0", tk.END)
        self.ocr_edit_var.set("")

        status_row = 2 # Fila por defecto para el status label

        if result['state'] != 'unknown': # Si se detectó *algo*
            self.confirm_button.config(state="normal")
            self.deny_button.config(state="normal")

            if result['method'] == 'ocr':
                 self.ocr_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
                 status_row = 3

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
        else: # No reconocido
            self.launch_capture_button.config(state="normal") # Permitir abrir gestor si no se reconoció nada
            self.status_message("Pantalla NO RECONOCIDA. Puedes abrir el gestor de plantillas.")

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
        else:
            messagebox.showwarning("Advertencia", "No hay detección válida para confirmar.")

    def deny_detection(self):
        """Registra la negación y habilita el botón para abrir la otra GUI."""
        detected_state = self.state_var.get()
        if detected_state != "N/A":
            logging.warning(f"NEGACIÓN USUARIO: Detección de '{detected_state}' es INCORRECTA.")
            self.status_message(f"Detección de '{detected_state}' negada. Abre el gestor si es necesario.")
            self.confirm_button.config(state="disabled")
            self.deny_button.config(state="disabled")
            self.launch_capture_button.config(state="normal") # Habilitar botón de lanzar
            self.ocr_frame.grid_forget() # Ocultar detalles OCR si estaban visibles
            self.status_label.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew") # Ajustar fila status
        else:
            messagebox.showwarning("Advertencia", "No hay detección válida para negar.")

    def launch_template_manager(self):
        """Lanza la GUI template_manager_gui.py en un proceso separado."""
        logging.info(f"Intentando lanzar: {TEMPLATE_MANAGER_SCRIPT_PATH}")
        self.status_message("Abriendo Gestor de Plantillas...")
        try:
            # Usar sys.executable para asegurar que usa el mismo intérprete Python
            process = subprocess.Popen([sys.executable, TEMPLATE_MANAGER_SCRIPT_PATH])
            logging.info(f"Gestor de Plantillas lanzado con PID: {process.pid}")
            self.status_message("Gestor de Plantillas abierto en otra ventana.")
            self.launch_capture_button.config(state="disabled") # Deshabilitar después de lanzar
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
                 logging.error(f"Entrada inválida para '{state_name}' en {OCR_MAPPING_FILE}")
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
                        if isinstance(entry, dict) and 'region' in entry and entry['region'] == region_coords:
                            region_entry = entry
                            existing_index = i
                            break

                    if region_entry is None:
                         logging.info(f"Añadiendo nueva región {region_coords} para '{state_name}'")
                         region_entry = {'region': region_coords, 'expected_text': []}
                         all_ocr_mappings[state_name].append(region_entry)
                         existing_index = len(all_ocr_mappings[state_name]) - 1
                    else:
                        if 'expected_text' not in region_entry or not isinstance(region_entry['expected_text'], list):
                            region_entry['expected_text'] = []

                    if extracted_text not in region_entry['expected_text']:
                        region_entry['expected_text'].append(extracted_text)
                        updated = True
                        logging.info(f"Añadiendo texto esperado '{extracted_text}' a la región {existing_index} de '{state_name}'")

                except Exception as e:
                    logging.error(f"Error procesando región {idx} para '{state_name}': {e}")
                    messagebox.showerror("Error", f"Error procesando región {idx} para '{state_name}': {e}")
                    return

        if updated:
            if save_json_mapping(all_ocr_mappings, OCR_MAPPING_FILE, "regiones OCR"):
                self.recognizer._load_all_data()
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
                  logging.error(f"Entrada inválida para '{state_name}' en {OCR_MAPPING_FILE} al intentar guardar texto editado.")
                  return

        updated = False
        if self.last_recognition_result['ocr_results']:
             detected_indices = list(self.last_recognition_result['ocr_results'].keys())

             for idx in range(len(all_ocr_mappings[state_name])):
                  if idx in detected_indices:
                       try:
                           if isinstance(all_ocr_mappings[state_name][idx], dict) and 'region' in all_ocr_mappings[state_name][idx]:
                                all_ocr_mappings[state_name][idx]['expected_text'] = expected_texts
                                updated = True
                                logging.info(f"Estableciendo texto esperado (editado) {expected_texts} para región {idx} de '{state_name}'")
                           else:
                               logging.warning(f"Saltando índice {idx} para '{state_name}' debido a formato inesperado al editar texto OCR.")
                       except Exception as e:
                            logging.error(f"Error actualizando región {idx} para '{state_name}' al guardar texto editado: {e}")
                            messagebox.showerror("Error", f"Error actualizando región {idx} para '{state_name}': {e}")
                            return

        if updated:
            if save_json_mapping(all_ocr_mappings, OCR_MAPPING_FILE, "regiones OCR"):
                self.recognizer._load_all_data()
                logging.info(f"Texto(s) esperado(s) editado(s) guardado(s) para '{state_name}'.")
                messagebox.showinfo("Éxito", f"Texto(s) esperado(s) editado(s) guardado(s) para las regiones detectadas de '{state_name}'.")
                self.status_message("Texto esperado editado y guardado.")
                self.ocr_edit_var.set("")
            else:
                 logging.error(f"Falló al guardar {OCR_MAPPING_FILE} al guardar texto OCR editado.")
                 messagebox.showerror("Error", f"Falló al guardar {OCR_MAPPING_FILE}.")
        else:
             logging.warning(f"No se encontraron regiones válidas (detectadas en el último test) para actualizar para '{state_name}' al guardar texto editado.")
             messagebox.showinfo("Información", f"No se encontraron regiones válidas (detectadas en el último test) para actualizar para '{state_name}'.")


    def status_message(self, message):
        """Actualiza el mensaje en el label de estado."""
        self.status_label_var.set(message)
        self.update_idletasks()

if __name__ == "__main__":
    app = ScreenTesterGUI()
    app.mainloop()