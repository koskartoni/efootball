"""
Módulo de interfaz de configuración para la automatización de eFootball.

Este módulo proporciona una interfaz para configurar secuencias de acciones
personalizadas para diferentes escenarios del juego, permitiendo un control
preciso del cursor y la selección de opciones.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_interface')

class ActionSequence:
    """
    Clase que representa una secuencia de acciones para un escenario específico.
    """
    def __init__(self, name: str, description: str = ""):
        """
        Inicializa una nueva secuencia de acciones.
        
        Args:
            name: Nombre identificativo de la secuencia
            description: Descripción detallada de la secuencia
        """
        self.name = name
        self.description = description
        self.actions: List[Dict[str, Any]] = []
        
    def add_action(self, action_type: str, **kwargs) -> None:
        """
        Añade una acción a la secuencia.
        
        Args:
            action_type: Tipo de acción (button_press, wait_for_image, etc.)
            **kwargs: Parámetros específicos de la acción
        """
        action = {
            'type': action_type,
            'params': kwargs
        }
        self.actions.append(action)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la secuencia a un diccionario para su serialización.
        
        Returns:
            Diccionario con los datos de la secuencia
        """
        return {
            'name': self.name,
            'description': self.description,
            'actions': self.actions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionSequence':
        """
        Crea una secuencia a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la secuencia
            
        Returns:
            Instancia de ActionSequence
        """
        sequence = cls(data['name'], data.get('description', ''))
        sequence.actions = data.get('actions', [])
        return sequence


class ConfigManager:
    """
    Gestor de configuraciones para la automatización de eFootball.
    """
    def __init__(self, config_dir: str = None):
        """
        Inicializa el gestor de configuraciones.
        
        Args:
            config_dir: Directorio donde se almacenarán las configuraciones
        """
        if config_dir is None:
            # Directorio por defecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, 'config')
        
        self.config_dir = config_dir
        self.sequences_dir = os.path.join(config_dir, 'sequences')
        self.templates_dir = os.path.join(config_dir, 'templates')
        self.settings_file = os.path.join(config_dir, 'settings.yaml')
        
        # Crear directorios si no existen
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.sequences_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Cargar configuración global
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """
        Carga la configuración global desde el archivo settings.yaml.
        
        Returns:
            Diccionario con la configuración global
        """
        if not os.path.exists(self.settings_file):
            # Crear configuración por defecto
            default_settings = {
                'gamepad': {
                    'type': 'xbox',  # o 'ps4'
                    'button_mapping': {
                        'A': 'A',  # Xbox A = PS4 X
                        'B': 'B',  # Xbox B = PS4 O
                        'X': 'X',  # Xbox X = PS4 □
                        'Y': 'Y',  # Xbox Y = PS4 △
                        'LB': 'LB',
                        'RB': 'RB',
                        'LT': 'LT',
                        'RT': 'RT',
                        'START': 'START',
                        'SELECT': 'SELECT',
                        'DPAD_UP': 'DPAD_UP',
                        'DPAD_DOWN': 'DPAD_DOWN',
                        'DPAD_LEFT': 'DPAD_LEFT',
                        'DPAD_RIGHT': 'DPAD_RIGHT'
                    }
                },
                'screen_recognition': {
                    'confidence_threshold': 0.7,
                    'max_wait_time': 10.0,  # segundos
                    'check_interval': 0.5   # segundos
                },
                'cursor_navigation': {
                    'move_speed': 5,  # velocidad de movimiento del cursor
                    'precision_threshold': 10  # píxeles
                }
            }
            
            with open(self.settings_file, 'w') as f:
                yaml.dump(default_settings, f, default_flow_style=False)
            
            return default_settings
        
        with open(self.settings_file, 'r') as f:
            return yaml.safe_load(f)
    
    def save_settings(self) -> None:
        """
        Guarda la configuración global en el archivo settings.yaml.
        """
        with open(self.settings_file, 'w') as f:
            yaml.dump(self.settings, f, default_flow_style=False)
        
        logger.info(f"Configuración guardada en {self.settings_file}")
    
    def get_sequence_path(self, name: str) -> str:
        """
        Obtiene la ruta completa a un archivo de secuencia.
        
        Args:
            name: Nombre de la secuencia
            
        Returns:
            Ruta completa al archivo de secuencia
        """
        return os.path.join(self.sequences_dir, f"{name}.json")
    
    def save_sequence(self, sequence: ActionSequence) -> None:
        """
        Guarda una secuencia de acciones en un archivo JSON.
        
        Args:
            sequence: Secuencia de acciones a guardar
        """
        file_path = self.get_sequence_path(sequence.name)
        
        with open(file_path, 'w') as f:
            json.dump(sequence.to_dict(), f, indent=2)
        
        logger.info(f"Secuencia '{sequence.name}' guardada en {file_path}")
    
    def load_sequence(self, name: str) -> Optional[ActionSequence]:
        """
        Carga una secuencia de acciones desde un archivo JSON.
        
        Args:
            name: Nombre de la secuencia
            
        Returns:
            Secuencia de acciones o None si no existe
        """
        file_path = self.get_sequence_path(name)
        
        if not os.path.exists(file_path):
            logger.warning(f"No se encontró la secuencia '{name}'")
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return ActionSequence.from_dict(data)
    
    def list_sequences(self) -> List[str]:
        """
        Lista todas las secuencias disponibles.
        
        Returns:
            Lista de nombres de secuencias
        """
        sequences = []
        
        for file_name in os.listdir(self.sequences_dir):
            if file_name.endswith('.json'):
                sequences.append(file_name[:-5])  # Eliminar extensión .json
        
        return sequences
    
    def delete_sequence(self, name: str) -> bool:
        """
        Elimina una secuencia.
        
        Args:
            name: Nombre de la secuencia
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        file_path = self.get_sequence_path(name)
        
        if not os.path.exists(file_path):
            logger.warning(f"No se encontró la secuencia '{name}'")
            return False
        
        os.remove(file_path)
        logger.info(f"Secuencia '{name}' eliminada")
        return True


class SequenceBuilder:
    """
    Constructor de secuencias de acciones para la automatización de eFootball.
    """
    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa el constructor de secuencias.
        
        Args:
            config_manager: Gestor de configuraciones
        """
        self.config_manager = config_manager
        self.current_sequence: Optional[ActionSequence] = None
    
    def create_sequence(self, name: str, description: str = "") -> ActionSequence:
        """
        Crea una nueva secuencia de acciones.
        
        Args:
            name: Nombre de la secuencia
            description: Descripción de la secuencia
            
        Returns:
            Nueva secuencia de acciones
        """
        self.current_sequence = ActionSequence(name, description)
        return self.current_sequence
    
    def add_button_press(self, button: str, duration: float = 0.1) -> None:
        """
        Añade una acción de pulsación de botón.
        
        Args:
            button: Nombre del botón (A, B, X, Y, etc.)
            duration: Duración de la pulsación en segundos
        """
        if self.current_sequence is None:
            raise ValueError("No hay una secuencia activa")
        
        self.current_sequence.add_action(
            'button_press',
            button=button,
            duration=duration
        )
    
    def add_wait_for_image(self, image_name: str, timeout: float = 10.0) -> None:
        """
        Añade una acción de espera hasta que aparezca una imagen.
        
        Args:
            image_name: Nombre de la imagen a buscar
            timeout: Tiempo máximo de espera en segundos
        """
        if self.current_sequence is None:
            raise ValueError("No hay una secuencia activa")
        
        self.current_sequence.add_action(
            'wait_for_image',
            image_name=image_name,
            timeout=timeout
        )
    
    def add_move_cursor(self, target_type: str, **kwargs) -> None:
        """
        Añade una acción de movimiento del cursor.
        
        Args:
            target_type: Tipo de objetivo ('image', 'coordinates', 'element')
            **kwargs: Parámetros específicos según el tipo de objetivo
        """
        if self.current_sequence is None:
            raise ValueError("No hay una secuencia activa")
        
        params = {'target_type': target_type}
        params.update(kwargs)
        
        self.current_sequence.add_action('move_cursor', **params)
    
    def add_wait(self, seconds: float) -> None:
        """
        Añade una acción de espera.
        
        Args:
            seconds: Tiempo de espera en segundos
        """
        if self.current_sequence is None:
            raise ValueError("No hay una secuencia activa")
        
        self.current_sequence.add_action('wait', seconds=seconds)
    
    def save_current_sequence(self) -> None:
        """
        Guarda la secuencia actual.
        """
        if self.current_sequence is None:
            raise ValueError("No hay una secuencia activa")
        
        self.config_manager.save_sequence(self.current_sequence)


class ActionExecutor:
    """
    Ejecutor de secuencias de acciones para la automatización de eFootball.
    """
    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa el ejecutor de acciones.
        
        Args:
            config_manager: Gestor de configuraciones
        """
        self.config_manager = config_manager
        
        # Estos módulos se importarán dinámicamente para evitar dependencias circulares
        self.gamepad_controller = None
        self.screen_recognizer = None
    
    def _load_dependencies(self) -> None:
        """
        Carga las dependencias necesarias para ejecutar acciones.
        """
        if self.gamepad_controller is None or self.screen_recognizer is None:
            # Importar módulos dinámicamente
            import sys
            import importlib.util
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(base_dir)
            
            # Cargar gamepad_controller
            try:
                from src.gamepad_controller import GamepadController
                self.gamepad_controller = GamepadController()
            except ImportError:
                logger.error("No se pudo cargar el módulo gamepad_controller")
                raise
            
            # Cargar screen_recognizer
            try:
                from src.screen_recognizer import ScreenRecognizer
                self.screen_recognizer = ScreenRecognizer()
            except ImportError:
                logger.error("No se pudo cargar el módulo screen_recognizer")
                raise
    
    def execute_sequence(self, sequence_name: str) -> bool:
        """
        Ejecuta una secuencia de acciones.
        
        Args:
            sequence_name: Nombre de la secuencia a ejecutar
            
        Returns:
            True si la ejecución fue exitosa, False en caso contrario
        """
        self._load_dependencies()
        
        sequence = self.config_manager.load_sequence(sequence_name)
        if sequence is None:
            logger.error(f"No se encontró la secuencia '{sequence_name}'")
            return False
        
        logger.info(f"Ejecutando secuencia '{sequence_name}'")
        
        for i, action in enumerate(sequence.actions):
            action_type = action['type']
            params = action['params']
            
            logger.info(f"Ejecutando acción {i+1}/{len(sequence.actions)}: {action_type}")
            
            try:
                if action_type == 'button_press':
                    self._execute_button_press(params)
                elif action_type == 'wait_for_image':
                    self._execute_wait_for_image(params)
                elif action_type == 'move_cursor':
                    self._execute_move_cursor(params)
                elif action_type == 'wait':
                    self._execute_wait(params)
                else:
                    logger.warning(f"Tipo de acción desconocido: {action_type}")
            except Exception as e:
                logger.error(f"Error al ejecutar acción {action_type}: {str(e)}")
                return False
        
        logger.info(f"Secuencia '{sequence_name}' ejecutada correctamente")
        return True
    
    def _execute_button_press(self, params: Dict[str, Any]) -> None:
        """
        Ejecuta una acción de pulsación de botón.
        
        Args:
            params: Parámetros de la acción
        """
        button = params['button']
        duration = params.get('duration', 0.1)
        
        self.gamepad_controller.press_button(button, duration)
    
    def _execute_wait_for_image(self, params: Dict[str, Any]) -> None:
        """
        Ejecuta una acción de espera hasta que aparezca una imagen.
        
        Args:
            params: Parámetros de la acción
        """
        image_name = params['image_name']
        timeout = params.get('timeout', 10.0)
        
        self.screen_recognizer.wait_for_image(image_name, timeout)
    
    def _execute_move_cursor(self, params: Dict[str, Any]) -> None:
        """
        Ejecuta una acción de movimiento del cursor.
        
        Args:
            params: Parámetros de la acción
        """
        target_type = params['target_type']
        
        if target_type == 'image':
            image_name = params['image_name']
            self.screen_recognizer.move_to_image(image_name)
        elif target_type == 'coordinates':
            x = params['x']
            y = params['y']
            self.gamepad_controller.move_cursor_to(x, y)
        elif target_type == 'element':
            element_id = params['element_id']
            self.screen_recognizer.move_to_element(element_id)
    
    def _execute_wait(self, params: Dict[str, Any]) -> None:
        """
        Ejecuta una acción de espera.
        
        Args:
            params: Parámetros de la acción
        """
        import time
        seconds = params['seconds']
        time.sleep(seconds)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear gestor de configuraciones
    config_manager = ConfigManager()
    
    # Crear constructor de secuencias
    builder = SequenceBuilder(config_manager)
    
    # Crear una secuencia de ejemplo para saltar banners iniciales
    sequence = builder.create_sequence(
        "saltar_banners", 
        "Secuencia para saltar los banners iniciales del juego"
    )
    
    # Añadir acciones a la secuencia
    builder.add_wait_for_image("Pantalla_bienvenida.png")
    builder.add_button_press("A")
    builder.add_wait(1.0)
    builder.add_wait_for_image("Bonus_inicio_sesion.png")
    builder.add_button_press("A")
    builder.add_wait(1.0)
    builder.add_wait_for_image("Bonus_Campaña.png")
    builder.add_button_press("A")
    builder.add_wait(1.0)
    builder.add_wait_for_image("Menu_principal_baner.png")
    builder.add_button_press("B")
    
    # Guardar la secuencia
    builder.save_current_sequence()
    
    print("Secuencia de ejemplo creada y guardada.")
    print(f"Secuencias disponibles: {config_manager.list_sequences()}")
