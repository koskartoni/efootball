"""
Script de pruebas para la aplicación de automatización de eFootball

Este script realiza pruebas de las diferentes funcionalidades de la aplicación
para verificar su correcto funcionamiento y detectar posibles errores.
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# Añadir el directorio src al path para poder importar los módulos
sys.path.append('/home/ubuntu/efootball_automation/src')

# Importar los módulos a probar
from gamepad_controller import GamepadController, GamepadButton, GamepadType
from screen_recognizer import ScreenRecognizer, GameScreen, ScreenElement
from banner_skipper import BannerSkipper
from player_signer import PlayerSigner
from player_trainer import PlayerTrainer
from match_player import MatchPlayer
from main import EFootballAutomation

class TestGamepadController(unittest.TestCase):
    """Pruebas para el módulo de control de gamepad"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.gamepad = GamepadController()
    
    def test_initialization(self):
        """Prueba la inicialización del controlador de gamepad"""
        self.assertIsNotNone(self.gamepad)
        self.assertEqual(self.gamepad.gamepad_type, GamepadType.XBOX360)
    
    def test_button_mapping(self):
        """Prueba el mapeo de botones"""
        self.assertIn(GamepadButton.A, self.gamepad.button_mapping)
        self.assertIn(GamepadButton.B, self.gamepad.button_mapping)
        self.assertIn(GamepadButton.X, self.gamepad.button_mapping)
        self.assertIn(GamepadButton.Y, self.gamepad.button_mapping)
    
    @patch('vgamepad.VX360Gamepad')
    def test_press_button(self, mock_gamepad):
        """Prueba la función de presionar botón"""
        # Configurar el mock
        instance = mock_gamepad.return_value
        
        # Crear el controlador con el mock
        gamepad = GamepadController()
        
        # Probar presionar un botón
        gamepad.press_button(GamepadButton.A, duration=0.1)
        
        # Verificar que se llamaron los métodos correctos
        instance.press_button.assert_called_once()
        instance.update.assert_called()
    
    @patch('vgamepad.VX360Gamepad')
    def test_move_joystick(self, mock_gamepad):
        """Prueba la función de mover joystick"""
        # Configurar el mock
        instance = mock_gamepad.return_value
        
        # Crear el controlador con el mock
        gamepad = GamepadController()
        
        # Probar mover el joystick
        gamepad.move_joystick("left", x_value=32767, y_value=0, duration=0.1)
        
        # Verificar que se llamaron los métodos correctos
        instance.left_joystick.assert_called_once_with(x_value=32767, y_value=0)
        instance.update.assert_called()

class TestScreenRecognizer(unittest.TestCase):
    """Pruebas para el módulo de reconocimiento de pantalla"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.recognizer = ScreenRecognizer()
    
    def test_initialization(self):
        """Prueba la inicialización del reconocedor de pantalla"""
        self.assertIsNotNone(self.recognizer)
        self.assertIsNotNone(self.recognizer.templates_dir)
    
    @patch('cv2.imread')
    def test_load_templates(self, mock_imread):
        """Prueba la carga de plantillas"""
        # Configurar el mock para que devuelva una imagen simulada
        mock_imread.return_value = MagicMock()
        
        # Crear un reconocedor con el mock
        recognizer = ScreenRecognizer()
        
        # Verificar que se intentó cargar al menos una plantilla
        mock_imread.assert_called()
    
    @patch('pyautogui.screenshot')
    def test_capture_screen(self, mock_screenshot):
        """Prueba la captura de pantalla"""
        # Configurar el mock para que devuelva una captura simulada
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_screenshot.return_value = mock_img
        
        # Probar capturar la pantalla
        with patch('numpy.array'), patch('cv2.cvtColor'):
            result = self.recognizer.capture_screen()
        
        # Verificar que se llamó a screenshot
        mock_screenshot.assert_called_once()

class TestBannerSkipper(unittest.TestCase):
    """Pruebas para el módulo de saltar banners"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear mocks para los componentes
        self.mock_gamepad = MagicMock(spec=GamepadController)
        self.mock_recognizer = MagicMock(spec=ScreenRecognizer)
        
        # Crear el saltador de banners con los mocks
        self.banner_skipper = BannerSkipper(self.mock_gamepad, self.mock_recognizer)
    
    def test_initialization(self):
        """Prueba la inicialización del saltador de banners"""
        self.assertIsNotNone(self.banner_skipper)
        self.assertEqual(self.banner_skipper.gamepad, self.mock_gamepad)
        self.assertEqual(self.banner_skipper.recognizer, self.mock_recognizer)
    
    def test_skip_welcome_screen(self):
        """Prueba la función de saltar la pantalla de bienvenida"""
        # Configurar el mock del reconocedor para simular la pantalla de bienvenida
        self.mock_recognizer.capture_screen.return_value = MagicMock()
        self.mock_recognizer.recognize_screen.side_effect = [
            GameScreen.WELCOME,  # Primera llamada: estamos en la pantalla de bienvenida
            GameScreen.BANNER    # Segunda llamada: avanzamos a un banner
        ]
        
        # Probar saltar la pantalla de bienvenida
        result = self.banner_skipper.skip_welcome_screen(max_attempts=1, wait_time=0.1)
        
        # Verificar que se llamaron los métodos correctos
        self.mock_recognizer.capture_screen.assert_called()
        self.mock_recognizer.recognize_screen.assert_called()
        self.mock_gamepad.press_button.assert_called_once()
        self.assertTrue(result)
    
    def test_skip_all_banners(self):
        """Prueba la función de saltar todos los banners"""
        # Configurar los mocks para simular el proceso completo
        self.mock_recognizer.capture_screen.return_value = MagicMock()
        
        # Simular que primero estamos en la pantalla de bienvenida, luego en un banner, y finalmente en el menú principal
        self.mock_recognizer.recognize_screen.side_effect = [
            GameScreen.WELCOME,  # Para skip_welcome_screen
            GameScreen.BANNER,   # Para skip_welcome_screen (después de presionar A)
            GameScreen.BANNER,   # Primera iteración de skip_all_banners
            GameScreen.MAIN_MENU # Segunda iteración de skip_all_banners
        ]
        
        # Configurar el mock para detectar un banner
        self.mock_recognizer.detect_banner_type.return_value = "anuncio"
        
        # Configurar el mock para encontrar el botón X
        self.mock_recognizer.find_element.return_value = (100, 100, 50, 50)
        
        # Probar saltar todos los banners
        with patch.object(self.banner_skipper, 'skip_welcome_screen', return_value=True):
            result = self.banner_skipper.skip_all_banners(max_banners=2, timeout=1)
        
        # Verificar que se llamaron los métodos correctos
        self.mock_recognizer.capture_screen.assert_called()
        self.mock_recognizer.recognize_screen.assert_called()
        self.assertTrue(result)

class TestPlayerSigner(unittest.TestCase):
    """Pruebas para el módulo de fichar jugadores"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear mocks para los componentes
        self.mock_gamepad = MagicMock(spec=GamepadController)
        self.mock_recognizer = MagicMock(spec=ScreenRecognizer)
        
        # Crear el fichador de jugadores con los mocks
        self.player_signer = PlayerSigner(self.mock_gamepad, self.mock_recognizer)
    
    def test_initialization(self):
        """Prueba la inicialización del fichador de jugadores"""
        self.assertIsNotNone(self.player_signer)
        self.assertEqual(self.player_signer.gamepad, self.mock_gamepad)
        self.assertEqual(self.player_signer.recognizer, self.mock_recognizer)
    
    def test_navigate_to_contracts_menu(self):
        """Prueba la navegación al menú de contratos"""
        # Configurar el mock del reconocedor
        self.mock_recognizer.capture_screen.return_value = MagicMock()
        self.mock_recognizer.recognize_screen.side_effect = [
            GameScreen.MAIN_MENU,     # Primera llamada: estamos en el menú principal
            GameScreen.CONTRACTS_MENU # Segunda llamada: llegamos al menú de contratos
        ]
        
        # Configurar el mock para encontrar la opción de contrato
        self.mock_recognizer.find_element.return_value = (100, 100, 50, 50)
        
        # Probar navegar al menú de contratos
        result = self.player_signer.navigate_to_contracts_menu(max_attempts=1, wait_time=0.1)
        
        # Verificar que se llamaron los métodos correctos
        self.mock_recognizer.capture_screen.assert_called()
        self.mock_recognizer.recognize_screen.assert_called()
        self.mock_gamepad.execute_sequence.assert_called_once()
        self.assertTrue(result)

class TestPlayerTrainer(unittest.TestCase):
    """Pruebas para el módulo de entrenar jugadores"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear mocks para los componentes
        self.mock_gamepad = MagicMock(spec=GamepadController)
        self.mock_recognizer = MagicMock(spec=ScreenRecognizer)
        
        # Crear el entrenador de jugadores con los mocks
        self.player_trainer = PlayerTrainer(self.mock_gamepad, self.mock_recognizer)
    
    def test_initialization(self):
        """Prueba la inicialización del entrenador de jugadores"""
        self.assertIsNotNone(self.player_trainer)
        self.assertEqual(self.player_trainer.gamepad, self.mock_gamepad)
        self.assertEqual(self.player_trainer.recognizer, self.mock_recognizer)
    
    def test_navigate_to_my_team(self):
        """Prueba la navegación a Mi Equipo"""
        # Configurar el mock del reconocedor
        self.mock_recognizer.capture_screen.return_value = MagicMock()
        self.mock_recognizer.recognize_screen.side_effect = [
            GameScreen.MAIN_MENU, # Primera llamada: estamos en el menú principal
            GameScreen.MY_TEAM    # Segunda llamada: llegamos a Mi Equipo
        ]
        
        # Configurar el mock para encontrar la opción de Mi Equipo
        self.mock_recognizer.find_element.return_value = (100, 100, 50, 50)
        
        # Probar navegar a Mi Equipo
        result = self.player_trainer.navigate_to_my_team(max_attempts=1, wait_time=0.1)
        
        # Verificar que se llamaron los métodos correctos
        self.mock_recognizer.capture_screen.assert_called()
        self.mock_recognizer.recognize_screen.assert_called()
        self.mock_gamepad.execute_sequence.assert_called_once()
        self.assertTrue(result)

class TestMatchPlayer(unittest.TestCase):
    """Pruebas para el módulo de jugar partidos"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear mocks para los componentes
        self.mock_gamepad = MagicMock(spec=GamepadController)
        self.mock_recognizer = MagicMock(spec=ScreenRecognizer)
        
        # Crear el jugador de partidos con los mocks
        self.match_player = MatchPlayer(self.mock_gamepad, self.mock_recognizer)
    
    def test_initialization(self):
        """Prueba la inicialización del jugador de partidos"""
        self.assertIsNotNone(self.match_player)
        self.assertEqual(self.match_player.gamepad, self.mock_gamepad)
        self.assertEqual(self.match_player.recognizer, self.mock_recognizer)
    
    def test_navigate_to_match_menu(self):
        """Prueba la navegación al menú de partidos"""
        # Configurar el mock del reconocedor
        self.mock_recognizer.capture_screen.return_value = MagicMock()
        self.mock_recognizer.recognize_screen.side_effect = [
            GameScreen.MAIN_MENU,  # Primera llamada: estamos en el menú principal
            GameScreen.MATCH_MENU  # Segunda llamada: llegamos al menú de partidos
        ]
        
        # Configurar el mock para encontrar la opción de partido
        self.mock_recognizer.find_element.return_value = (100, 100, 50, 50)
        
        # Probar navegar al menú de partidos
        result = self.match_player.navigate_to_match_menu(max_attempts=1, wait_time=0.1)
        
        # Verificar que se llamaron los métodos correctos
        self.mock_recognizer.capture_screen.assert_called()
        self.mock_recognizer.recognize_screen.assert_called()
        self.mock_gamepad.execute_sequence.assert_called_once()
        self.assertTrue(result)

class TestEFootballAutomation(unittest.TestCase):
    """Pruebas para la aplicación principal"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Parchear las clases de los componentes
        with patch('gamepad_controller.GamepadController'), \
             patch('screen_recognizer.ScreenRecognizer'), \
             patch('banner_skipper.BannerSkipper'), \
             patch('player_signer.PlayerSigner'), \
             patch('player_trainer.PlayerTrainer'), \
             patch('match_player.MatchPlayer'):
            
            # Crear la aplicación
            self.app = EFootballAutomation()
    
    def test_initialization(self):
        """Prueba la inicialización de la aplicación"""
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.app.gamepad)
        self.assertIsNotNone(self.app.recognizer)
        self.assertIsNotNone(self.app.banner_skipper)
        self.assertIsNotNone(self.app.player_signer)
        self.assertIsNotNone(self.app.player_trainer)
        self.assertIsNotNone(self.app.match_player)
    
    def test_skip_banners(self):
        """Prueba la función de saltar banners"""
        # Configurar el mock para que devuelva True
        self.app.banner_skipper.run = MagicMock(return_value=True)
        
        # Probar saltar banners
        result = self.app.skip_banners()
        
        # Verificar que se llamó al método run del saltador de banners
        self.app.banner_skipper.run.assert_called_once()
        self.assertTrue(result)
    
    def test_sign_player(self):
        """Prueba la función de fichar jugador"""
        # Configurar el mock para que devuelva True
        self.app.player_signer.run = MagicMock(return_value=True)
        
        # Probar fichar jugador
        result = self.app.sign_player(player_name="Test", filters={"position": "Delantero"}, player_index=0)
        
        # Verificar que se llamó al método run del fichador de jugadores
        self.app.player_signer.run.assert_called_once_with("Test", {"position": "Delantero"}, 0)
        self.assertTrue(result)
    
    def test_train_player(self):
        """Prueba la función de entrenar jugador"""
        # Configurar el mock para que devuelva True
        self.app.player_trainer.run = MagicMock(return_value=True)
        
        # Probar entrenar jugador
        result = self.app.train_player(player_name="Test")
        
        # Verificar que se llamó al método run del entrenador de jugadores
        self.app.player_trainer.run.assert_called_once_with("Test")
        self.assertTrue(result)
    
    def test_play_matches(self):
        """Prueba la función de jugar partidos"""
        # Configurar el mock para que devuelva True
        self.app.match_player.run = MagicMock(return_value=True)
        
        # Probar jugar partidos
        result = self.app.play_matches(max_matches=5, event_mode=True, difficulty="normal")
        
        # Verificar que se llamó al método run del jugador de partidos
        self.app.match_player.run.assert_called_once_with(5, True, "normal")
        self.assertTrue(result)
    
    def test_run_all(self):
        """Prueba la función de ejecutar todas las funcionalidades"""
        # Configurar los mocks para que devuelvan True
        self.app.skip_banners = MagicMock(return_value=True)
        self.app.sign_player = MagicMock(return_value=True)
        self.app.train_player = MagicMock(return_value=True)
        self.app.play_matches = MagicMock(return_value=True)
        
        # Probar ejecutar todas las funcionalidades
        results = self.app.run_all()
        
        # Verificar que se llamaron todos los métodos
        self.app.skip_banners.assert_called_once()
        self.app.sign_player.assert_called_once()
        self.app.train_player.assert_called_once()
        self.app.play_matches.assert_called_once()
        
        # Verificar los resultados
        self.assertTrue(results["skip_banners"])
        self.assertTrue(results["sign_player"])
        self.assertTrue(results["train_player"])
        self.assertTrue(results["play_matches"])

if __name__ == "__main__":
    unittest.main()
