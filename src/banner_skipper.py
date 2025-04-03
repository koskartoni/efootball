"""
Función para saltar banners iniciales en eFootball

Este módulo implementa la funcionalidad para saltar automáticamente
los banners y anuncios iniciales que aparecen al iniciar el juego eFootball,
hasta llegar al menú principal.

Utiliza los módulos de control de gamepad y reconocimiento de pantalla.
"""

import time
from gamepad_controller import GamepadController, GamepadButton, EFootballSequences
from screen_recognizer import ScreenRecognizer, GameScreen, ScreenElement

class BannerSkipper:
    """
    Clase para automatizar el proceso de saltar banners iniciales en eFootball.
    """
    
    def __init__(self, gamepad_controller=None, screen_recognizer=None):
        """
        Inicializa el saltador de banners.
        
        Args:
            gamepad_controller (GamepadController, optional): Controlador de gamepad a utilizar
            screen_recognizer (ScreenRecognizer, optional): Reconocedor de pantalla a utilizar
        """
        # Inicializar el controlador de gamepad si no se proporciona uno
        if gamepad_controller is None:
            self.gamepad = GamepadController()
        else:
            self.gamepad = gamepad_controller
        
        # Inicializar el reconocedor de pantalla si no se proporciona uno
        if screen_recognizer is None:
            self.recognizer = ScreenRecognizer()
        else:
            self.recognizer = screen_recognizer
        
        print("Saltador de banners inicializado")
    
    def skip_welcome_screen(self, max_attempts=5, wait_time=2.0):
        """
        Salta la pantalla de bienvenida presionando el botón A.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se saltó correctamente, False en caso contrario
        """
        print("Intentando saltar la pantalla de bienvenida...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            
            # Verificar si estamos en la pantalla de bienvenida
            current_screen = self.recognizer.recognize_screen(screen)
            
            if current_screen == GameScreen.WELCOME:
                print(f"Pantalla de bienvenida detectada (intento {attempt+1})")
                
                # Presionar el botón A para continuar
                self.gamepad.press_button(GamepadButton.A, duration=0.2)
                time.sleep(wait_time)
                
                # Verificar si hemos avanzado
                new_screen = self.recognizer.recognize_screen()
                if new_screen != GameScreen.WELCOME:
                    print("Pantalla de bienvenida saltada correctamente")
                    return True
            else:
                print(f"No estamos en la pantalla de bienvenida, estamos en: {current_screen.value}")
                return True  # Ya estamos fuera de la pantalla de bienvenida
        
        print("No se pudo saltar la pantalla de bienvenida después de varios intentos")
        return False
    
    def skip_banner(self, max_attempts=3, wait_time=1.0):
        """
        Salta un banner o anuncio individual.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se saltó correctamente, False en caso contrario
        """
        print("Intentando saltar un banner...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            
            # Verificar si estamos en un banner
            current_screen = self.recognizer.recognize_screen(screen)
            
            if current_screen == GameScreen.BANNER:
                print(f"Banner detectado (intento {attempt+1})")
                
                # Detectar el tipo de banner
                banner_type = self.recognizer.detect_banner_type(screen)
                print(f"Tipo de banner detectado: {banner_type}")
                
                # Buscar el botón X para cerrar el banner
                x_button = self.recognizer.find_element(ScreenElement.BUTTON_X, screen)
                
                if x_button is not None:
                    # Si encontramos el botón X, presionarlo
                    print("Botón X encontrado, presionando...")
                    self.gamepad.press_button(GamepadButton.X, duration=0.2)
                else:
                    # Si no encontramos el botón X, intentar con el botón A
                    print("Botón X no encontrado, intentando con botón A...")
                    self.gamepad.press_button(GamepadButton.A, duration=0.2)
                
                time.sleep(wait_time)
                
                # Verificar si hemos avanzado
                new_screen = self.recognizer.recognize_screen()
                if new_screen != GameScreen.BANNER:
                    print("Banner saltado correctamente")
                    return True
            else:
                print(f"No estamos en un banner, estamos en: {current_screen.value}")
                return True  # Ya estamos fuera del banner
        
        print("No se pudo saltar el banner después de varios intentos")
        return False
    
    def skip_all_banners(self, max_banners=10, timeout=60):
        """
        Salta todos los banners iniciales hasta llegar al menú principal.
        
        Args:
            max_banners (int): Número máximo de banners a intentar saltar
            timeout (int): Tiempo máximo total en segundos
        
        Returns:
            bool: True si se llegó al menú principal, False en caso contrario
        """
        print("Iniciando proceso para saltar todos los banners iniciales...")
        
        start_time = time.time()
        banners_skipped = 0
        
        # Primero, intentar saltar la pantalla de bienvenida
        if not self.skip_welcome_screen():
            print("No se pudo saltar la pantalla de bienvenida")
            return False
        
        # Luego, saltar todos los banners hasta llegar al menú principal
        while banners_skipped < max_banners and time.time() - start_time < timeout:
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en el menú principal, hemos terminado
            if current_screen == GameScreen.MAIN_MENU:
                print(f"Llegamos al menú principal después de saltar {banners_skipped} banners")
                return True
            
            # Si estamos en un banner, intentar saltarlo
            if current_screen == GameScreen.BANNER:
                print(f"Banner #{banners_skipped + 1} detectado, intentando saltar...")
                if self.skip_banner():
                    banners_skipped += 1
                    print(f"Banner #{banners_skipped} saltado correctamente")
                else:
                    print(f"No se pudo saltar el banner #{banners_skipped + 1}")
            else:
                # Si no estamos en un banner ni en el menú principal, intentar con botón A
                print(f"Pantalla desconocida: {current_screen.value}, intentando con botón A...")
                self.gamepad.press_button(GamepadButton.A, duration=0.2)
            
            # Esperar un momento antes de la siguiente comprobación
            time.sleep(1.0)
        
        # Verificar si llegamos al menú principal
        final_screen = self.recognizer.recognize_screen()
        if final_screen == GameScreen.MAIN_MENU:
            print(f"Llegamos al menú principal después de saltar {banners_skipped} banners")
            return True
        else:
            print(f"No se pudo llegar al menú principal. Pantalla actual: {final_screen.value}")
            return False
    
    def run(self):
        """
        Ejecuta el proceso completo de saltar banners iniciales.
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print("Iniciando proceso automático para saltar banners iniciales en eFootball...")
        
        # Guardar una captura de la pantalla inicial
        self.recognizer.save_screenshot("pantalla_inicial.png")
        
        # Intentar saltar todos los banners hasta llegar al menú principal
        result = self.skip_all_banners()
        
        # Guardar una captura de la pantalla final
        self.recognizer.save_screenshot("pantalla_final.png")
        
        if result:
            print("Proceso completado exitosamente. Hemos llegado al menú principal.")
        else:
            print("No se pudo completar el proceso. Revise las capturas de pantalla para más detalles.")
        
        return result

# Ejemplo de uso
def main():
    """Función principal para ejecutar el saltador de banners"""
    # Crear el controlador de gamepad
    gamepad = GamepadController()
    
    # Crear el reconocedor de pantalla
    recognizer = ScreenRecognizer()
    
    # Crear el saltador de banners
    banner_skipper = BannerSkipper(gamepad, recognizer)
    
    # Ejecutar el proceso
    banner_skipper.run()

if __name__ == "__main__":
    print("Módulo para saltar banners iniciales en eFootball")
    print("Este módulo permite automatizar el proceso de saltar los banners")
    print("y anuncios iniciales que aparecen al iniciar el juego.")
    print("\nEjecutando proceso...")
    main()
