"""
Optimized Screen Recognizer for eFootball Automation using JSON Mapping and OCR fallback

Este módulo utiliza mss para capturar la pantalla, carga las plantillas desde
el archivo JSON (templates_mapping.json) para realizar la detección visual, y si ésta falla,
usa regiones OCR definidas en el archivo ocr_regions.json para extraer texto en tiempo real.
"""

import cv2
import numpy as np
import mss
import os
import json
from enum import Enum
import pytesseract

# Definir rutas del proyecto
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_MAPPING_FILE = os.path.join(PROJECT_DIR, "templates_mapping.json")
OCR_MAPPING_FILE = os.path.join(PROJECT_DIR, "ocr_regions.json")

def load_templates_mapping():
    """Carga el mapping de plantillas desde el archivo JSON."""
    if os.path.exists(TEMPLATES_MAPPING_FILE):
        with open(TEMPLATES_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print("No se encontró el archivo de mapping de plantillas, usando diccionario vacío.")
        return {}

def load_ocr_mapping():
    """Carga el mapping de zonas OCR desde el archivo JSON."""
    if os.path.exists(OCR_MAPPING_FILE):
        with open(OCR_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print("No se encontró el archivo de mapping OCR, usando diccionario vacío.")
        return {}

def extract_text_from_region(region, monitor=1):
    """
    Captura una región específica de la pantalla y aplica OCR para extraer el texto.

    Args:
        region (dict): Diccionario con 'left', 'top', 'width' y 'height'.
        monitor (int): Número del monitor (1-indexado).

    Returns:
        Texto extraído (str) limpio.
    """
    with mss.mss() as sct:
        sct_img = sct.grab(region)
        img = np.array(sct_img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang="eng")
        return text.strip()

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

class ScreenRecognizer:
    def __init__(self, monitor=1, templates_dir="images", capture_region=None):
        """
        Inicializa el reconocedor de pantalla.

        Args:
            monitor (int): Índice del monitor a capturar (1-indexado).
            templates_dir (str): Directorio que contiene las imágenes de plantilla.
            capture_region (dict o None): Región de captura definida como {"left": int, "top": int, "width": int, "height": int}.
                Si es None, se captura todo el monitor.
        """
        self.monitor = monitor
        self.templates_dir = templates_dir
        self.capture_region = capture_region
        self.templates = {}  # Diccionario: estado -> lista de imágenes (en escala de grises)
        self.load_templates_from_json()

    def load_templates_from_json(self):
        """
        Carga las plantillas usando el mapping del archivo JSON.
        Cada clave en el mapping es una etiqueta (estado) y su valor es una lista de nombres de archivos.
        Se cargan las imágenes en escala de grises para acelerar la coincidencia.
        """
        mapping = load_templates_mapping()
        for state, file_list in mapping.items():
            loaded_images = []
            for file_name in file_list:
                template_path = os.path.join(self.templates_dir, file_name)
                if os.path.exists(template_path):
                    img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        loaded_images.append(img)
                    else:
                        print(f"Error al cargar la imagen (posiblemente dañada): {template_path}")
                else:
                    print(f"No se encontró la plantilla: {template_path}")
            if loaded_images:
                self.templates[state] = loaded_images
            else:
                print(f"No se cargaron plantillas para el estado: {state}")

    def capture_screen(self):
        """
        Captura la pantalla utilizando mss, considerando la región definida si se especifica.

        Returns:
            Imagen capturada en formato BGR (numpy array).
        """
        return capture_screen(region=self.capture_region, monitor=self.monitor)

    def find_template(self, screen_gray, template_gray, threshold=0.7):
        """
        Busca una plantilla en la imagen de pantalla capturada.

        Args:
            screen_gray (np.array): Imagen capturada en escala de grises.
            template_gray (np.array): Imagen de plantilla en escala de grises.
            threshold (float): Umbral mínimo de coincidencia (valor entre 0 y 1).

        Returns:
            Tuple ((x, y, w, h), match_val) si se encuentra la plantilla; de lo contrario, (None, 0).
        """
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            h, w = template_gray.shape
            return (max_loc[0], max_loc[1], w, h), max_val
        return None, 0

    def detect_screen(self, threshold=0.7):
        """
        Detecta la pantalla actual del juego comparando la captura con las plantillas cargadas.

        Args:
            threshold (float): Umbral de coincidencia para considerar un template como detectado.

        Returns:
            La etiqueta (estado) detectada o "unknown" si ninguna plantilla coincide.
        """
        screen_bgr = self.capture_screen()
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        best_match = ("unknown", 0.0)
        for state, template_list in self.templates.items():
            for template_gray in template_list:
                match, match_val = self.find_template(screen_gray, template_gray, threshold)
                if match and match_val > best_match[1]:
                    best_match = (state, match_val)

        if best_match[0] != "unknown":
            print(f"Pantalla detectada: {best_match[0]} (coincidencia: {best_match[1]:.2f})")
            return best_match[0]
        else:
            print("Pantalla actual detectada: unknown")
            return "unknown"

    def detect_screen_with_ocr_from_file(self, threshold=0.7):
        """
        Método híbrido para detectar la pantalla: primero se intenta el matching visual,
        y si no se obtiene un resultado (estado "unknown"), se cargan las zonas OCR definidas
        en ocr_regions.json y se extrae texto en cada una. Si se obtiene un texto significativo,
        se devuelve ese estado.

        Args:
            threshold (float): Umbral para el matching visual.

        Returns:
            Estado detectado (str).
        """
        state = self.detect_screen(threshold=threshold)
        if state != "unknown":
            return state
        # Si no se detecta mediante matching, intenta OCR
        ocr_mapping = load_ocr_mapping()
        for state_name, region in ocr_mapping.items():
            text = extract_text_from_region(region, monitor=self.monitor)
            if text and len(text) > 3:
                print(f"Estado detectado por OCR: {state_name} (texto: {text})")
                return state_name
        print("Pantalla detectada: unknown")
        return "unknown"

if __name__ == "__main__":
    # Define la región de captura si es necesario; si no, puede ser None para capturar todo el monitor.
    region_juego = {"left": 0, "top": 0, "width": 3840, "height": 2160}
    recognizer = ScreenRecognizer(monitor=1, templates_dir=os.path.join(PROJECT_DIR, "images"), capture_region=region_juego)
    # Usa el método híbrido que intenta matching visual y, en caso de fallo, OCR.
    detected_state = recognizer.detect_screen_with_ocr_from_file(threshold=0.7)
    print("Estado final detectado:", detected_state)
