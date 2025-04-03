import cv2
import numpy as np
import mss
import os
from enum import Enum

class GameScreen(Enum):
    UNKNOWN = "unknown"
    WELCOME = "pantalla_bienvenida"
    BANNER = "banner_inicial"
    MAIN_MENU = "menu_principal"
    CONTRACTS_MENU = "menu_contratos"
    NORMAL_PLAYERS_LIST = "jugadores_normales_lista"
    PURCHASE_CONFIRMATION = "confirmacion_compra"
    PURCHASE_COMPLETED = "compra_realizada"
    MY_TEAM = "mi_equipo"
    PLAYER_LIST = "mi_equipo_jugadores_lista"
    PLAYER_ACTIONS = "mi_equipo_jugador_acciones"
    PLAYER_SKILLS = "mi_equipo_jugador_habilidades"

# Aquí mapeamos cada estado a una o varias imágenes reales que tú tengas
TEMPLATE_FILES = {
    GameScreen.UNKNOWN: ["Anuncio1.png", "Bonus_Campaña.png", "Bonus_inicio_sesion.png"],
    GameScreen.WELCOME: ["Pantalla_bienvenida.png"],
    GameScreen.BANNER: ["Menu_principal_baner.png"],  # o las que correspondan
    GameScreen.MAIN_MENU: ["Menu_principal.png", "Menu_principal_list_arriba.png", "Menu_principal_selContratacion.png"],
    GameScreen.CONTRACTS_MENU: ["Menu_contratos.png"],
    GameScreen.NORMAL_PLAYERS_LIST: ["Jugadores_normales_lista.png"],
    GameScreen.PURCHASE_CONFIRMATION: ["Confirmacion_compra_1.png", "Confirmacion_compra_2.png", "Confirmacion_compra_3.png"],
    GameScreen.PURCHASE_COMPLETED: ["Compra_realizada.png"],
    GameScreen.MY_TEAM: ["Mi_equipo.png"],  # o la que tengas
    GameScreen.PLAYER_LIST: ["Mi_equipo_jugadores_lista.png"],
    GameScreen.PLAYER_ACTIONS: ["Mi_equipo_jugadores_accion_1.png", "Mi_equipo_jugadores_accion_2.png"],
    GameScreen.PLAYER_SKILLS: ["Mi_equipo_raul_habilidades_entrenamiento_1.png", "Mi_equipo_raul_habilidades_entrenamiento_2.png"],
}

class ScreenRecognizer:
    def __init__(self, monitor=1, templates_dir="images", capture_region=None):
        self.monitor = monitor
        self.templates_dir = templates_dir
        self.capture_region = capture_region
        # Aquí guardaremos listas de plantillas por cada estado
        self.templates = {}
        self.load_templates()

    def load_templates(self):
        """
        Carga todas las plantillas indicadas en TEMPLATE_FILES.
        Cada estado puede tener varias imágenes asociadas.
        """
        for state, file_list in TEMPLATE_FILES.items():
            loaded_images = []
            for file_name in file_list:
                template_path = os.path.join(self.templates_dir, file_name)
                if os.path.exists(template_path):
                    img = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        loaded_images.append(img)
                else:
                    print(f"No se encontró la plantilla: {template_path}")
            if loaded_images:
                self.templates[state] = loaded_images

    def capture_screen(self):
        with mss.mss() as sct:
            print("Monitores detectados:", sct.monitors)
            monitor_full = sct.monitors[self.monitor]
            region = self.capture_region if self.capture_region else monitor_full
            sct_img = sct.grab(region)
            img = np.array(sct_img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr

    def find_template(self, screen_gray, template_gray, threshold=0.7):
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            h, w = template_gray.shape
            return (max_loc[0], max_loc[1], w, h)
        return None

    def detect_screen(self, threshold=0.7):
        """
        Devuelve el estado de pantalla detectado. Si ninguna plantilla coincide, UNKNOWN.
        """
        screen_bgr = self.capture_screen()
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        best_match = (GameScreen.UNKNOWN, 0.0)
        # Recorremos todos los estados que tengan plantillas cargadas
        for state, template_list in self.templates.items():
            for template_gray in template_list:
                result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > best_match[1] and max_val >= threshold:
                    best_match = (state, max_val)

        if best_match[0] != GameScreen.UNKNOWN:
            print(f"Pantalla detectada: {best_match[0].value} (coincidencia: {best_match[1]:.2f})")
            return best_match[0]
        else:
            print("Pantalla actual detectada: unknown")
            return GameScreen.UNKNOWN

    def show_capture(self):
        screen = self.capture_screen()
        cv2.imshow("Captura de Pantalla", screen)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Ajusta la región a la parte de tu monitor 4K donde corre el juego (si está en ventana 1080p, por ejemplo)
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sube 1 nivel
    IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
    region_juego = None
    recognizer = ScreenRecognizer(monitor=1, templates_dir="images", capture_region=region_juego)
    # Captura y guarda para depurar
    screen_bgr = recognizer.capture_screen()
    cv2.imwrite("captura_debug.png", screen_bgr)

    current_screen = recognizer.detect_screen(threshold=0.6)
    print("Estado final detectado:", current_screen.value)
