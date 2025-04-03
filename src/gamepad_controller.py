"""
Módulo de control de gamepad para la automatización de eFootball

Este módulo proporciona funciones para emular un gamepad virtual (Xbox/DualSense)
y controlar el juego eFootball mediante comandos programáticos.

Utiliza la biblioteca vgamepad para crear y manipular un gamepad virtual en Windows.
"""

import vgamepad as vg
import time
from enum import Enum

class GamepadType(Enum):
    """Tipos de gamepad soportados"""
    XBOX360 = "xbox360"
    XBOXONE = "xboxone"
    DS4 = "dualshock4"  # PlayStation DualShock 4

class GamepadButton(Enum):
    """Botones comunes en gamepads"""
    # Botones comunes
    A = "a"
    B = "b"
    X = "x"
    Y = "y"
    START = "start"
    BACK = "back"
    # D-Pad
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"
    # Bumpers y triggers
    LB = "left_shoulder"
    RB = "right_shoulder"
    LT = "left_trigger"
    RT = "right_trigger"
    # Joysticks
    LEFT_THUMB = "left_thumb"
    RIGHT_THUMB = "right_thumb"

class GamepadController:
    """
    Clase para controlar un gamepad virtual y enviar comandos al juego eFootball.
    """
    
    def __init__(self, gamepad_type=GamepadType.XBOX360):
        """
        Inicializa un controlador de gamepad virtual.
        
        Args:
            gamepad_type (GamepadType): Tipo de gamepad a emular (por defecto: Xbox 360)
        """
        self.gamepad_type = gamepad_type
        
        # Crear el gamepad virtual según el tipo seleccionado
        if gamepad_type == GamepadType.XBOX360:
            self.gamepad = vg.VX360Gamepad()
        elif gamepad_type == GamepadType.XBOXONE:
            self.gamepad = vg.VX360Gamepad()  # Usamos el mismo ya que vgamepad no tiene específico para Xbox One
        elif gamepad_type == GamepadType.DS4:
            self.gamepad = vg.VDS4Gamepad()  # DualShock 4
        else:
            raise ValueError(f"Tipo de gamepad no soportado: {gamepad_type}")
        
        # Mapeo de botones según el tipo de gamepad
        self._init_button_mapping()
        
        print(f"Gamepad virtual de tipo {gamepad_type.value} inicializado correctamente")
    
    def _init_button_mapping(self):
        """Inicializa el mapeo de botones según el tipo de gamepad"""
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            self.button_mapping = {
                GamepadButton.A: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                GamepadButton.B: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                GamepadButton.X: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                GamepadButton.Y: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                GamepadButton.START: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                GamepadButton.BACK: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                GamepadButton.LB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                GamepadButton.RB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                GamepadButton.LEFT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                GamepadButton.RIGHT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                GamepadButton.DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                GamepadButton.DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                GamepadButton.DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                GamepadButton.DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
            }
        elif self.gamepad_type == GamepadType.DS4:
            # Mapeo para DualShock 4
            self.button_mapping = {
                GamepadButton.A: vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
                GamepadButton.B: vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
                GamepadButton.X: vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
                GamepadButton.Y: vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
                GamepadButton.START: vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
                GamepadButton.BACK: vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
                GamepadButton.LB: vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
                GamepadButton.RB: vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
                GamepadButton.LEFT_THUMB: vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
                GamepadButton.RIGHT_THUMB: vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
                GamepadButton.DPAD_UP: vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH,
                GamepadButton.DPAD_DOWN: vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH,
                GamepadButton.DPAD_LEFT: vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST,
                GamepadButton.DPAD_RIGHT: vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST,
            }
    
    def press_button(self, button, duration=0.1):
        """
        Presiona un botón del gamepad y lo suelta después de la duración especificada.
        
        Args:
            button (GamepadButton): Botón a presionar
            duration (float): Duración en segundos que el botón permanecerá presionado
        """
        if button not in self.button_mapping:
            raise ValueError(f"Botón no soportado: {button}")
        
        # Obtener el botón específico según el tipo de gamepad
        mapped_button = self.button_mapping[button]
        
        # Presionar el botón
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            self.gamepad.press_button(button=mapped_button)
        elif self.gamepad_type == GamepadType.DS4:
            if button in [GamepadButton.DPAD_UP, GamepadButton.DPAD_DOWN, 
                         GamepadButton.DPAD_LEFT, GamepadButton.DPAD_RIGHT]:
                self.gamepad.directional_pad(direction=mapped_button)
            else:
                self.gamepad.press_button(button=mapped_button)
        
        # Actualizar el estado del gamepad
        self.gamepad.update()
        
        # Esperar la duración especificada
        time.sleep(duration)
        
        # Soltar el botón
        self.release_button(button)
    
    def release_button(self, button):
        """
        Suelta un botón del gamepad.
        
        Args:
            button (GamepadButton): Botón a soltar
        """
        if button not in self.button_mapping:
            raise ValueError(f"Botón no soportado: {button}")
        
        # Obtener el botón específico según el tipo de gamepad
        mapped_button = self.button_mapping[button]
        
        # Soltar el botón
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            self.gamepad.release_button(button=mapped_button)
        elif self.gamepad_type == GamepadType.DS4:
            if button in [GamepadButton.DPAD_UP, GamepadButton.DPAD_DOWN, 
                         GamepadButton.DPAD_LEFT, GamepadButton.DPAD_RIGHT]:
                self.gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
            else:
                self.gamepad.release_button(button=mapped_button)
        
        # Actualizar el estado del gamepad
        self.gamepad.update()
    
    def move_joystick(self, joystick="left", x_value=0, y_value=0, duration=0.1):
        """
        Mueve un joystick del gamepad.
        
        Args:
            joystick (str): Joystick a mover ("left" o "right")
            x_value (int): Valor del eje X (-32768 a 32767)
            y_value (int): Valor del eje Y (-32768 a 32767)
            duration (float): Duración en segundos que el joystick permanecerá en la posición
        """
        # Mover el joystick
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            if joystick.lower() == "left":
                self.gamepad.left_joystick(x_value=x_value, y_value=y_value)
            elif joystick.lower() == "right":
                self.gamepad.right_joystick(x_value=x_value, y_value=y_value)
            else:
                raise ValueError(f"Joystick no válido: {joystick}. Debe ser 'left' o 'right'")
        elif self.gamepad_type == GamepadType.DS4:
            if joystick.lower() == "left":
                self.gamepad.left_joystick_float(x_value=x_value/32767.0, y_value=y_value/32767.0)
            elif joystick.lower() == "right":
                self.gamepad.right_joystick_float(x_value=x_value/32767.0, y_value=y_value/32767.0)
            else:
                raise ValueError(f"Joystick no válido: {joystick}. Debe ser 'left' o 'right'")
        
        # Actualizar el estado del gamepad
        self.gamepad.update()
        
        # Esperar la duración especificada
        time.sleep(duration)
        
        # Volver a la posición central
        if duration > 0:
            self.reset_joystick(joystick)
    
    def reset_joystick(self, joystick="left"):
        """
        Devuelve un joystick a su posición central.
        
        Args:
            joystick (str): Joystick a resetear ("left" o "right")
        """
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            if joystick.lower() == "left":
                self.gamepad.left_joystick(x_value=0, y_value=0)
            elif joystick.lower() == "right":
                self.gamepad.right_joystick(x_value=0, y_value=0)
            else:
                raise ValueError(f"Joystick no válido: {joystick}. Debe ser 'left' o 'right'")
        elif self.gamepad_type == GamepadType.DS4:
            if joystick.lower() == "left":
                self.gamepad.left_joystick_float(x_value=0.0, y_value=0.0)
            elif joystick.lower() == "right":
                self.gamepad.right_joystick_float(x_value=0.0, y_value=0.0)
            else:
                raise ValueError(f"Joystick no válido: {joystick}. Debe ser 'left' o 'right'")
        
        # Actualizar el estado del gamepad
        self.gamepad.update()
    
    def trigger_press(self, trigger="left", value=255, duration=0.1):
        """
        Presiona un gatillo del gamepad.
        
        Args:
            trigger (str): Gatillo a presionar ("left" o "right")
            value (int): Valor de presión (0-255 para Xbox, 0-255 para DS4)
            duration (float): Duración en segundos que el gatillo permanecerá presionado
        """
        # Presionar el gatillo
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            if trigger.lower() == "left":
                self.gamepad.left_trigger(value=value)
            elif trigger.lower() == "right":
                self.gamepad.right_trigger(value=value)
            else:
                raise ValueError(f"Gatillo no válido: {trigger}. Debe ser 'left' o 'right'")
        elif self.gamepad_type == GamepadType.DS4:
            if trigger.lower() == "left":
                self.gamepad.left_trigger_float(value=value/255.0)
            elif trigger.lower() == "right":
                self.gamepad.right_trigger_float(value=value/255.0)
            else:
                raise ValueError(f"Gatillo no válido: {trigger}. Debe ser 'left' o 'right'")
        
        # Actualizar el estado del gamepad
        self.gamepad.update()
        
        # Esperar la duración especificada
        time.sleep(duration)
        
        # Soltar el gatillo
        if duration > 0:
            self.trigger_release(trigger)
    
    def trigger_release(self, trigger="left"):
        """
        Suelta un gatillo del gamepad.
        
        Args:
            trigger (str): Gatillo a soltar ("left" o "right")
        """
        # Soltar el gatillo
        if self.gamepad_type in [GamepadType.XBOX360, GamepadType.XBOXONE]:
            if trigger.lower() == "left":
                self.gamepad.left_trigger(value=0)
            elif trigger.lower() == "right":
                self.gamepad.right_trigger(value=0)
            else:
                raise ValueError(f"Gatillo no válido: {trigger}. Debe ser 'left' o 'right'")
        elif self.gamepad_type == GamepadType.DS4:
            if trigger.lower() == "left":
                self.gamepad.left_trigger_float(value=0.0)
            elif trigger.lower() == "right":
                self.gamepad.right_trigger_float(value=0.0)
            else:
                raise ValueError(f"Gatillo no válido: {trigger}. Debe ser 'left' o 'right'")
        
        # Actualizar el estado del gamepad
        self.gamepad.update()
    
    def execute_sequence(self, sequence):
        """
        Ejecuta una secuencia de comandos del gamepad.
        
        Args:
            sequence (list): Lista de diccionarios con comandos a ejecutar
                Ejemplo: [
                    {"type": "button", "button": GamepadButton.A, "duration": 0.1},
                    {"type": "joystick", "joystick": "left", "x": 32767, "y": 0, "duration": 0.5},
                    {"type": "wait", "duration": 1.0}
                ]
        """
        for command in sequence:
            cmd_type = command.get("type", "")
            
            if cmd_type == "button":
                button = command.get("button")
                duration = command.get("duration", 0.1)
                self.press_button(button, duration)
            
            elif cmd_type == "joystick":
                joystick = command.get("joystick", "left")
                x_value = command.get("x", 0)
                y_value = command.get("y", 0)
                duration = command.get("duration", 0.1)
                self.move_joystick(joystick, x_value, y_value, duration)
            
            elif cmd_type == "trigger":
                trigger = command.get("trigger", "left")
                value = command.get("value", 255)
                duration = command.get("duration", 0.1)
                self.trigger_press(trigger, value, duration)
            
            elif cmd_type == "wait":
                duration = command.get("duration", 0.5)
                time.sleep(duration)
            
            else:
                print(f"Tipo de comando desconocido: {cmd_type}")

# Ejemplos de secuencias predefinidas para eFootball
class EFootballSequences:
    """
    Secuencias predefinidas de comandos para acciones comunes en eFootball.
    """
    
    @staticmethod
    def saltar_banner():
        """Secuencia para saltar un banner o anuncio"""
        return [
            {"type": "button", "button": GamepadButton.X, "duration": 0.1},
            {"type": "wait", "duration": 0.5},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 0.5}
        ]
    
    @staticmethod
    def navegar_menu_principal_a_contratos():
        """Secuencia para navegar desde el menú principal a la sección de contratos"""
        return [
            {"type": "button", "button": GamepadButton.DPAD_RIGHT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.DPAD_RIGHT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 1.0}
        ]
    
    @staticmethod
    def seleccionar_jugadores_normales():
        """Secuencia para seleccionar la opción de jugadores normales en el menú de contratos"""
        return [
            {"type": "button", "button": GamepadButton.DPAD_DOWN, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 1.0}
        ]
    
    @staticmethod
    def confirmar_compra():
        """Secuencia para confirmar la compra de un jugador"""
        return [
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 0.5},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 2.0}
        ]
    
    @staticmethod
    def navegar_menu_principal_a_mi_equipo():
        """Secuencia para navegar desde el menú principal a la sección de Mi Equipo"""
        return [
            {"type": "button", "button": GamepadButton.DPAD_LEFT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 1.0}
        ]
    
    @staticmethod
    def seleccionar_jugador_en_lista(navegaciones_abajo=0):
        """
        Secuencia para seleccionar un jugador en la lista de Mi Equipo
        
        Args:
            navegaciones_abajo (int): Número de veces que se presiona el botón abajo para llegar al jugador
        """
        sequence = []
        
        # Navegar hacia abajo hasta el jugador deseado
        for _ in range(navegaciones_abajo):
            sequence.append({"type": "button", "button": GamepadButton.DPAD_DOWN, "duration": 0.1})
            sequence.append({"type": "wait", "duration": 0.2})
        
        # Seleccionar el jugador
        sequence.append({"type": "button", "button": GamepadButton.A, "duration": 0.1})
        sequence.append({"type": "wait", "duration": 0.5})
        
        return sequence
    
    @staticmethod
    def acceder_a_habilidades():
        """Secuencia para acceder a la sección de habilidades de un jugador"""
        return [
            {"type": "button", "button": GamepadButton.DPAD_RIGHT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.DPAD_RIGHT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 1.0}
        ]
    
    @staticmethod
    def seleccionar_entrenamiento_habilidad():
        """Secuencia para seleccionar la opción de entrenamiento de habilidad"""
        return [
            {"type": "button", "button": GamepadButton.DPAD_DOWN, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 1.0}
        ]
    
    @staticmethod
    def navegar_menu_principal_a_partido():
        """Secuencia para navegar desde el menú principal a la sección de partidos"""
        return [
            {"type": "button", "button": GamepadButton.DPAD_LEFT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.DPAD_LEFT, "duration": 0.1},
            {"type": "wait", "duration": 0.3},
            {"type": "button", "button": GamepadButton.A, "duration": 0.1},
            {"type": "wait", "duration": 1.0}
        ]

# Ejemplo de uso
def ejemplo_uso():
    """Ejemplo de uso del módulo de control de gamepad"""
    # Crear un controlador de gamepad virtual (Xbox 360 por defecto)
    controller = GamepadController()
    
    # Presionar un botón
    controller.press_button(GamepadButton.A, duration=0.2)
    
    # Mover el joystick izquierdo
    controller.move_joystick("left", x_value=32767, y_value=0, duration=0.5)  # Derecha
    
    # Ejecutar una secuencia predefinida
    controller.execute_sequence(EFootballSequences.saltar_banner())
    
    print("Ejemplo completado")

if __name__ == "__main__":
    print("Módulo de control de gamepad para eFootball")
    print("Este módulo proporciona funciones para emular un gamepad virtual")
    print("y controlar el juego eFootball mediante comandos programáticos.")
    print("\nEjemplo de uso:")
    ejemplo_uso()
