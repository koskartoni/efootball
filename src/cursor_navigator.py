"""
Sistema mejorado de navegación por cursor para eFootball.

Este módulo proporciona funcionalidades avanzadas para el control preciso
del cursor en la interfaz de eFootball, utilizando reconocimiento de imágenes
y algoritmos de movimiento optimizados.
"""

import os
import time
import logging
import numpy as np
import cv2
import pyautogui
from typing import Tuple, List, Dict, Any, Optional, Union

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cursor_navigator')

class CursorNavigator:
    """
    Navegador de cursor avanzado para eFootball.
    """
    def __init__(self, gamepad_controller=None, screen_recognizer=None):
        """
        Inicializa el navegador de cursor.
        
        Args:
            gamepad_controller: Controlador de gamepad (opcional)
            screen_recognizer: Reconocedor de pantalla (opcional)
        """
        self.gamepad_controller = gamepad_controller
        self.screen_recognizer = screen_recognizer
        
        # Cargar configuración
        self._load_config()
        
        # Inicializar estado del cursor
        self.current_position = (0, 0)
        self.target_position = (0, 0)
        self.is_moving = False
        
        # Cargar dependencias si no se proporcionaron
        if self.gamepad_controller is None or self.screen_recognizer is None:
            self._load_dependencies()
    
    def _load_config(self):
        """
        Carga la configuración del navegador de cursor.
        """
        # Valores por defecto
        self.config = {
            'move_speed': 5,  # Velocidad de movimiento del cursor
            'precision_threshold': 10,  # Umbral de precisión en píxeles
            'max_attempts': 3,  # Número máximo de intentos para alcanzar un objetivo
            'move_delay': 0.05,  # Retraso entre movimientos del cursor
            'acceleration': 1.5,  # Factor de aceleración para movimientos largos
            'deceleration': 0.5,  # Factor de desaceleración para aproximación final
            'element_detection_confidence': 0.7,  # Umbral de confianza para detección de elementos
            'use_adaptive_speed': True,  # Usar velocidad adaptativa según distancia
            'use_path_correction': True,  # Usar corrección de trayectoria
            'debug_mode': False  # Modo de depuración
        }
        
        # Intentar cargar configuración desde archivo
        try:
            import yaml
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
            settings_file = os.path.join(config_dir, 'settings.yaml')
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f)
                    
                    if 'cursor_navigation' in settings:
                        cursor_settings = settings['cursor_navigation']
                        for key, value in cursor_settings.items():
                            if key in self.config:
                                self.config[key] = value
                                
                logger.info("Configuración de navegación por cursor cargada desde archivo")
            else:
                logger.warning("No se encontró archivo de configuración, usando valores por defecto")
        
        except Exception as e:
            logger.error(f"Error al cargar configuración: {str(e)}")
            logger.info("Usando configuración por defecto")
    
    def _load_dependencies(self):
        """
        Carga las dependencias necesarias si no se proporcionaron en el constructor.
        """
        try:
            # Importar módulos dinámicamente
            import sys
            import importlib.util
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(base_dir)
            
            # Cargar gamepad_controller si no se proporcionó
            if self.gamepad_controller is None:
                try:
                    from src.gamepad_controller import GamepadController
                    self.gamepad_controller = GamepadController()
                    logger.info("GamepadController cargado dinámicamente")
                except ImportError:
                    logger.error("No se pudo cargar el módulo gamepad_controller")
                    raise
            
            # Cargar screen_recognizer si no se proporcionó
            if self.screen_recognizer is None:
                try:
                    from src.screen_recognizer import ScreenRecognizer
                    self.screen_recognizer = ScreenRecognizer()
                    logger.info("ScreenRecognizer cargado dinámicamente")
                except ImportError:
                    logger.error("No se pudo cargar el módulo screen_recognizer")
                    raise
        
        except Exception as e:
            logger.error(f"Error al cargar dependencias: {str(e)}")
            raise
    
    def get_current_position(self) -> Tuple[int, int]:
        """
        Obtiene la posición actual del cursor.
        
        Returns:
            Tupla con las coordenadas (x, y) del cursor
        """
        # Si estamos usando un cursor virtual, devolver la posición almacenada
        if hasattr(self.gamepad_controller, 'get_cursor_position'):
            self.current_position = self.gamepad_controller.get_cursor_position()
        else:
            # Si no tenemos acceso directo a la posición del cursor, estimarla
            # basándonos en la última posición conocida y los movimientos realizados
            pass
        
        return self.current_position
    
    def move_to_coordinates(self, x: int, y: int, smooth: bool = True) -> bool:
        """
        Mueve el cursor a las coordenadas especificadas.
        
        Args:
            x: Coordenada X de destino
            y: Coordenada Y de destino
            smooth: Si True, realiza un movimiento suave
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        self.target_position = (x, y)
        current_x, current_y = self.get_current_position()
        
        logger.info(f"Moviendo cursor de ({current_x}, {current_y}) a ({x}, {y})")
        
        if smooth and self.config['use_adaptive_speed']:
            return self._move_smooth(current_x, current_y, x, y)
        else:
            return self._move_direct(current_x, current_y, x, y)
    
    def _move_direct(self, current_x: int, current_y: int, target_x: int, target_y: int) -> bool:
        """
        Realiza un movimiento directo del cursor.
        
        Args:
            current_x: Coordenada X actual
            current_y: Coordenada Y actual
            target_x: Coordenada X de destino
            target_y: Coordenada Y de destino
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        # Calcular vector de movimiento
        dx = target_x - current_x
        dy = target_y - current_y
        
        # Normalizar vector si es necesario
        distance = np.sqrt(dx**2 + dy**2)
        
        if distance < self.config['precision_threshold']:
            logger.info(f"Ya estamos suficientemente cerca del objetivo ({distance:.2f} px)")
            return True
        
        # Mover el cursor usando el gamepad
        self.is_moving = True
        
        try:
            if hasattr(self.gamepad_controller, 'move_cursor_to'):
                # Si el controlador tiene un método específico para mover el cursor
                success = self.gamepad_controller.move_cursor_to(target_x, target_y)
                self.current_position = (target_x, target_y)
                return success
            else:
                # Implementación genérica usando el stick analógico
                normalized_dx = dx / distance
                normalized_dy = dy / distance
                
                # Calcular cuánto tiempo mantener presionado el stick
                move_time = distance / (self.config['move_speed'] * 10)  # Ajustar según sea necesario
                
                # Mover usando el stick analógico
                self.gamepad_controller.move_stick('right', normalized_dx, normalized_dy, duration=move_time)
                
                # Actualizar posición actual
                self.current_position = (target_x, target_y)
                
                return True
        
        except Exception as e:
            logger.error(f"Error al mover el cursor: {str(e)}")
            return False
        
        finally:
            self.is_moving = False
    
    def _move_smooth(self, current_x: int, current_y: int, target_x: int, target_y: int) -> bool:
        """
        Realiza un movimiento suave del cursor con velocidad adaptativa.
        
        Args:
            current_x: Coordenada X actual
            current_y: Coordenada Y actual
            target_x: Coordenada X de destino
            target_y: Coordenada Y de destino
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        # Calcular distancia total
        dx = target_x - current_x
        dy = target_y - current_y
        total_distance = np.sqrt(dx**2 + dy**2)
        
        if total_distance < self.config['precision_threshold']:
            logger.info(f"Ya estamos suficientemente cerca del objetivo ({total_distance:.2f} px)")
            return True
        
        # Calcular número de pasos basado en la distancia
        num_steps = max(int(total_distance / 10), 5)  # Al menos 5 pasos
        
        # Calcular incrementos para cada paso
        step_x = dx / num_steps
        step_y = dy / num_steps
        
        # Mover el cursor gradualmente
        self.is_moving = True
        success = True
        
        try:
            for i in range(num_steps):
                # Calcular posición intermedia
                progress = (i + 1) / num_steps
                
                # Aplicar aceleración/desaceleración
                if progress < 0.3:
                    # Fase de aceleración
                    factor = self.config['acceleration'] * (progress / 0.3)
                elif progress > 0.7:
                    # Fase de desaceleración
                    factor = self.config['deceleration'] + (1 - self.config['deceleration']) * ((1 - progress) / 0.3)
                else:
                    # Velocidad constante
                    factor = 1.0
                
                # Calcular posición actual
                current_progress = i / num_steps
                next_x = int(current_x + dx * (current_progress + factor / num_steps))
                next_y = int(current_y + dy * (current_progress + factor / num_steps))
                
                # Mover a la siguiente posición
                if hasattr(self.gamepad_controller, 'move_cursor_to'):
                    step_success = self.gamepad_controller.move_cursor_to(next_x, next_y)
                else:
                    # Calcular dirección para este paso
                    step_dx = next_x - (current_x + dx * current_progress)
                    step_dy = next_y - (current_y + dy * current_progress)
                    step_distance = np.sqrt(step_dx**2 + step_dy**2)
                    
                    if step_distance > 0:
                        normalized_dx = step_dx / step_distance
                        normalized_dy = step_dy / step_distance
                        
                        # Mover usando el stick analógico
                        self.gamepad_controller.move_stick('right', normalized_dx, normalized_dy, duration=self.config['move_delay'])
                        step_success = True
                    else:
                        step_success = True
                
                if not step_success:
                    success = False
                    break
                
                # Actualizar posición actual
                self.current_position = (next_x, next_y)
                
                # Pequeña pausa entre movimientos
                time.sleep(self.config['move_delay'])
            
            # Movimiento final para asegurar precisión
            if success and hasattr(self.gamepad_controller, 'move_cursor_to'):
                self.gamepad_controller.move_cursor_to(target_x, target_y)
            
            self.current_position = (target_x, target_y)
            return success
        
        except Exception as e:
            logger.error(f"Error al mover el cursor suavemente: {str(e)}")
            return False
        
        finally:
            self.is_moving = False
    
    def move_to_element(self, element_id: str) -> bool:
        """
        Mueve el cursor a un elemento identificado por su ID.
        
        Args:
            element_id: Identificador del elemento
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        # Buscar el elemento en la pantalla
        element = self.screen_recognizer.find_element_by_id(element_id)
        
        if element is None:
            logger.error(f"No se encontró el elemento con ID '{element_id}'")
            return False
        
        # Obtener coordenadas del centro del elemento
        x, y = element['center']
        
        # Mover el cursor a las coordenadas del elemento
        return self.move_to_coordinates(x, y)
    
    def move_to_image(self, image_name: str, confidence: float = None) -> bool:
        """
        Mueve el cursor a una imagen en la pantalla.
        
        Args:
            image_name: Nombre del archivo de imagen a buscar
            confidence: Umbral de confianza para la detección (opcional)
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        if confidence is None:
            confidence = self.config['element_detection_confidence']
        
        # Buscar la imagen en la pantalla
        location = self.screen_recognizer.find_image_on_screen(image_name, confidence)
        
        if location is None:
            logger.error(f"No se encontró la imagen '{image_name}' en la pantalla")
            return False
        
        # Obtener coordenadas del centro de la imagen
        x, y, w, h = location
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Mover el cursor a las coordenadas de la imagen
        return self.move_to_coordinates(center_x, center_y)
    
    def move_to_text(self, text: str, region: Tuple[int, int, int, int] = None) -> bool:
        """
        Mueve el cursor a un texto en la pantalla.
        
        Args:
            text: Texto a buscar
            region: Región de la pantalla donde buscar (x, y, ancho, alto)
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        # Buscar el texto en la pantalla
        location = self.screen_recognizer.find_text_on_screen(text, region)
        
        if location is None:
            logger.error(f"No se encontró el texto '{text}' en la pantalla")
            return False
        
        # Obtener coordenadas del centro del texto
        x, y, w, h = location
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Mover el cursor a las coordenadas del texto
        return self.move_to_coordinates(center_x, center_y)
    
    def move_in_direction(self, direction: str, distance: int = 50) -> bool:
        """
        Mueve el cursor en una dirección específica.
        
        Args:
            direction: Dirección ('up', 'down', 'left', 'right')
            distance: Distancia en píxeles
            
        Returns:
            True si el movimiento fue exitoso, False en caso contrario
        """
        current_x, current_y = self.get_current_position()
        
        if direction == 'up':
            target_y = current_y - distance
            target_x = current_x
        elif direction == 'down':
            target_y = current_y + distance
            target_x = current_x
        elif direction == 'left':
            target_x = current_x - distance
            target_y = current_y
        elif direction == 'right':
            target_x = current_x + distance
            target_y = current_y
        else:
            logger.error(f"Dirección no válida: {direction}")
            return False
        
        return self.move_to_coordinates(target_x, target_y)
    
    def click_at_current_position(self, button: str = 'A') -> bool:
        """
        Hace clic en la posición actual del cursor.
        
        Args:
            button: Botón a pulsar ('A', 'B', 'X', 'Y', etc.)
            
        Returns:
            True si el clic fue exitoso, False en caso contrario
        """
        try:
            self.gamepad_controller.press_button(button)
            return True
        except Exception as e:
            logger.error(f"Error al hacer clic: {str(e)}")
            return False
    
    def navigate_to_menu_option(self, option_text: str, menu_region: Tuple[int, int, int, int] = None) -> bool:
        """
        Navega a una opción de menú específica.
        
        Args:
            option_text: Texto de la opción de menú
            menu_region: Región de la pantalla donde buscar (x, y, ancho, alto)
            
        Returns:
            True si la navegación fue exitosa, False en caso contrario
        """
        # Buscar la opción de menú en la pantalla
        success = self.move_to_text(option_text, menu_region)
        
        if not success:
            logger.error(f"No se pudo navegar a la opción de menú '{option_text}'")
            return False
        
        # Hacer clic en la opción
        return self.click_at_current_position()
    
    def navigate_menu_by_dpad(self, target_option: str, menu_options: List[str], 
                             current_option: str = None, layout: str = 'vertical') -> bool:
        """
        Navega por un menú usando el D-pad.
        
        Args:
            target_option: Opción de menú objetivo
            menu_options: Lista de opciones de menú en orden
            current_option: Opción de menú actual (si se conoce)
            layout: Disposición del menú ('vertical' u 'horizontal')
            
        Returns:
            True si la navegación fue exitosa, False en caso contrario
        """
        if target_option not in menu_options:
            logger.error(f"La opción objetivo '{target_option}' no está en la lista de opciones")
            return False
        
        # Si no se conoce la opción actual, intentar detectarla
        if current_option is None:
            # Aquí podríamos implementar lógica para detectar la opción actual
            # basándonos en el reconocimiento de pantalla
            current_option = menu_options[0]  # Asumir que estamos en la primera opción
        
        if current_option not in menu_options:
            logger.error(f"La opción actual '{current_option}' no está en la lista de opciones")
            return False
        
        # Calcular número de movimientos necesarios
        current_index = menu_options.index(current_option)
        target_index = menu_options.index(target_option)
        steps = target_index - current_index
        
        if steps == 0:
            # Ya estamos en la opción objetivo
            return True
        
        # Determinar dirección de navegación
        if layout == 'vertical':
            direction = 'DPAD_DOWN' if steps > 0 else 'DPAD_UP'
        else:  # horizontal
            direction = 'DPAD_RIGHT' if steps > 0 else 'DPAD_LEFT'
        
        # Navegar al objetivo
        for _ in range(abs(steps)):
            self.gamepad_controller.press_button(direction)
            time.sleep(0.2)  # Pequeña pausa entre pulsaciones
        
        # Seleccionar la opción
        self.gamepad_controller.press_button('A')
        
        return True
    
    def find_and_click_element(self, element_type: str, identifier: str) -> bool:
        """
        Busca y hace clic en un elemento específico.
        
        Args:
            element_type: Tipo de elemento ('image', 'text', 'element_id')
            identifier: Identificador del elemento
            
        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        success = False
        
        if element_type == 'image':
            success = self.move_to_image(identifier)
        elif element_type == 'text':
            success = self.move_to_text(identifier)
        elif element_type == 'element_id':
            success = self.move_to_element(identifier)
        else:
            logger.error(f"Tipo de elemento no válido: {element_type}")
            return False
        
        if not success:
            return False
        
        # Hacer clic en el elemento
        return self.click_at_current_position()
    
    def navigate_complex_menu(self, menu_path: List[str], layout_map: Dict[str, str] = None) -> bool:
        """
        Navega por un menú complejo siguiendo una ruta de opciones.
        
        Args:
            menu_path: Lista de opciones de menú a seguir
            layout_map: Mapa de disposición para cada nivel de menú
            
        Returns:
            True si la navegación fue exitosa, False en caso contrario
        """
        if not menu_path:
            return True
        
        if layout_map is None:
            # Asumir que todos los menús son verticales por defecto
            layout_map = {option: 'vertical' for option in menu_path}
        
        for i, option in enumerate(menu_path):
            # Intentar encontrar y hacer clic en la opción
            success = self.find_and_click_element('text', option)
            
            if not success:
                # Si no podemos encontrar la opción por texto, intentar por imagen
                image_name = f"{option.lower().replace(' ', '_')}.png"
                success = self.find_and_click_element('image', image_name)
            
            if not success:
                logger.error(f"No se pudo navegar a la opción '{option}'")
                return False
            
            # Esperar a que se cargue el siguiente menú
            time.sleep(0.5)
        
        return True


# Ejemplo de uso
if __name__ == "__main__":
    # Este código se ejecutaría solo si se ejecuta el módulo directamente
    print("Módulo de navegación por cursor para eFootball")
    print("Este módulo debe ser importado por otros componentes del sistema")
