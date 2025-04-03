"""
Optimized Screen Recognizer for eFootball Automation using JSON Mapping

Este módulo utiliza mss para capturar la pantalla y carga las plantillas
desde un archivo JSON (templates_mapping.json) para realizar la detección
de pantallas del juego.
"""

import cv2
import numpy as np
import mss
import os
import json
from enum import Enum

# Opcional: Puedes conservar el enum para tener valores estándar, pero aquí lo usaremos para referencia.
class GameScreen(Enum):
    UNKNOWN = "unknown"
    # Los demás valores se definirán según las etiquetas que utilices en el JSON

# Ruta del archivo JSON que contiene el mapping de plantillas.
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_MAPPING_FILE = os.path.join(PROJECT_DIR, "templates_mapping.json")

def load_templates_mapping():
    """Carga el mapping de plantillas desde el archivo JSON."""
    if os.path.exists(TEMPLATES_MAPPING_FILE):
        with open(TEMPLATES_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print("No se encontró el archivo de mapping, usando diccionario vacío.")
        return {}

class ScreenRecognizer:
    def __init__(self, monitor=1, templates_dir="images", capture_region=None):
        """
        Inicializa el reconocedor de pantalla.

        Args:
            monitor (int): Índice del monitor a capturar (1-indexado).
            templates_dir (str): Directorio que contiene las imágenes de plantilla.
            capture_region (dict o None): Región de captura definida como
                {"left": int, "top": int, "width": int, "height": int}.
                Si es None, se captura todo el monitor.
        """
        self.monitor = monitor
        self.templates_dir = templates_dir
        self.capture_region = capture_region
        self.templates = {}  # Diccionario que almacenará listas de plantillas para cada etiqueta
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
        with mss.mss() as sct:
            monitor_full = sct.monitors[self.monitor]
            region = self.capture_region if self.capture_region else monitor_full
            sct_img = sct.grab(region)
            img = np.array(sct_img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr

    def find_template(self, screen_gray, template_gray, threshold=0.7):
        """
        Busca una plantilla en la imagen de pantalla capturada.

        Args:
            screen_gray (np.array): Imagen capturada en escala de grises.
            template_gray (np.array): Imagen de plantilla en escala de grises.
            threshold (float): Umbral mínimo de coincidencia (valor entre 0 y 1).

        Returns:
            Tuple (x, y, w, h) si se encuentra la plantilla; de lo contrario, None.
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
        # Recorre todos los estados y sus plantillas
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

    def show_capture(self):
        """
        Para pruebas: muestra la imagen capturada en una ventana.
        """
        screen = self.capture_screen()
        cv2.imshow("Captura de Pantalla", screen)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Ejemplo: define la región de captura si es necesario.
    region_juego = {"left": 0, "top": 0, "width": 3840, "height": 2160}
    recognizer = ScreenRecognizer(monitor=1, templates_dir=os.path.join(PROJECT_DIR, "images"), capture_region=region_juego)
    current_state = recognizer.detect_screen(threshold=0.7)
    print("Estado final detectado:", current_state)
