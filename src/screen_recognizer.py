import os
import json
import re # Para limpiar texto OCR
# Eliminar importaciones de tk y messagebox de este módulo
# from tkinter import messagebox
import cv2
import numpy as np
import mss
import pytesseract
from enum import Enum
import logging # Asegurar que logging esté importado

# --- Configuración del Logging (puede ser configurado externamente también) ---
# Si este módulo se usa solo, esta configuración básica es útil.
# Si se importa en una aplicación más grande, la configuración de la app principal prevalecerá.
if not logging.getLogger().hasHandlers(): # Configurar solo si no hay handlers configurados
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            # logging.FileHandler("recognizer.log", encoding='utf-8'), # Opcional: log específico
            logging.StreamHandler()
        ]
    )

# --- Constantes ---
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
TEMPLATE_MAPPING_FILE = os.path.join(CONFIG_DIR, "templates_mapping.json")
OCR_MAPPING_FILE = os.path.join(CONFIG_DIR, "ocr_regions.json") # <<< Nombre correcto de la constante
# Umbral por defecto para la coincidencia de plantillas
DEFAULT_TEMPLATE_THRESHOLD = 0.75
# Umbral mínimo para considerar una coincidencia parcial (para dirigir OCR)
OCR_FALLBACK_THRESHOLD = 0.6
# Longitud mínima de texto OCR significativo (después de limpiar)
MIN_OCR_TEXT_LEN = 3
# Constante de fuente (Aunque no es ideal aquí, se mantiene por compatibilidad con importación previa)
DEFAULT_FONT_SIZE = 11


# --- Funciones de Carga/Guardado de Mappings (con mejor manejo de errores) ---
def load_json_mapping(file_path, file_desc="mapping"):
    """Carga un mapping JSON desde un archivo con manejo de errores."""
    if not os.path.exists(file_path):
        logging.warning(f"Archivo de {file_desc} '{file_path}' no encontrado. Usando diccionario vacío.")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            if not isinstance(mapping, dict):
                logging.error(f"El contenido de {file_path} no es un diccionario JSON válido.")
                return {}
            return mapping
    except json.JSONDecodeError:
        logging.error(f"El archivo {file_path} está malformado o vacío.")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al cargar {file_path}: {e}")
        return {}

# --- <<< AÑADIR FUNCIÓN GLOBAL save_json_mapping >>> ---
def save_json_mapping(mapping, file_path, file_desc="mapping"):
    """Guarda un diccionario de mapping en un archivo JSON."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4, ensure_ascii=False) # ensure_ascii=False para caracteres especiales
        logging.info(f"Archivo de {file_desc} guardado en: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error al guardar {file_desc} en {file_path}: {e}")
        return False


# --- ScreenRecognizer Class ---
class ScreenRecognizer:
    def __init__(self, monitor=1, threshold=DEFAULT_TEMPLATE_THRESHOLD, ocr_fallback_threshold=OCR_FALLBACK_THRESHOLD):
        """
        Inicializa el reconocedor de pantalla.

        Args:
            monitor (int): Índice del monitor a capturar (1-indexado).
            threshold (float): Umbral principal para template matching.
            ocr_fallback_threshold (float): Umbral mínimo para considerar OCR fallback.
        """
        self.monitor_index = monitor
        self.threshold = threshold
        self.ocr_fallback_threshold = ocr_fallback_threshold
        self.templates = {}
        self.template_names_mapping = {}
        self.ocr_regions_mapping = {}
        self.monitors_info = self._detect_monitors() # Detectar y guardar monitores
        self._load_all_data()

    def _detect_monitors(self):
        """Detecta los monitores existentes usando mss."""
        try:
            with mss.mss() as sct:
                # Devolver la lista completa, el índice 0 es 'all screens'
                return sct.monitors
        except Exception as e:
            logging.error(f"Error detectando monitores: {e}")
            return [{}] # Lista con diccionario vacío como fallback

    def _get_monitor_region(self):
        """Obtiene la geometría del monitor seleccionado (1-based index)."""
        # mss.monitors[0] es 'all screens', los reales empiezan en 1
        monitor_real_index = self.monitor_index
        if monitor_real_index >= 1 and monitor_real_index < len(self.monitors_info):
            return self.monitors_info[monitor_real_index]
        else:
            logging.warning(f"Monitor {self.monitor_index} no válido. Usando monitor primario (1).")
            if len(self.monitors_info) > 1:
                 return self.monitors_info[1] # Fallback al primario
            else:
                 logging.error("No se encontraron monitores válidos.")
                 return None # No se puede proceder

    def _load_all_data(self):
        """Carga los mappings de plantillas y OCR."""
        logging.info("Cargando datos de reconocimiento...")
        self.template_names_mapping = load_json_mapping(TEMPLATE_MAPPING_FILE, "plantillas")
        self.ocr_regions_mapping = load_json_mapping(OCR_MAPPING_FILE, "regiones OCR")
        self._load_templates()
        logging.info("Datos cargados.")

    # --- <<< AÑADIR MÉTODO reload_data >>> ---
    def reload_data(self):
        """Recarga los mappings JSON y las plantillas."""
        logging.info("Recargando datos del reconocedor...")
        self._load_all_data() # Reutiliza la función interna existente
        logging.info("Datos del reconocedor recargados.")

    def _load_templates(self):
        """Carga las imágenes de plantilla en escala de grises."""
        self.templates = {}
        loaded_count = 0
        error_count = 0
        missing_files = []
        corrupt_files = []

        for state, file_list in self.template_names_mapping.items():
            if not isinstance(file_list, list):
                 logging.warning(f"Valor para '{state}' en {TEMPLATE_MAPPING_FILE} no es una lista. Saltando.")
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
                        logging.error(f"No se pudo cargar la imagen (posiblemente corrupta): {template_path}")
                        corrupt_files.append(template_path)
                        error_count += 1
                else:
                    logging.warning(f"No se encontró la plantilla listada: {template_path}")
                    missing_files.append(template_path)
                    error_count += 1

            if loaded_images:
                self.templates[state] = loaded_images

        logging.info(f"Carga de plantillas: {loaded_count} cargadas, {error_count} errores/faltantes.")
        if missing_files:
             logging.warning(f"Archivos de plantilla faltantes: {missing_files}")
        if corrupt_files:
             logging.error(f"Archivos de plantilla corruptos: {corrupt_files}")


    def capture_screen(self, region=None):
        """Captura la pantalla o una región específica del monitor configurado."""
        monitor_region = self._get_monitor_region()
        if monitor_region is None: return None

        capture_area = region if region is not None else monitor_region

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(capture_area)
                img = np.array(sct_img)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img_bgr
        except Exception as e:
            logging.error(f"Error durante la captura de pantalla: {e}")
            return None


    def find_template_on_screen(self, screen_gray, template_gray):
        """Busca una única plantilla en la pantalla."""
        if template_gray.shape[0] > screen_gray.shape[0] or template_gray.shape[1] > screen_gray.shape[1]:
            return None, 0.0
        try:
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            return max_loc, max_val
        except cv2.error as e:
             # Puede ocurrir si screen_gray es más pequeño que template_gray después de todo
             logging.warning(f"Error en matchTemplate (probablemente tamaño): {e}")
             return None, 0.0


    def recognize_screen_for_test(self):
        """
        Intenta reconocer la pantalla actual y devuelve información detallada para testeo,
        incluyendo verificación de texto esperado en OCR.
        """
        result = {
            'method': 'unknown',
            'state': 'unknown',
            'confidence': None,
            'ocr_results': None # {idx: {'region': dict, 'text': str, 'expected': list, 'match_expected': bool}}
        }
        screen_bgr = self.capture_screen()
        if screen_bgr is None:
            logging.error("No se pudo capturar la pantalla para reconocimiento.")
            return result
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        # --- 1. Template Matching ---
        best_match_state = "unknown"
        best_match_val = 0.0
        potential_ocr_states = []

        logging.debug("Iniciando Template Matching...")
        for state, template_list in self.templates.items():
            state_best_val = 0.0
            for i, template_gray in enumerate(template_list):
                loc, match_val = self.find_template_on_screen(screen_gray, template_gray)
                logging.debug(f"  Comparando con {state} (plantilla {i+1}/{len(template_list)}): Confianza={match_val:.3f}")
                state_best_val = max(state_best_val, match_val)

            if state_best_val >= self.threshold:
                if state_best_val > best_match_val:
                    best_match_val = state_best_val
                    best_match_state = state
                    logging.debug(f"  Nuevo mejor match encontrado: {state} con {best_match_val:.3f}")
            elif state_best_val >= self.ocr_fallback_threshold:
                potential_ocr_states.append((state, state_best_val))
                logging.debug(f"  Candidato OCR: {state} con {state_best_val:.3f}")

        if best_match_state != "unknown":
            result['method'] = 'template'
            result['state'] = best_match_state
            result['confidence'] = best_match_val
            logging.info(f"Estado detectado (Template): {result['state']} (Confianza: {result['confidence']:.3f})")
            return result

        # --- 2. OCR Fallback con Verificación de Texto Esperado ---
        logging.info("No se encontró coincidencia clara de plantilla. Intentando OCR fallback con verificación...")
        potential_ocr_states.sort(key=lambda item: item[1], reverse=True)

        for state_candidate, match_score in potential_ocr_states:
            if state_candidate in self.ocr_regions_mapping:
                regions_data_list = self.ocr_regions_mapping[state_candidate]
                if isinstance(regions_data_list, list):
                    ocr_results_for_state = {}
                    found_match_in_state = False # Flag si *alguna* región coincide con su texto esperado
                    logging.info(f"  Probando OCR para candidato: {state_candidate} (Score: {match_score:.3f}) con {len(regions_data_list)} regiones...")

                    for idx, region_data in enumerate(regions_data_list):
                        # --- Validar estructura y extraer datos ---
                        if not (isinstance(region_data, dict) and 'region' in region_data and
                                isinstance(region_data['region'], dict) and # Asegurar que 'region' sea dict
                                all(k in region_data['region'] for k in ('left', 'top', 'width', 'height'))):
                            logging.warning(f"    Formato de datos de región inválido para '{state_candidate}', índice {idx}. Saltando: {region_data}")
                            continue

                        region_coords = region_data['region']
                        expected_texts = region_data.get('expected_text', [])
                        if not isinstance(expected_texts, list):
                             logging.warning(f"    'expected_text' para '{state_candidate}' región {idx} no es una lista. Tratando como vacía.")
                             expected_texts = []

                        # --- Realizar OCR ---
                        region_img = self.capture_screen(region=region_coords)
                        extracted_text = self._extract_and_clean_text(region_img)

                        # --- Verificar si coincide con texto esperado ---
                        match_expected = False
                        if extracted_text and expected_texts:
                            for expected in expected_texts:
                                if expected.lower() == extracted_text.lower():
                                    match_expected = True
                                    break

                        logging.info(f"    Región {idx}: Texto='{extracted_text}', Esperado={expected_texts}, Coincide={match_expected}")

                        ocr_results_for_state[idx] = {
                            'region': region_coords,
                            'text': extracted_text,
                            'expected': expected_texts,
                            'match_expected': match_expected
                        }

                        if match_expected:
                            found_match_in_state = True # Marcar si esta región coincidió

                    # --- Decisión Final ---
                    if found_match_in_state:
                        result['method'] = 'ocr'
                        result['state'] = state_candidate
                        result['ocr_results'] = ocr_results_for_state
                        logging.info(f"Estado detectado (OCR Fallback Verificado): {result['state']}")
                        return result
                else:
                    logging.warning(f"Las regiones OCR para '{state_candidate}' en {OCR_MAPPING_FILE} no son una lista.")

        logging.warning("No se pudo detectar el estado mediante OCR fallback verificado.")
        return result

    def _extract_and_clean_text(self, image_bgr):
        """Extrae texto de una imagen y lo limpia."""
        if image_bgr is None: return ""
        try:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            # Considerar aplicar umbralización aquí si ayuda al OCR
            # _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(gray, lang="spa+eng") # Español primero si es más común
            text = text.replace('\n', ' ').replace('\r', '')
            text = re.sub(r'[^a-zA-Z0-9ñÑáéíóúÁÉÍÓÚüÜ\s]', '', text) # Añadir Ü si es necesario
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            logging.error(f"Error durante OCR: {e}")
            return ""

# --- Ejemplo de Uso (opcional, el tester es ahora la forma principal de probar) ---
if __name__ == "__main__":
    logging.info("Ejecutando prueba interna de ScreenRecognizer...")

    # Crear directorios si no existen
    if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
    if not os.path.exists(IMAGES_DIR): os.makedirs(IMAGES_DIR)

    # Crear archivos JSON de ejemplo si no existen
    if not os.path.exists(TEMPLATE_MAPPING_FILE):
        logging.info(f"Creando archivo de ejemplo: {TEMPLATE_MAPPING_FILE}")
        ejemplo_templates = {"ejemplo_estado": ["ejemplo_plantilla.png"]}
        save_json_mapping(ejemplo_templates, TEMPLATE_MAPPING_FILE, "plantillas de ejemplo")

    if not os.path.exists(OCR_MAPPING_FILE):
        logging.info(f"Creando archivo de ejemplo: {OCR_MAPPING_FILE}")
        ejemplo_ocr = {
             "ejemplo_estado": [{"region": {"left": 100, "top": 100, "width": 200, "height": 50}, "expected_text": ["Texto Ejemplo", "Otro Texto"]}]
        }
        save_json_mapping(ejemplo_ocr, OCR_MAPPING_FILE, "regiones OCR de ejemplo")

    try:
        recognizer = ScreenRecognizer(monitor=1) # Usar monitor 1

        # Intentar reconocer la pantalla actual
        logging.info("Intentando reconocer pantalla actual (método de test)...")
        detected_state_info = recognizer.recognize_screen_for_test()
        logging.info("--- Resultado Detallado ---")
        logging.info(json.dumps(detected_state_info, indent=4, ensure_ascii=False))
        logging.info("---------------------------")

    except Exception as e:
        logging.exception("Error durante la prueba interna de ScreenRecognizer.")