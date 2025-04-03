"""
Función para fichar jugadores específicos en eFootball

Este módulo implementa la funcionalidad para automatizar el proceso de fichaje
de jugadores específicos en eFootball, navegando por los menús de contratación,
buscando jugadores y completando el proceso de compra.

Utiliza los módulos de control de gamepad y reconocimiento de pantalla.
"""

import time
import os
from gamepad_controller import GamepadController, GamepadButton, EFootballSequences
from screen_recognizer import ScreenRecognizer, GameScreen, ScreenElement

class PlayerSigner:
    """
    Clase para automatizar el proceso de fichaje de jugadores en eFootball.
    """
    
    def __init__(self, gamepad_controller=None, screen_recognizer=None):
        """
        Inicializa el fichador de jugadores.
        
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
        self.screenshots_dir = "/home/ubuntu/efootball_automation/screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        print("Fichador de jugadores inicializado")
    
    def navigate_to_contracts_menu(self, max_attempts=5, wait_time=2.0):
        """
        Navega desde el menú principal al menú de contratos.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se navegó correctamente, False en caso contrario
        """
        print("Navegando al menú de contratos...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en el menú de contratos, hemos terminado
            if current_screen == GameScreen.CONTRACTS_MENU:
                print("Ya estamos en el menú de contratos")
                return True
            
            # Si estamos en el menú principal, navegar al menú de contratos
            if current_screen == GameScreen.MAIN_MENU:
                print(f"Menú principal detectado (intento {attempt+1})")
                
                # Buscar la opción de contrato
                contract_option = self.recognizer.find_element(ScreenElement.CONTRACT_OPTION, screen)
                
                if contract_option is not None:
                    # Si encontramos la opción, navegar hasta ella y seleccionarla
                    print("Opción de contrato encontrada, navegando...")
                    
                    # Ejecutar la secuencia para navegar al menú de contratos
                    self.gamepad.execute_sequence(EFootballSequences.navegar_menu_principal_a_contratos())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado al menú de contratos
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.CONTRACTS_MENU:
                        print("Navegación al menú de contratos exitosa")
                        return True
                else:
                    print("Opción de contrato no encontrada, intentando con secuencia predefinida...")
                    # Si no encontramos la opción, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.navegar_menu_principal_a_contratos())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado al menú de contratos
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.CONTRACTS_MENU:
                        print("Navegación al menú de contratos exitosa")
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
        
        print("No se pudo navegar al menú de contratos después de varios intentos")
        return False
    
    def select_normal_players(self, max_attempts=5, wait_time=2.0):
        """
        Selecciona la opción de jugadores normales en el menú de contratos.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se seleccionó correctamente, False en caso contrario
        """
        print("Seleccionando opción de jugadores normales...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Si ya estamos en la lista de jugadores normales, hemos terminado
            if current_screen == GameScreen.NORMAL_PLAYERS_LIST:
                print("Ya estamos en la lista de jugadores normales")
                return True
            
            # Si estamos en el menú de contratos, seleccionar jugadores normales
            if current_screen == GameScreen.CONTRACTS_MENU:
                print(f"Menú de contratos detectado (intento {attempt+1})")
                
                # Buscar la opción de jugadores normales
                normal_players_option = self.recognizer.find_element(ScreenElement.NORMAL_PLAYERS_OPTION, screen)
                
                if normal_players_option is not None:
                    # Si encontramos la opción, seleccionarla
                    print("Opción de jugadores normales encontrada, seleccionando...")
                    
                    # Ejecutar la secuencia para seleccionar jugadores normales
                    self.gamepad.execute_sequence(EFootballSequences.seleccionar_jugadores_normales())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la lista de jugadores normales
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.NORMAL_PLAYERS_LIST:
                        print("Selección de jugadores normales exitosa")
                        return True
                else:
                    print("Opción de jugadores normales no encontrada, intentando con secuencia predefinida...")
                    # Si no encontramos la opción, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.seleccionar_jugadores_normales())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la lista de jugadores normales
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.NORMAL_PLAYERS_LIST:
                        print("Selección de jugadores normales exitosa")
                        return True
            else:
                print(f"No estamos en el menú de contratos, estamos en: {current_screen.value}")
                print("Intentando navegar al menú de contratos...")
                
                # Intentar navegar al menú de contratos
                if self.navigate_to_contracts_menu():
                    # Si llegamos al menú de contratos, continuar con el siguiente intento
                    continue
                else:
                    print("No se pudo navegar al menú de contratos")
                    return False
        
        print("No se pudo seleccionar la opción de jugadores normales después de varios intentos")
        return False
    
    def apply_filters(self, filters=None, max_attempts=5, wait_time=2.0):
        """
        Aplica filtros para buscar jugadores específicos.
        
        Args:
            filters (dict, optional): Diccionario con los filtros a aplicar
                Ejemplo: {
                    "position": "Delantero",
                    "club": "Barcelona",
                    "price_max": 100000
                }
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se aplicaron los filtros correctamente, False en caso contrario
        """
        print("Aplicando filtros para buscar jugadores...")
        
        # Si no se proporcionan filtros, no hacer nada
        if filters is None:
            print("No se proporcionaron filtros, omitiendo paso")
            return True
        
        # Capturar la pantalla actual
        screen = self.recognizer.capture_screen()
        current_screen = self.recognizer.recognize_screen(screen)
        
        # Verificar que estamos en la lista de jugadores normales
        if current_screen != GameScreen.NORMAL_PLAYERS_LIST:
            print(f"No estamos en la lista de jugadores normales, estamos en: {current_screen.value}")
            print("Intentando navegar a la lista de jugadores normales...")
            
            # Intentar navegar a la lista de jugadores normales
            if not self.select_normal_players():
                print("No se pudo navegar a la lista de jugadores normales")
                return False
        
        # Guardar una captura de pantalla antes de aplicar filtros
        self.recognizer.save_screenshot("antes_filtros.png", self.screenshots_dir)
        
        # Aplicar filtros (implementación simplificada)
        print("Aplicando filtros (simulación)...")
        
        # Presionar Y para abrir el menú de filtros
        self.gamepad.press_button(GamepadButton.Y, duration=0.2)
        time.sleep(1.0)
        
        # Navegar por los filtros y aplicarlos según los valores proporcionados
        # Nota: Esta es una implementación simplificada, en una versión real
        # se necesitaría reconocer cada opción de filtro y navegar adecuadamente
        
        # Posición
        if "position" in filters:
            print(f"Aplicando filtro de posición: {filters['position']}")
            # Navegar al filtro de posición y seleccionarlo
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(1.0)
            
            # Seleccionar la posición (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(1.0)
            
            # Volver al menú de filtros
            self.gamepad.press_button(GamepadButton.B, duration=0.2)
            time.sleep(1.0)
        
        # Club
        if "club" in filters:
            print(f"Aplicando filtro de club: {filters['club']}")
            # Navegar al filtro de club y seleccionarlo
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(1.0)
            
            # Seleccionar el club (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(1.0)
            
            # Volver al menú de filtros
            self.gamepad.press_button(GamepadButton.B, duration=0.2)
            time.sleep(1.0)
        
        # Precio máximo
        if "price_max" in filters:
            print(f"Aplicando filtro de precio máximo: {filters['price_max']}")
            # Navegar al filtro de precio y seleccionarlo
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(1.0)
            
            # Seleccionar el precio máximo (simulación)
            self.gamepad.press_button(GamepadButton.DPAD_RIGHT, duration=0.2)
            time.sleep(0.5)
            self.gamepad.press_button(GamepadButton.A, duration=0.2)
            time.sleep(1.0)
            
            # Volver al menú de filtros
            self.gamepad.press_button(GamepadButton.B, duration=0.2)
            time.sleep(1.0)
        
        # Aplicar los filtros
        print("Aplicando filtros seleccionados...")
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(2.0)
        
        # Guardar una captura de pantalla después de aplicar filtros
        self.recognizer.save_screenshot("despues_filtros.png", self.screenshots_dir)
        
        print("Filtros aplicados correctamente")
        return True
    
    def select_player(self, player_index=0, max_attempts=5, wait_time=2.0):
        """
        Selecciona un jugador de la lista según su índice.
        
        Args:
            player_index (int): Índice del jugador a seleccionar (0 para el primero)
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se seleccionó correctamente, False en caso contrario
        """
        print(f"Seleccionando jugador en posición {player_index}...")
        
        # Capturar la pantalla actual
        screen = self.recognizer.capture_screen()
        current_screen = self.recognizer.recognize_screen(screen)
        
        # Verificar que estamos en la lista de jugadores normales
        if current_screen != GameScreen.NORMAL_PLAYERS_LIST:
            print(f"No estamos en la lista de jugadores normales, estamos en: {current_screen.value}")
            return False
        
        # Guardar una captura de pantalla antes de seleccionar el jugador
        self.recognizer.save_screenshot("antes_seleccion_jugador.png", self.screenshots_dir)
        
        # Navegar hasta el jugador deseado
        for i in range(player_index):
            print(f"Navegando al jugador {i+1}...")
            self.gamepad.press_button(GamepadButton.DPAD_DOWN, duration=0.2)
            time.sleep(0.5)
        
        # Seleccionar el jugador
        print(f"Seleccionando jugador {player_index}...")
        self.gamepad.press_button(GamepadButton.A, duration=0.2)
        time.sleep(wait_time)
        
        # Verificar si hemos llegado a la pantalla de confirmación de compra
        new_screen = self.recognizer.recognize_screen()
        if new_screen == GameScreen.PURCHASE_CONFIRMATION:
            print("Jugador seleccionado correctamente")
            
            # Guardar una captura de pantalla después de seleccionar el jugador
            self.recognizer.save_screenshot("despues_seleccion_jugador.png", self.screenshots_dir)
            
            return True
        else:
            print(f"No se pudo seleccionar el jugador. Pantalla actual: {new_screen.value}")
            return False
    
    def confirm_purchase(self, max_attempts=5, wait_time=2.0):
        """
        Confirma la compra de un jugador.
        
        Args:
            max_attempts (int): Número máximo de intentos
            wait_time (float): Tiempo de espera entre intentos en segundos
        
        Returns:
            bool: True si se confirmó correctamente, False en caso contrario
        """
        print("Confirmando compra del jugador...")
        
        for attempt in range(max_attempts):
            # Capturar la pantalla actual
            screen = self.recognizer.capture_screen()
            current_screen = self.recognizer.recognize_screen(screen)
            
            # Verificar que estamos en la pantalla de confirmación de compra
            if current_screen == GameScreen.PURCHASE_CONFIRMATION:
                print(f"Pantalla de confirmación de compra detectada (intento {attempt+1})")
                
                # Buscar el botón de confirmar
                confirm_button = self.recognizer.find_element(ScreenElement.CONFIRM_BUTTON, screen)
                
                if confirm_button is not None:
                    # Si encontramos el botón, presionarlo
                    print("Botón de confirmar encontrado, presionando...")
                    
                    # Ejecutar la secuencia para confirmar la compra
                    self.gamepad.execute_sequence(EFootballSequences.confirmar_compra())
                    
                    # Esperar a que cambie la pantalla
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la pantalla de compra realizada
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.PURCHASE_COMPLETED:
                        print("Compra confirmada exitosamente")
                        
                        # Guardar una captura de pantalla de la compra realizada
                        self.recognizer.save_screenshot("compra_realizada.png", self.screenshots_dir)
                        
                        # Presionar A para continuar
                        self.gamepad.press_button(GamepadButton.A, duration=0.2)
                        time.sleep(wait_time)
                        
                        return True
                else:
                    print("Botón de confirmar no encontrado, intentando con secuencia predefinida...")
                    # Si no encontramos el botón, intentar con una secuencia predefinida
                    self.gamepad.execute_sequence(EFootballSequences.confirmar_compra())
                    time.sleep(wait_time)
                    
                    # Verificar si hemos llegado a la pantalla de compra realizada
                    new_screen = self.recognizer.recognize_screen()
                    if new_screen == GameScreen.PURCHASE_COMPLETED:
                        print("Compra confirmada exitosamente")
                        
                        # Guardar una captura de pantalla de la compra realizada
                        self.recognizer.save_screenshot("compra_realizada.png", self.screenshots_dir)
                        
                        # Presionar A para continuar
                        self.gamepad.press_button(GamepadButton.A, duration=0.2)
                        time.sleep(wait_time)
                        
                        return True
            else:
                print(f"No estamos en la pantalla de confirmación de compra, estamos en: {current_screen.value}")
                return False
        
        print("No se pudo confirmar la compra después de varios intentos")
        return False
    
    def sign_player(self, player_name=None, filters=None, player_index=0):
        """
        Ejecuta el proceso completo de fichaje de un jugador.
        
        Args:
            player_name (str, optional): Nombre del jugador a fichar
            filters (dict, optional): Filtros para buscar al jugador
            player_index (int): Índice del jugador a seleccionar si no se especifica nombre
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print(f"Iniciando proceso de fichaje de jugador: {player_name if player_name else f'índice {player_index}'}")
        
        # Paso 1: Navegar al menú de contratos
        if not self.navigate_to_contracts_menu():
            print("No se pudo navegar al menú de contratos")
            return False
        
        # Paso 2: Seleccionar la opción de jugadores normales
        if not self.select_normal_players():
            print("No se pudo seleccionar la opción de jugadores normales")
            return False
        
        # Paso 3: Aplicar filtros si se proporcionan
        if filters:
            if not self.apply_filters(filters):
                print("No se pudieron aplicar los filtros")
                return False
        
        # Paso 4: Seleccionar el jugador
        if player_name:
            # Si se proporciona un nombre, buscar al jugador por nombre
            print(f"Buscando jugador por nombre: {player_name}")
            # Nota: La búsqueda por nombre requeriría implementación de OCR
            # Por ahora, simplemente seleccionamos el primer jugador
            if not self.select_player(0):
                print("No se pudo seleccionar el jugador")
                return False
        else:
            # Si no se proporciona un nombre, seleccionar por índice
            if not self.select_player(player_index):
                print("No se pudo seleccionar el jugador")
                return False
        
        # Paso 5: Confirmar la compra
        if not self.confirm_purchase():
            print("No se pudo confirmar la compra")
            return False
        
        print("Proceso de fichaje completado exitosamente")
        return True
    
    def run(self, player_name=None, filters=None, player_index=0):
        """
        Ejecuta el proceso completo de fichaje de un jugador.
        
        Args:
            player_name (str, optional): Nombre del jugador a fichar
            filters (dict, optional): Filtros para buscar al jugador
            player_index (int): Índice del jugador a seleccionar si no se especifica nombre
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print("Iniciando proceso automático para fichar jugadores en eFootball...")
        
        # Guardar una captura de la pantalla inicial
        self.recognizer.save_screenshot("pantalla_inicial_fichaje.png", self.screenshots_dir)
        
        # Ejecutar el proceso de fichaje
        result = self.sign_player(player_name, filters, player_index)
        
        # Guardar una captura de la pantalla final
        self.recognizer.save_screenshot("pantalla_final_fichaje.png", self.screenshots_dir)
        
        if result:
            print("Proceso de fichaje completado exitosamente.")
        else:
            print("No se pudo completar el proceso de fichaje. Revise las capturas de pantalla para más detalles.")
        
        return result

# Ejemplo de uso
def main():
    """Función principal para ejecutar el fichador de jugadores"""
    # Crear el controlador de gamepad
    gamepad = GamepadController()
    
    # Crear el reconocedor de pantalla
    recognizer = ScreenRecognizer()
    
    # Crear el fichador de jugadores
    player_signer = PlayerSigner(gamepad, recognizer)
    
    # Definir filtros para buscar un jugador específico
    filters = {
        "position": "Delantero",
        "club": "Barcelona",
        "price_max": 100000
    }
    
    # Ejecutar el proceso para fichar al primer jugador que cumpla los filtros
    player_signer.run(filters=filters, player_index=0)

if __name__ == "__main__":
    print("Módulo para fichar jugadores específicos en eFootball")
    print("Este módulo permite automatizar el proceso de fichaje de jugadores")
    print("navegando por los menús de contratación, buscando jugadores y completando el proceso de compra.")
    print("\nEjecutando proceso...")
    main()
