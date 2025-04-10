import os
import json
import re # Para limpiar texto OCR
import tkinter as tk # Solo para messagebox (considerar logging en su lugar)
from tkinter import messagebox
import cv2
import numpy as np
import mss
import pytesseract
from enum import Enum

# --- Constantes ---
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
TEMPLATE_MAPPING_FILE = os.path.join(CONFIG_DIR, "templates_mapping.json")
OCR_MAPPING_FILE = os.path.join(CONFIG_DIR, "ocr_regions.json")
# Umbral por defecto para la coincidencia de plantillas
DEFAULT_TEMPLATE_THRESHOLD = 0.75 # Puedes ajustar este valor
# Umbral mínimo para considerar una coincidencia parcial (para dirigir OCR)
OCR_FALLBACK_THRESHOLD = 0.6 # Ajusta según sea necesario
# Longitud mínima de texto OCR significativo (después de limpiar)
MIN_OCR_TEXT_LEN = 3

# --- Funciones de Carga de Mappings (con mejor manejo de errores) ---
def load_json_mapping(file_path, file_desc="mapping"):
    """Carga un mapping JSON desde un archivo con manejo de errores."""
    if not os.path.exists(file_path):
        print(f"Advertencia: Archivo de {file_desc} '{file_path}' no encontrado. Usando diccionario vacío.")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            if not isinstance(mapping, dict):
                print(f"Error: El contenido de {file_path} no es un diccionario JSON válido.")
                return {}
            return mapping
    except json.JSONDecodeError:
        print(f"Error: El archivo {file_path} está malformado o vacío.")
        # Considerar messagebox si la GUI depende críticamente de esto
        # messagebox.showerror("Error de Configuración", f"Error al leer {file_path}. Revise el archivo.")
        return {}
    except Exception as e:
        print(f"Error inesperado al cargar {file_path}: {e}")
        return {}

# --- ScreenRecognizer Class ---
class ScreenRecognizer:
    def __init__(self, monitor=1, threshold=DEFAULT_TEMPLATE_THRESHOLD, ocr_fallback_threshold=OCR_FALLBACK_THRESHOLD):
        """
        Inicializa el reconocedor de pantalla.

        Args:
            monitor (int): Índice del monitor a capturar (1-indexado por mss, corregido internamente).
            threshold (float): Umbral principal para template matching.
            ocr_fallback_threshold (float): Umbral mínimo para considerar OCR fallback.
        """
        self.monitor_index = monitor # mss usa 1 para primario, etc.
        self.threshold = threshold
        self.ocr_fallback_threshold = ocr_fallback_threshold
        self.templates = {}  # Diccionario: estado -> lista de imágenes (en escala de grises)
        self.template_names_mapping = {} # Guardar el mapping nombre -> [archivos]
        self.ocr_regions_mapping = {} # Guardar el mapping nombre -> [regiones]
        self._load_all_data() # Cargar todo al inicio

    def _get_monitor_region(self):
        """Obtiene la geometría del monitor seleccionado."""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                # mss.monitors[0] es 'all screens', los reales empiezan en 1
                if self.monitor_index >= 1 and self.monitor_index < len(monitors):
                    return monitors[self.monitor_index]
                else:
                    print(f"Error: Monitor {self.monitor_index} no válido. Usando monitor primario (1).")
                    if len(monitors) > 1:
                         return monitors[1]
                    else: # Fallback si solo existe el monitor 'all'
                         print("Error: No se encontraron monitores válidos.")
                         return None
        except Exception as e:
            print(f"Error obteniendo información del monitor: {e}")
            return None

    def _load_all_data(self):
        """Carga los mappings de plantillas y OCR."""
        print("Cargando datos de reconocimiento...")
        self.template_names_mapping = load_json_mapping(TEMPLATE_MAPPING_FILE, "plantillas")
        self.ocr_regions_mapping = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")
        self._load_templates()
        print("Datos cargados.")

    def _load_templates(self):
        """Carga las imágenes de plantilla en escala de grises."""
        self.templates = {} # Limpiar antes de recargar
        loaded_count = 0
        error_count = 0
        for state, file_list in self.template_names_mapping.items():
            if not isinstance(file_list, list):
                 print(f"Advertencia: Valor para '{state}' en {TEMPLATE_MAPPING_FILE} no es una lista. Saltando.")
                 error_count += 1
                 continue

            loaded_images = []
            for file_name in file_list:
                template_path = os.path.join(IMAGES_DIR, file_name)
                if os.path.exists(template_path):
                    img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        loaded_images.append(img)
                        loaded_count += 1
                    else:
                        print(f"Error: No se pudo cargar la imagen (posiblemente corrupta): {template_path}")
                        error_count += 1
                else:
                    print(f"Advertencia: No se encontró la plantilla listada: {template_path}")
                    error_count += 1 # Contar como error si está listada pero no existe

            if loaded_images:
                self.templates[state] = loaded_images
            # No imprimir si no se cargaron, ya se imprimieron advertencias/errores

        print(f"Carga de plantillas completada. Cargadas: {loaded_count}, Errores/Faltantes: {error_count}")


    def capture_screen(self, region=None):
        """
        Captura la pantalla o una región específica del monitor configurado.

        Args:
            region (dict o None): Coordenadas específicas a capturar. Si es None, usa el monitor completo.

        Returns:
            Imagen capturada (numpy array en formato BGR) o None si falla.
        """
        monitor_region = self._get_monitor_region()
        if monitor_region is None: return None # No se pudo obtener info del monitor

        capture_area = region if region is not None else monitor_region

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(capture_area)
                img = np.array(sct_img)
                # Convertir BGRA a BGR (mss captura 4 canales)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img_bgr
        except Exception as e:
            print(f"Error durante la captura de pantalla: {e}")
            # messagebox.showerror("Error de Captura", f"No se pudo capturar la pantalla: {e}")
            return None


    def find_template_on_screen(self, screen_gray, template_gray):
        """Busca una única plantilla en la pantalla."""
        # Asegurar que la plantilla no sea más grande que la pantalla
        if template_gray.shape[0] > screen_gray.shape[0] or template_gray.shape[1] > screen_gray.shape[1]:
            # print(f"Advertencia: Plantilla es más grande que la pantalla. Saltando.")
            return None, 0.0

        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_loc, max_val # Devolver loc y val


    def recognize_screen(self):
        """
        Intenta reconocer la pantalla actual. Primero usa matching visual.
        Si no hay una coincidencia clara, intenta OCR en regiones definidas para
        estados que tuvieron coincidencias parciales.

        Returns:
            El nombre del estado detectado (str) o "unknown".
        """
        screen_bgr = self.capture_screen()
        if screen_bgr is None:
            print("Error: No se pudo capturar la pantalla para reconocimiento.")
            return "unknown"
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        # --- 1. Template Matching ---
        best_match_state = "unknown"
        best_match_val = 0.0
        potential_ocr_states = [] # Estados con coincidencia parcial para probar OCR

        for state, template_list in self.templates.items():
            state_best_val = 0.0 # Mejor valor para este estado específico
            for template_gray in template_list:
                loc, match_val = self.find_template_on_screen(screen_gray, template_gray)
                state_best_val = max(state_best_val, match_val)

            if state_best_val >= self.threshold:
                if state_best_val > best_match_val: # Encontrar la mejor coincidencia general por encima del umbral
                    best_match_val = state_best_val
                    best_match_state = state
            elif state_best_val >= self.ocr_fallback_threshold:
                # Si está por encima del umbral de fallback pero debajo del principal,
                # es candidato para OCR. Guardar con su puntuación.
                potential_ocr_states.append((state, state_best_val))

        # Si encontramos una coincidencia clara con templates, la retornamos
        if best_match_state != "unknown":
            print(f"Estado detectado (Template): {best_match_state} (Confianza: {best_match_val:.3f})")
            return best_match_state

        # --- 2. OCR Fallback (Solo si no hubo match claro) ---
        print("No se encontró coincidencia clara de plantilla. Intentando OCR fallback...")
        # Ordenar candidatos OCR por puntuación descendente
        potential_ocr_states.sort(key=lambda item: item[1], reverse=True)

        for state_candidate, match_score in potential_ocr_states:
            if state_candidate in self.ocr_regions_mapping:
                regions_for_state = self.ocr_regions_mapping[state_candidate]
                if isinstance(regions_for_state, list): # Verificar si es una lista de regiones
                    all_text_found = ""
                    print(f"  Probando OCR para candidato: {state_candidate} (Score: {match_score:.3f}) con {len(regions_for_state)} regiones...")
                    for region_data in regions_for_state:
                        if isinstance(region_data, dict) and all(k in region_data for k in ('left', 'top', 'width', 'height')):
                            region_coords = region_data
                            # Capturar la región específica (más eficiente que capturar toda la pantalla de nuevo)
                            region_img = self.capture_screen(region=region_coords)
                            if region_img is not None:
                                text = self._extract_and_clean_text(region_img)
                                if text:
                                    print(f"    Texto en región {region_coords}: '{text}'")
                                    all_text_found += text + " " # Acumular texto de todas las regiones
                        else:
                             print(f"Advertencia: Formato de región inválido para '{state_candidate}': {region_data}")

                    # Aquí podrías añadir lógica más compleja para validar 'all_text_found'
                    # Por ahora, si encontramos *algo* significativo en *alguna* región de este estado candidato, lo aceptamos.
                    cleaned_total_text = all_text_found.strip()
                    if len(cleaned_total_text) >= MIN_OCR_TEXT_LEN:
                        print(f"Estado detectado (OCR Fallback): {state_candidate} (Texto relevante encontrado)")
                        return state_candidate
                else:
                    print(f"Advertencia: Las regiones OCR para '{state_candidate}' en {OCR_MAPPING_FILE} no son una lista.")


        print("No se pudo detectar el estado mediante OCR fallback.")
        return "unknown"


    def _extract_and_clean_text(self, image_bgr):
        """Extrae texto de una imagen y lo limpia."""
        if image_bgr is None: return ""
        try:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            # Preprocesamiento opcional para mejorar OCR (ej. umbralización)
            # _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # text = pytesseract.image_to_string(thresh, lang="eng+spa") # Añadir español si es necesario
            text = pytesseract.image_to_string(gray, lang="spa+eng") # Probar con español e inglés
            # Limpiar texto: quitar saltos de línea, espacios extra, caracteres no deseados
            text = text.replace('\n', ' ').replace('\r', '')
            text = re.sub(r'[^a-zA-Z0-9ñÑáéíóúÁÉÍÓÚ\s]', '', text) # Permitir letras con tilde y ñ
            text = re.sub(r'\s+', ' ', text).strip() # Reemplazar múltiples espacios por uno
            return text
        except Exception as e:
            print(f"Error durante OCR: {e}")
            return ""

# --- Dentro de la clase ScreenRecognizer en screen_recognizer.py ---

    def recognize_screen_for_test(self):
        """
        Intenta reconocer la pantalla actual y devuelve información detallada para testeo.

        Returns:
            dict: Un diccionario con:
                'method': 'template' o 'ocr' o 'unknown'
                'state': El nombre del estado detectado (str) o "unknown"
                'confidence': El valor de confianza del matching (float) si method='template', o None si OCR/unknown.
                'ocr_results': Un diccionario {index: {'region': dict, 'text': str}} si method='ocr',
                               o None si template/unknown. El índice corresponde a la lista de regiones en ocr_regions.json.
        """
        result = {
            'method': 'unknown',
            'state': 'unknown',
            'confidence': None,
            'ocr_results': None
        }
        screen_bgr = self.capture_screen()
        if screen_bgr is None:
            print("Error: No se pudo capturar la pantalla para reconocimiento.")
            return result
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        # --- 1. Template Matching ---
        best_match_state = "unknown"
        best_match_val = 0.0
        potential_ocr_states = []

        for state, template_list in self.templates.items():
            state_best_val = 0.0
            for template_gray in template_list:
                loc, match_val = self.find_template_on_screen(screen_gray, template_gray)
                state_best_val = max(state_best_val, match_val)

            if state_best_val >= self.threshold:
                if state_best_val > best_match_val:
                    best_match_val = state_best_val
                    best_match_state = state
            elif state_best_val >= self.ocr_fallback_threshold:
                potential_ocr_states.append((state, state_best_val))

        if best_match_state != "unknown":
            result['method'] = 'template'
            result['state'] = best_match_state
            result['confidence'] = best_match_val
            print(f"Estado detectado (Template): {result['state']} (Confianza: {result['confidence']:.3f})")
            return result

        # --- 2. OCR Fallback ---
        print("No se encontró coincidencia clara de plantilla. Intentando OCR fallback...")
        potential_ocr_states.sort(key=lambda item: item[1], reverse=True)

        for state_candidate, match_score in potential_ocr_states:
            if state_candidate in self.ocr_regions_mapping:
                regions_for_state = self.ocr_regions_mapping[state_candidate]
                if isinstance(regions_for_state, list):
                    ocr_texts_for_state = {}
                    text_found_in_state = False
                    print(f"  Probando OCR para candidato: {state_candidate} (Score: {match_score:.3f}) con {len(regions_for_state)} regiones...")
                    for idx, region_data in enumerate(regions_for_state):
                        if isinstance(region_data, dict) and all(k in region_data for k in ('left', 'top', 'width', 'height')):
                            region_coords = region_data
                            region_img = self.capture_screen(region=region_coords)
                            if region_img is not None:
                                text = self._extract_and_clean_text(region_img)
                                ocr_texts_for_state[idx] = {'region': region_coords, 'text': text} # Guardar texto por índice
                                if text and len(text) >= MIN_OCR_TEXT_LEN:
                                    print(f"    Texto significativo en región {idx}: '{text}'")
                                    text_found_in_state = True # Marcar si encontramos algo útil
                                else:
                                    print(f"    Texto en región {idx}: '{text}' (ignorado o corto)")
                        else:
                             print(f"Advertencia: Formato de región inválido para '{state_candidate}', índice {idx}: {region_data}")

                    # Si encontramos *algún* texto significativo en *alguna* región de este estado, lo consideramos detectado por OCR
                    if text_found_in_state:
                        result['method'] = 'ocr'
                        result['state'] = state_candidate
                        result['ocr_results'] = ocr_texts_for_state
                        print(f"Estado detectado (OCR Fallback): {result['state']} (Texto relevante encontrado)")
                        return result
                else:
                    print(f"Advertencia: Las regiones OCR para '{state_candidate}' en {OCR_MAPPING_FILE} no son una lista.")

        print("No se pudo detectar el estado mediante OCR fallback.")
        return result # Retorna el diccionario con method='unknown'

    # ... (resto de métodos de ScreenRecognizer sin cambios) ...
# --- Ejemplo de Uso ---

# --- Añade esta función a screen_recognizer.py (cerca de load_json_mapping) ---

def save_json_mapping(mapping, file_path, file_desc="mapping"):
    """Guarda un diccionario de mapping en un archivo JSON."""
    try:
        # Crear directorio si no existe (útil si config/ no existe al principio)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4)
        print(f"Archivo de {file_desc} guardado en: {file_path}")
        return True # Indicar éxito
    except Exception as e:
        print(f"Error al guardar {file_desc} en {file_path}: {e}")
        # Evitar messagebox en este módulo de bajo nivel
        # messagebox.showerror("Error", f"Error al guardar {file_desc}: {e}")
        return False # Indicar fallo
# --- Dentro de la clase ScreenRecognizer en screen_recognizer.py ---

    def reload_data(self):
        """Recarga los mappings JSON y las plantillas."""
        logging.info("Recargando datos del reconocedor...")
        self._load_all_data() # Reutiliza la función interna existente
        logging.info("Datos del reconocedor recargados.")

# ... (resto del código de screen_recognizer.py sin cambios) ...

if __name__ == "__main__":
    print("Iniciando prueba del ScreenRecognizer...")
    # Asegúrate de que los directorios existan
    if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
    if not os.path.exists(IMAGES_DIR): os.makedirs(IMAGES_DIR)

    # Crear archivos JSON de ejemplo si no existen (para prueba)
    if not os.path.exists(TEMPLATE_MAPPING_FILE):
        print(f"Creando archivo de ejemplo: {TEMPLATE_MAPPING_FILE}")
        ejemplo_templates = {
            "pantalla_bienvenida": ["pantalla_bienvenida_20250403_172226.png"],
            "menu_principal_home_seleccionado": ["menu_principal_home_seleccionado_20250403_172940.png"]
        }
        with open(TEMPLATE_MAPPING_FILE, "w", encoding='utf-8') as f: json.dump(ejemplo_templates, f, indent=4)

    if not os.path.exists(OCR_MAPPING_FILE):
        print(f"Creando archivo de ejemplo: {OCR_MAPPING_FILE}")
        ejemplo_ocr = {
             "pantalla_bienvenida": [{"left": 800, "top": 900, "width": 300, "height": 50}] # Ejemplo región "Pulsa Confirmar"
        }
        with open(OCR_MAPPING_FILE, "w", encoding='utf-8') as f: json.dump(ejemplo_ocr, f, indent=4)


    # Inicializar el reconocedor (Monitor 1 por defecto)
    recognizer = ScreenRecognizer(monitor=1, threshold=0.7, ocr_fallback_threshold=0.6)

    # Intentar reconocer la pantalla actual
    print("\nIntentando reconocer pantalla actual...")
    detected_state = recognizer.recognize_screen()
    print("\n=====================================")
    print(f"Estado final detectado: {detected_state}")
    print("=====================================")

    # Ejemplo de cómo podrías usar la extracción de texto para una región específica
    # (si supieras que estás en una pantalla y quieres leer algo concreto)
    # print("\nProbando extracción OCR directa:")
    # ocr_map = load_ocr_mapping()
    # if "pantalla_bienvenida" in ocr_map and ocr_map["pantalla_bienvenida"]:
    #    region_a_leer = ocr_map["pantalla_bienvenida"][0] # Leer la primera región definida
    #    texto_leido = recognizer._extract_and_clean_text(recognizer.capture_screen(region=region_a_leer))
    #    print(f"Texto leído de la región para 'pantalla_bienvenida': '{texto_leido}'")