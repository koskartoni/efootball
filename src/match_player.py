"""
Función para jugar partidos contra la CPU en eFootball

Este módulo implementa la funcionalidad para automatizar el proceso de jugar
partidos contra la CPU en eFootball, navegando por los menús de partidos,
configurando y jugando partidos hasta cumplir el objetivo del evento.

Utiliza los módulos de control de gamepad y reconocimiento de pantalla.
"""

import time
import os
import random
from gamepad_controller import GamepadController, GamepadButton, EFootballSequences
from screen_recognizer import ScreenRecognizer, GameScreen, ScreenElement

class MatchPlayer:
    """
    Clase para automatizar el proceso de jugar partidos contra la CPU en eFootball.
    """
    
    def __init__(self, gamepad_controller=None, screen_recognizer=None):
        """
        Inicializa el jugador de partidos.
        
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
        self.screenshots_dir = "/home/ubuntu/efootball_automation/screenshots/matches"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        print("Jugador de partidos inicializado")
    
    def navigate_to_match_menu(self, max_attempts=5, wait_time=2.0):
        """
        Navega desde el menú principal al menú de partidos.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se navegó correctamente, False en caso contrario
        """
        print("Navegando al menú de partidos...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en el menú de partidos, hemos terminado
            if current_screen == GameScreen.MATCH_MENU:
                print("Ya estamos en el menú de partidos")
                return True
            
            # Si estamos en el menú principal, navegar al menú de partidos
            if current_screen == GameScreen.MAIN_MENU:
                print(f"Menú principal detectado (intento {attempt+1})")
                
                # Buscar la opción de partido
                match_option = self.recognizer.find_element(ScreenElement.MATCH_OPTION, screen)
                
                if match_option is not None:
                    # Si encontramos la opción, navegar hasta ella y seleccionarla
                    print("Opción de partido encontrada, navegando...")
                    
                    # Ejecutar la secuencia para navegar al menú de partidos
                    self.gamepad.execute_sequence(EFootballSequences.navegar_menu_principal_a_partido())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado al menú de partidos
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.MATCH_MENU:
                        print("Navegación al menú de partidos exitosa")
                        return True
                else:
                    print("Opción de partido no encontrada, intentando con secuencia predefinida...")
                    # Si no encontramos la opción, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.navegar_menu_principal_a_partido())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado al menú de partidos
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.MATCH_MENU:
                        print("Navegación al menú de partidos exitosa")
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
        
        print("No se pudo navegar al menú de partidos después de varios intentos")
        return False
    
    def select_cpu_match(self, event_mode=True, max_attempts=5, wait_time=2.0):
        """
        Selecciona un partido contra la CPU, opcionalmente en modo evento.
        
        Args:
            event_mode (bool): Si True, intenta seleccionar un partido de evento
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se seleccionó correctamente, False en caso contrario
        """
        print(f"Seleccionando partido contra CPU{' (modo evento)' if event_mode else ''}...")
        
        # Capturar la pantalla actual
        screen = self.recognizer.capture_screen()
        current_screen = self.recognizer.recognize_screen(screen)
        
        # Verificar que estamos en el menú de partidos
        if current_screen != GameScreen.MATCH_MENU:
            print(f"No estamos en el menú de partidos, estamos en: {current_screen.value}")
            print("Intentando navegar al menú de partidos...")
            
            if not self.navigate_to_match_menu():
                print("No se pudo navegar al menú de partidos")
                return False
        
        # Guardar una captura de pantalla antes de seleccionar el partido
        self.recognizer.save_screenshot("menu_partidos.png", self.screenshots_dir)
        
        # Seleccionar el modo de partido (simulación)
        if event_mode:
            print("Seleccionando modo evento...")
            # Navegar al modo evento (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_RIGHT, duration=0.2)
            time.sleep(wait_time)
            self.gamepad.press_button(GamepadButton.DPAD_RIGHT, duration=0.2)
            time.sleep(wait_time)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(wait_time * 2)
        else:
            print("Seleccionando partido amistoso contra CPU...")
            # Navegar al modo amistoso (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(wait_time)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(wait_time * 2)
        
        # Seleccionar CPU como oponente (simulación)
        print("Seleccionando CPU como oponente...")
        self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
        time.sleep(wait_time)
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time * 2)
        
        # Confirmar selección
        print("Confirmando selección...")
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time * 2)
        
        # Guardar una captura de pantalla después de seleccionar el partido
        self.recognizer.save_screenshot("partido_seleccionado.png", self.screenshots_dir)
        
        print("Partido contra CPU seleccionado correctamente")
        return True
    
    def configure_match(self, difficulty="normal", max_attempts=5, wait_time=2.0):
        """
        Configura los parámetros del partido.
        
        Args:
            difficulty (str): Dificultad del partido ("easy", "normal", "hard")
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se configuró correctamente, False en caso contrario
        """
        print(f"Configurando partido con dificultad {difficulty}...")
        
        # Guardar una captura de pantalla antes de configurar el partido
        self.recognizer.save_screenshot("antes_configuracion.png", self.screenshots_dir)
        
        # Configurar dificultad (simulación)
        print(f"Configurando dificultad a {difficulty}...")
        
        # Navegar a la opción de dificultad (simulación)
        self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
        time.sleep(wait_time)
        self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
        time.sleep(wait_time)
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time)
        
        # Seleccionar dificultad según el parámetro
        if difficulty == "easy":
            # Navegar a dificultad fácil (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_UP, duration=0.2)
            time.sleep(wait_time)
        elif difficulty == "hard":
            # Navegar a dificultad difícil (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(wait_time)
        # Para "normal" no hacemos nada, asumimos que es la opción por defecto
        
        # Confirmar selección de dificultad
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time)
        
        # Confirmar configuración y comenzar partido
        print("Confirmando configuración y comenzando partido...")
        self.gamepad.press_button(GamepadButton.START, duration=0.2)
        time.sleep(wait_time * 3)  # Esperar más tiempo para la carga del partido
        
        # Guardar una captura de pantalla después de configurar el partido
        self.recognizer.save_screenshot("despues_configuracion.png", self.screenshots_dir)
        
        print("Partido configurado correctamente")
        return True
    
    def play_match(self, duration_minutes=5, max_wait_time=600):
        """
        Juega un partido contra la CPU.
        
        Args:
            duration_minutes (int): Duración aproximada del partido en minutos
            max_wait_time (int): Tiempo máximo de espera para que termine el partido en segundos
        
        Returns:
            bool: True si se jugó correctamente, False en caso contrario
        """
        print(f"Jugando partido contra CPU (duración aproximada: {duration_minutes} minutos)...")
        
        # Guardar una captura de pantalla al inicio del partido
        self.recognizer.save_screenshot("inicio_partido.png", self.screenshots_dir)
        
        # Calcular el tiempo de juego en segundos
        play_time = duration_minutes * 60
        
        # Tiempo de inicio
        start_time = time.time()
        
        # Simular juego presionando botones aleatorios
        print("Simulando juego...")
        
        # Lista de botones comunes durante el juego
        game_buttons = [
            GamepadButton.A,  # Pase corto
            GamepadButton.X,  # Pase largo
            GamepadButton.B,  # Tiro
            GamepadButton.Y,  # A través
            GamepadButton.RB,  # Sprint
            GamepadButton.LB  # Presión
        ]
        
        # Jugar hasta que se cumpla el tiempo o se detecte el fin del partido
        while time.time() - start_time < play_time and time.time() - start_time < max_wait_time:
            # Presionar un botón aleatorio
            random_button = random.choice(game_buttons)
            self.gamepad.press_button(random_button, duration=random.uniform(0.1, 0.3))
            
            # Mover el joystick izquierdo aleatoriamente
            x_value = random.randint(-32768, 32767)
            y_value = random.randint(-32768, 32767)
            self.gamepad.move_joystick("left", x_value, y_value, duration=random.uniform(0.2, 0.5))
            
            # Esperar un tiempo aleatorio entre acciones
            time.sleep(random.uniform(0.1, 0.5))
            
            # Cada 30 segundos, verificar si el partido ha terminado
            if (time.time() - start_time) % 30 < 1:
                # Capturar la pantalla actual
                screen = self.recognizer.capture_screen()
                current_screen = self.recognizer.recognize_screen(screen)
                
                # Si ya no estamos en el partido, asumir que ha terminado
                if current_screen != GameScreen.MATCH_MENU:
                    print("Partido terminado (detectado cambio de pantalla)")
                    break
        
        # Si llegamos aquí por tiempo, presionar START para pausar y abandonar
        if time.time() - start_time >= play_time and time.time() - start_time < max_wait_time:
            print("Tiempo de juego cumplido, abandonando partido...")
            
            # Pausar el partido
            self.gamepad.press_button(GamepadButton.START, duration=0.2)
            time.sleep(2.0)
            
            # Navegar a la opción de abandonar (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(1.0)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(1.0)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(2.0)
            
            # Confirmar abandono
            self.gamepad.press_button(GamepadButton.DPAD_LEFT, duration=0.2)
            time.sleep(1.0)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(3.0)
        
        # Guardar una captura de pantalla al final del partido
        self.recognizer.save_screenshot("fin_partido.png", self.screenshots_dir)
        
        # Manejar pantallas post-partido (simulación)
        print("Manejando pantallas post-partido...")
        
        # Presionar A varias veces para pasar pantallas de resultados, recompensas, etc.
        for _ in range(5):
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(2.0)
        
        print("Partido jugado correctamente")
        return True
    
    def check_event_completion(self, max_attempts=5, wait_time=2.0):
        """
        Verifica si se ha completado el objetivo del evento.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se ha completado el objetivo, False en caso contrario
        """
        print("Verificando si se ha completado el objetivo del evento...")
        
        # Guardar una captura de pantalla para verificación
        self.recognizer.save_screenshot("verificacion_objetivo.png", self.screenshots_dir)
        
        # Nota: En una implementación real, aquí se utilizaría OCR para reconocer
        # el texto que indica el progreso del evento. Como es una simulación,
        # simplemente asumimos que no se ha completado aún.
        
        # Simulación: Asumir que no se ha completado el objetivo
        completed = False
        
        if completed:
            print("¡Objetivo del evento completado!")
        else:
            print("Objetivo del evento aún no completado")
        
        return completed
    
    def play_matches_until_completion(self, max_matches=10, event_mode=True, difficulty="normal"):
        """
        Juega partidos contra la CPU hasta completar el objetivo del evento.
        
        Args:
            max_matches (int): Número máximo de partidos a jugar
            event_mode (bool): Si True, intenta seleccionar partidos de evento
            difficulty (str): Dificultad de los partidos ("easy", "normal", "hard")
        
        Returns:
            bool: True si se completó el objetivo, False en caso contrario
        """
        print(f"Iniciando proceso para jugar hasta {max_matches} partidos contra CPU...")
        
        matches_played = 0
        objective_completed = False
        
        while matches_played < max_matches and not objective_completed:
            print(f"\n=== Partido {matches_played + 1}/{max_matches} ===")
            
            # Paso 1: Navegar al menú de partidos
            if not self.navigate_to_match_menu():
                print("No se pudo navegar al menú de partidos")
                return False
            
            # Paso 2: Seleccionar partido contra CPU
            if not self.select_cpu_match(event_mode):
                print("No se pudo seleccionar el partido contra CPU")
                return False
            
            # Paso 3: Configurar el partido
            if not self.configure_match(difficulty):
                print("No se pudo configurar el partido")
                return False
            
            # Paso 4: Jugar el partido
            if not self.play_match():
                print("No se pudo jugar el partido correctamente")
                return False
            
            # Incrementar contador de partidos jugados
            matches_played += 1
            
            # Paso 5: Verificar si se ha completado el objetivo
            objective_completed = self.check_event_completion()
            
            if objective_completed:
                print(f"¡Objetivo completado después de {matches_played} partidos!")
                break
            
            print(f"Objetivo no completado aún. Partidos jugados: {matches_played}/{max_matches}")
            
            # Esperar un momento antes del siguiente partido
            time.sleep(5.0)
        
        if objective_completed:
            print("Proceso completado exitosamente: objetivo del evento alcanzado")
            return True
        else:
            print(f"Se alcanzó el límite de {max_matches} partidos sin completar el objetivo")
            return False
    
    def run(self, max_matches=10, event_mode=True, difficulty="normal"):
        """
        Ejecuta el proceso completo de jugar partidos contra la CPU hasta completar el objetivo.
        
        Args:
            max_matches (int): Número máximo de partidos a jugar
            event_mode (bool): Si True, intenta seleccionar partidos de evento
            difficulty (str): Dificultad de los partidos ("easy", "normal", "hard")
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print("Iniciando proceso automático para jugar partidos en eFootball...")
        
        # Guardar una captura de la pantalla inicial
        self.recognizer.save_screenshot("pantalla_inicial_partidos.png", self.screenshots_dir)
        
        # Ejecutar el proceso de jugar partidos hasta completar el objetivo
        result = self.play_matches_until_completion(max_matches, event_mode, difficulty)
        
        # Guardar una captura de la pantalla final
        self.recognizer.save_screenshot("pantalla_final_partidos.png", self.screenshots_dir)
        
        if result:
            print("Proceso de jugar partidos completado exitosamente: objetivo alcanzado.")
        else:
            print("No se pudo completar el objetivo. Revise las capturas de pantalla para más detalles.")
        
        return result

# Ejemplo de uso
def main():
    """Función principal para ejecutar el jugador de partidos"""
    # Crear el controlador de gamepad
    gamepad = GamepadController()
    
    # Crear el reconocedor de pantalla
    recognizer = ScreenRecognizer()
    
    # Crear el jugador de partidos
    match_player = MatchPlayer(gamepad, recognizer)
    
    # Configuración
    max_matches = 5
    event_mode = True
    difficulty = "normal"
    
    # Ejecutar el proceso para jugar partidos hasta completar el objetivo
    match_player.run(max_matches, event_mode, difficulty)

if __name__ == "__main__":
    print("Módulo para jugar partidos contra la CPU en eFootball")
    print("Este módulo permite automatizar el proceso de jugar partidos")
    print("contra la CPU hasta cumplir el objetivo del evento.")
    print("\nEjecutando proceso...")
    main()
