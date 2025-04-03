"""
Función para realizar entrenamientos de habilidad a jugadores en eFootball

Este módulo implementa la funcionalidad para automatizar el proceso de entrenamiento
de habilidades a jugadores específicos en eFootball, navegando por los menús de Mi Equipo,
seleccionando un jugador y realizando el entrenamiento de habilidades.

Utiliza los módulos de control de gamepad y reconocimiento de pantalla.
"""

import time
import os
from gamepad_controller import GamepadController, GamepadButton, EFootballSequences
from screen_recognizer import ScreenRecognizer, GameScreen, ScreenElement

class PlayerTrainer:
    """
    Clase para automatizar el proceso de entrenamiento de habilidades a jugadores en eFootball.
    """
    
    def __init__(self, gamepad_controller=None, screen_recognizer=None):
        """
        Inicializa el entrenador de jugadores.
        
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
        
        # Directorio para guardar capturas de pantalla
        self.screenshots_dir = "/home/ubuntu/efootball_automation/screenshots/training"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        print("Entrenador de jugadores inicializado")
    
    def navigate_to_my_team(self, max_attempts=5, wait_time=2.0):
        """
        Navega desde el menú principal a la sección de Mi Equipo.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se navegó correctamente, False en caso contrario
        """
        print("Navegando a la sección de Mi Equipo...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en Mi Equipo, hemos terminado
            if current_screen == GameScreen.MY_TEAM:
                print("Ya estamos en la sección de Mi Equipo")
                return True
            
            # Si estamos en el menú principal, navegar a Mi Equipo
            if current_screen == GameScreen.MAIN_MENU:
                print(f"Menú principal detectado (intento {attempt+1})")
                
                # Buscar la opción de Mi Equipo
                my_team_option = self.recognizer.find_element(ScreenElement.MY_TEAM_OPTION, screen)
                
                if my_team_option is not None:
                    # Si encontramos la opción, navegar hasta ella y seleccionarla
                    print("Opción de Mi Equipo encontrada, navegando...")
                    
                    # Ejecutar la secuencia para navegar a Mi Equipo
                    self.gamepad.execute_sequence(EFootballSequences.navegar_menu_principal_a_mi_equipo())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a Mi Equipo
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.MY_TEAM:
                        print("Navegación a Mi Equipo exitosa")
                        return True
                else:
                    print("Opción de Mi Equipo no encontrada, intentando con secuencia predefinida...")
                    # Si no encontramos la opción, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.navegar_menu_principal_a_mi_equipo())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a Mi Equipo
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.MY_TEAM:
                        print("Navegación a Mi Equipo exitosa")
                        return True
            else:
                print(f"No estamos en el menú principal, estamos en: {current_screen.value}")
                print("Intentando volver al menú principal...")
                
                # Intentar volver al menú principal presionando B varias veces
                for _ in range(3):
                    self.gamepad.press_button(GamepadButton.B, duration=0.2)
                    time.sleep(1.0)
                
                # Verificar si hemos vuelto al menú principal
                new_screen = self.recognizer.recognize_screen()
                if new_screen == GameScreen.MAIN_MENU:
                    print("Volvimos al menú principal")
                    # Continuar con el siguiente intento
                    continue
        
        print("No se pudo navegar a Mi Equipo después de varios intentos")
        return False
    
    def find_player_by_name(self, player_name, max_attempts=5, max_scrolls=10, wait_time=1.0):
        """
        Busca un jugador por su nombre en la lista de jugadores del equipo.
        
        Args:
            player_name (str): Nombre del jugador a buscar
            max_attempts (int): Número máximo de intentos
            max_scrolls (int): Número máximo de desplazamientos hacia abajo
            wait_time (float): Tiempo de espera entre acciones en segundos
        
        Returns:
            bool: True si se encontró el jugador, False en caso contrario
        """
        print(f"Buscando jugador: {player_name}")
        
        # Capturar la pantalla actual
        screen = self.recognizer.capture_screen()
        current_screen = self.recognizer.recognize_screen(screen)
        
        # Verificar que estamos en la sección de Mi Equipo
        if current_screen != GameScreen.MY_TEAM and current_screen != GameScreen.PLAYER_LIST:
            print(f"No estamos en Mi Equipo ni en la lista de jugadores, estamos en: {current_screen.value}")
            print("Intentando navegar a Mi Equipo...")
            
            if not self.navigate_to_my_team():
                print("No se pudo navegar a Mi Equipo")
                return False
        
        # Si estamos en Mi Equipo pero no en la lista de jugadores, navegar a la lista
        if current_screen == GameScreen.MY_TEAM:
            print("Navegando a la lista de jugadores...")
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(wait_time)
            
            # Verificar si hemos llegado a la lista de jugadores
            new_screen = self.recognizer.recognize_screen()
            if new_screen != GameScreen.PLAYER_LIST:
                print(f"No se pudo navegar a la lista de jugadores. Pantalla actual: {new_screen.value}")
                return False
        
        # Guardar una captura de pantalla antes de buscar al jugador
        self.recognizer.save_screenshot(f"busqueda_{player_name}_inicio.png", self.screenshots_dir)
        
        # Nota: En una implementación real, aquí se utilizaría OCR para reconocer
        # los nombres de los jugadores en la lista. Como es una simulación,
        # simplemente navegaremos por la lista y seleccionaremos un jugador.
        
        print("Buscando jugador en la lista (simulación)...")
        
        # Intentar encontrar al jugador desplazándose por la lista
        for scroll in range(max_scrolls):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            
            # Aquí iría la lógica de OCR para detectar el nombre del jugador
            # Por ahora, simplemente simulamos que no lo encontramos y seguimos desplazándonos
            
            print(f"Desplazamiento {scroll+1}/{max_scrolls}, jugador no encontrado aún")
            
            # Desplazarse hacia abajo
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(wait_time)
        
        # Para la simulación, asumimos que hemos encontrado al jugador
        # En una implementación real, se verificaría si realmente se encontró
        
        print(f"Jugador '{player_name}' encontrado (simulación)")
        
        # Seleccionar el jugador
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time)
        
        # Verificar si hemos llegado a la pantalla de acciones del jugador
        new_screen = self.recognizer.recognize_screen()
        if new_screen == GameScreen.PLAYER_ACTIONS:
            print("Jugador seleccionado correctamente")
            
            # Guardar una captura de pantalla después de seleccionar al jugador
            self.recognizer.save_screenshot(f"jugador_{player_name}_seleccionado.png", self.screenshots_dir)
            
            return True
        else:
            print(f"No se pudo seleccionar al jugador. Pantalla actual: {new_screen.value}")
            return False
    
    def navigate_to_skills(self, max_attempts=5, wait_time=2.0):
        """
        Navega a la sección de habilidades del jugador seleccionado.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se navegó correctamente, False en caso contrario
        """
        print("Navegando a la sección de habilidades...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en la pantalla de habilidades, hemos terminado
            if current_screen == GameScreen.PLAYER_SKILLS:
                print("Ya estamos en la sección de habilidades")
                return True
            
            # Si estamos en la pantalla de acciones del jugador, navegar a habilidades
            if current_screen == GameScreen.PLAYER_ACTIONS:
                print(f"Pantalla de acciones del jugador detectada (intento {attempt+1})")
                
                # Buscar la opción de habilidades
                skills_option = self.recognizer.find_element(ScreenElement.SKILLS_OPTION, screen)
                
                if skills_option is not None:
                    # Si encontramos la opción, navegar hasta ella y seleccionarla
                    print("Opción de habilidades encontrada, navegando...")
                    
                    # Ejecutar la secuencia para acceder a habilidades
                    self.gamepad.execute_sequence(EFootballSequences.acceder_a_habilidades())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la pantalla de habilidades
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.PLAYER_SKILLS:
                        print("Navegación a habilidades exitosa")
                        return True
                else:
                    print("Opción de habilidades no encontrada, intentando con secuencia predefinida...")
                    # Si no encontramos la opción, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.acceder_a_habilidades())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la pantalla de habilidades
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.PLAYER_SKILLS:
                        print("Navegación a habilidades exitosa")
                        return True
            else:
                print(f"No estamos en la pantalla de acciones del jugador, estamos en: {current_screen.value}")
                return False
        
        print("No se pudo navegar a la sección de habilidades después de varios intentos")
        return False
    
    def select_training(self, max_attempts=5, wait_time=2.0):
        """
        Selecciona la opción de entrenamiento de habilidad.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se seleccionó correctamente, False en caso contrario
        """
        print("Seleccionando opción de entrenamiento de habilidad...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en la pantalla de entrenamiento, hemos terminado
            if current_screen == GameScreen.PLAYER_TRAINING:
                print("Ya estamos en la pantalla de entrenamiento")
                return True
            
            # Si estamos en la pantalla de habilidades, seleccionar entrenamiento
            if current_screen == GameScreen.PLAYER_SKILLS:
                print(f"Pantalla de habilidades detectada (intento {attempt+1})")
                
                # Buscar la opción de entrenamiento
                training_option = self.recognizer.find_element(ScreenElement.TRAINING_OPTION, screen)
                
                if training_option is not None:
                    # Si encontramos la opción, seleccionarla
                    print("Opción de entrenamiento encontrada, seleccionando...")
                    
                    # Ejecutar la secuencia para seleccionar entrenamiento
                    self.gamepad.execute_sequence(EFootballSequences.seleccionar_entrenamiento_habilidad())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la pantalla de entrenamiento
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.PLAYER_TRAINING:
                        print("Selección de entrenamiento exitosa")
                        return True
                else:
                    print("Opción de entrenamiento no encontrada, intentando con secuencia predefinida...")
                    # Si no encontramos la opción, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.seleccionar_entrenamiento_habilidad())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la pantalla de entrenamiento
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.PLAYER_TRAINING:
                        print("Selección de entrenamiento exitosa")
                        return True
            else:
                print(f"No estamos en la pantalla de habilidades, estamos en: {current_screen.value}")
                return False
        
        print("No se pudo seleccionar la opción de entrenamiento después de varios intentos")
        return False
    
    def perform_training(self, max_attempts=5, wait_time=2.0):
        """
        Realiza el entrenamiento de habilidad.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se realizó correctamente, False en caso contrario
        """
        print("Realizando entrenamiento de habilidad...")
        
        # Capturar la pantalla actual
        screen = self.recognizer.capture_screen()
        current_screen = self.recognizer.recognize_screen(screen)
        
        # Verificar que estamos en la pantalla de entrenamiento
        if current_screen != GameScreen.PLAYER_TRAINING:
            print(f"No estamos en la pantalla de entrenamiento, estamos en: {current_screen.value}")
            return False
        
        # Guardar una captura de pantalla antes del entrenamiento
        self.recognizer.save_screenshot("antes_entrenamiento.png", self.screenshots_dir)
        
        # Seleccionar la primera habilidad disponible (simulación)
        print("Seleccionando habilidad para entrenar...")
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time)
        
        # Confirmar la selección
        print("Confirmando selección de habilidad...")
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time * 2)  # Esperar un poco más para la animación
        
        # Guardar una captura de pantalla después del entrenamiento
        self.recognizer.save_screenshot("despues_entrenamiento.png", self.screenshots_dir)
        
        # Volver a la pantalla de habilidades
        print("Volviendo a la pantalla de habilidades...")
        self.gamepad.press_button(GamepadButton.B, duration=0.2)
        time.sleep(wait_time)
        
        # Verificar si hemos vuelto a la pantalla de habilidades
        new_screen = self.recognizer.recognize_screen()
        if new_screen == GameScreen.PLAYER_SKILLS:
            print("Entrenamiento realizado exitosamente")
            return True
        else:
            print(f"No se pudo volver a la pantalla de habilidades. Pantalla actual: {new_screen.value}")
            return False
    
    def train_player(self, player_name):
        """
        Ejecuta el proceso completo de entrenamiento de habilidad para un jugador específico.
        
        Args:
            player_name (str): Nombre del jugador a entrenar
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print(f"Iniciando proceso de entrenamiento para el jugador: {player_name}")
        
        # Paso 1: Navegar a Mi Equipo
        if not self.navigate_to_my_team():
            print("No se pudo navegar a Mi Equipo")
            return False
        
        # Paso 2: Buscar y seleccionar el jugador
        if not self.find_player_by_name(player_name):
            print(f"No se pudo encontrar al jugador: {player_name}")
            return False
        
        # Paso 3: Navegar a la sección de habilidades
        if not self.navigate_to_skills():
            print("No se pudo navegar a la sección de habilidades")
            return False
        
        # Paso 4: Seleccionar la opción de entrenamiento
        if not self.select_training():
            print("No se pudo seleccionar la opción de entrenamiento")
            return False
        
        # Paso 5: Realizar el entrenamiento
        if not self.perform_training():
            print("No se pudo realizar el entrenamiento")
            return False
        
        print(f"Proceso de entrenamiento para {player_name} completado exitosamente")
        return True
    
    def run(self, player_name):
        """
        Ejecuta el proceso completo de entrenamiento de habilidad para un jugador específico.
        
        Args:
            player_name (str): Nombre del jugador a entrenar
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print("Iniciando proceso automático para entrenar jugadores en eFootball...")
        
        # Guardar una captura de la pantalla inicial
        self.recognizer.save_screenshot("pantalla_inicial_entrenamiento.png", self.screenshots_dir)
        
        # Ejecutar el proceso de entrenamiento
        result = self.train_player(player_name)
        
        # Guardar una captura de la pantalla final
        self.recognizer.save_screenshot("pantalla_final_entrenamiento.png", self.screenshots_dir)
        
        if result:
            print(f"Proceso de entrenamiento para {player_name} completado exitosamente.")
        else:
            print(f"No se pudo completar el proceso de entrenamiento para {player_name}. Revise las capturas de pantalla para más detalles.")
        
        return result

# Ejemplo de uso
def main():
    """Función principal para ejecutar el entrenador de jugadores"""
    # Crear el controlador de gamepad
    gamepad = GamepadController()
    
    # Crear el reconocedor de pantalla
    recognizer = ScreenRecognizer()
    
    # Crear el entrenador de jugadores
    player_trainer = PlayerTrainer(gamepad, recognizer)
    
    # Nombre del jugador a entrenar
    player_name = "Raquel"
    
    # Ejecutar el proceso para entrenar al jugador
    player_trainer.run(player_name)

if __name__ == "__main__":
    print("Módulo para realizar entrenamientos de habilidad a jugadores en eFootball")
    print("Este módulo permite automatizar el proceso de entrenamiento de habilidades")
    print("navegando por los menús de Mi Equipo, seleccionando un jugador y realizando el entrenamiento.")
    print("\nEjecutando proceso...")
    main()
