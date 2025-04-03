"""
Interfaz de usuario para la configuración de acciones en eFootball.

Este módulo proporciona una interfaz de línea de comandos para crear, editar,
y gestionar secuencias de acciones personalizadas para la automatización de eFootball.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional

# Añadir el directorio padre al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar el gestor de configuraciones
from config_interface.config_manager import ConfigManager, SequenceBuilder, ActionSequence

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_interface.cli')

class ConfigCLI:
    """
    Interfaz de línea de comandos para la configuración de acciones.
    """
    def __init__(self):
        """
        Inicializa la interfaz de línea de comandos.
        """
        self.config_manager = ConfigManager()
        self.sequence_builder = SequenceBuilder(self.config_manager)
        
    def run(self):
        """
        Ejecuta la interfaz de línea de comandos.
        """
        parser = argparse.ArgumentParser(
            description='Configuración de acciones para la automatización de eFootball'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
        
        # Comando: list
        list_parser = subparsers.add_parser('list', help='Listar secuencias disponibles')
        
        # Comando: create
        create_parser = subparsers.add_parser('create', help='Crear una nueva secuencia')
        create_parser.add_argument('name', help='Nombre de la secuencia')
        create_parser.add_argument('--description', '-d', help='Descripción de la secuencia')
        
        # Comando: edit
        edit_parser = subparsers.add_parser('edit', help='Editar una secuencia existente')
        edit_parser.add_argument('name', help='Nombre de la secuencia')
        
        # Comando: delete
        delete_parser = subparsers.add_parser('delete', help='Eliminar una secuencia')
        delete_parser.add_argument('name', help='Nombre de la secuencia')
        
        # Comando: show
        show_parser = subparsers.add_parser('show', help='Mostrar detalles de una secuencia')
        show_parser.add_argument('name', help='Nombre de la secuencia')
        
        # Comando: settings
        settings_parser = subparsers.add_parser('settings', help='Gestionar configuración global')
        settings_parser.add_argument('--gamepad', choices=['xbox', 'ps4'], help='Tipo de gamepad')
        settings_parser.add_argument('--confidence', type=float, help='Umbral de confianza para reconocimiento de imágenes')
        settings_parser.add_argument('--move-speed', type=int, help='Velocidad de movimiento del cursor')
        
        # Parsear argumentos
        args = parser.parse_args()
        
        # Ejecutar comando
        if args.command == 'list':
            self._list_sequences()
        elif args.command == 'create':
            self._create_sequence(args.name, args.description)
        elif args.command == 'edit':
            self._edit_sequence(args.name)
        elif args.command == 'delete':
            self._delete_sequence(args.name)
        elif args.command == 'show':
            self._show_sequence(args.name)
        elif args.command == 'settings':
            self._manage_settings(args)
        else:
            parser.print_help()
    
    def _list_sequences(self):
        """
        Lista todas las secuencias disponibles.
        """
        sequences = self.config_manager.list_sequences()
        
        if not sequences:
            print("No hay secuencias disponibles.")
            return
        
        print("Secuencias disponibles:")
        for i, name in enumerate(sequences, 1):
            sequence = self.config_manager.load_sequence(name)
            description = sequence.description if sequence else ""
            print(f"{i}. {name} - {description}")
    
    def _create_sequence(self, name: str, description: Optional[str] = None):
        """
        Crea una nueva secuencia interactivamente.
        
        Args:
            name: Nombre de la secuencia
            description: Descripción de la secuencia
        """
        if description is None:
            description = input("Descripción de la secuencia (opcional): ")
        
        # Crear secuencia
        self.sequence_builder.create_sequence(name, description)
        
        print(f"Creando secuencia '{name}'")
        print("Añade acciones a la secuencia. Escribe 'fin' para terminar.")
        
        while True:
            print("\nTipos de acciones disponibles:")
            print("1. Pulsar botón")
            print("2. Esperar imagen")
            print("3. Mover cursor")
            print("4. Esperar tiempo")
            print("5. Guardar y salir")
            
            choice = input("\nSelecciona una acción (1-5): ")
            
            if choice == '5' or choice.lower() == 'fin':
                break
            
            try:
                if choice == '1':
                    self._add_button_press()
                elif choice == '2':
                    self._add_wait_for_image()
                elif choice == '3':
                    self._add_move_cursor()
                elif choice == '4':
                    self._add_wait()
                else:
                    print("Opción no válida.")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Guardar secuencia
        self.sequence_builder.save_current_sequence()
        print(f"Secuencia '{name}' guardada correctamente.")
    
    def _add_button_press(self):
        """
        Añade una acción de pulsación de botón interactivamente.
        """
        print("\nBotones disponibles:")
        print("A, B, X, Y, LB, RB, LT, RT, START, SELECT")
        print("DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT")
        
        button = input("Botón a pulsar: ").upper()
        duration = input("Duración (segundos, por defecto 0.1): ")
        
        try:
            duration = float(duration) if duration else 0.1
        except ValueError:
            print("Duración no válida, usando valor por defecto (0.1)")
            duration = 0.1
        
        self.sequence_builder.add_button_press(button, duration)
        print(f"Acción añadida: Pulsar botón {button} durante {duration} segundos")
    
    def _add_wait_for_image(self):
        """
        Añade una acción de espera de imagen interactivamente.
        """
        image_name = input("Nombre de la imagen (ej: Menu_principal.png): ")
        timeout = input("Tiempo máximo de espera (segundos, por defecto 10): ")
        
        try:
            timeout = float(timeout) if timeout else 10.0
        except ValueError:
            print("Tiempo no válido, usando valor por defecto (10)")
            timeout = 10.0
        
        self.sequence_builder.add_wait_for_image(image_name, timeout)
        print(f"Acción añadida: Esperar imagen {image_name} (timeout: {timeout}s)")
    
    def _add_move_cursor(self):
        """
        Añade una acción de movimiento del cursor interactivamente.
        """
        print("\nTipos de objetivo:")
        print("1. Imagen")
        print("2. Coordenadas")
        print("3. Elemento")
        
        target_type_choice = input("Selecciona tipo de objetivo (1-3): ")
        
        if target_type_choice == '1':
            target_type = 'image'
            image_name = input("Nombre de la imagen objetivo: ")
            self.sequence_builder.add_move_cursor(target_type, image_name=image_name)
            print(f"Acción añadida: Mover cursor a imagen {image_name}")
        
        elif target_type_choice == '2':
            target_type = 'coordinates'
            try:
                x = int(input("Coordenada X: "))
                y = int(input("Coordenada Y: "))
                self.sequence_builder.add_move_cursor(target_type, x=x, y=y)
                print(f"Acción añadida: Mover cursor a coordenadas ({x}, {y})")
            except ValueError:
                print("Coordenadas no válidas")
        
        elif target_type_choice == '3':
            target_type = 'element'
            element_id = input("ID del elemento: ")
            self.sequence_builder.add_move_cursor(target_type, element_id=element_id)
            print(f"Acción añadida: Mover cursor a elemento {element_id}")
        
        else:
            print("Opción no válida")
    
    def _add_wait(self):
        """
        Añade una acción de espera interactivamente.
        """
        seconds = input("Tiempo de espera (segundos): ")
        
        try:
            seconds = float(seconds)
            self.sequence_builder.add_wait(seconds)
            print(f"Acción añadida: Esperar {seconds} segundos")
        except ValueError:
            print("Tiempo no válido")
    
    def _edit_sequence(self, name: str):
        """
        Edita una secuencia existente.
        
        Args:
            name: Nombre de la secuencia a editar
        """
        sequence = self.config_manager.load_sequence(name)
        
        if sequence is None:
            print(f"No se encontró la secuencia '{name}'")
            return
        
        # Crear una nueva secuencia con el mismo nombre
        self.sequence_builder.create_sequence(name, sequence.description)
        
        # Mostrar acciones actuales
        print(f"Editando secuencia '{name}'")
        print(f"Descripción: {sequence.description}")
        print("\nAcciones actuales:")
        
        for i, action in enumerate(sequence.actions, 1):
            action_type = action['type']
            params = action['params']
            
            if action_type == 'button_press':
                print(f"{i}. Pulsar botón {params['button']} durante {params.get('duration', 0.1)} segundos")
            elif action_type == 'wait_for_image':
                print(f"{i}. Esperar imagen {params['image_name']} (timeout: {params.get('timeout', 10.0)}s)")
            elif action_type == 'move_cursor':
                target_type = params['target_type']
                if target_type == 'image':
                    print(f"{i}. Mover cursor a imagen {params['image_name']}")
                elif target_type == 'coordinates':
                    print(f"{i}. Mover cursor a coordenadas ({params['x']}, {params['y']})")
                elif target_type == 'element':
                    print(f"{i}. Mover cursor a elemento {params['element_id']}")
            elif action_type == 'wait':
                print(f"{i}. Esperar {params['seconds']} segundos")
        
        print("\nOpciones:")
        print("1. Mantener acciones actuales y añadir nuevas")
        print("2. Eliminar todas y crear nuevas")
        
        choice = input("\nSelecciona una opción (1-2): ")
        
        if choice == '2':
            # Eliminar todas las acciones
            self.sequence_builder.current_sequence.actions = []
        else:
            # Mantener acciones actuales
            self.sequence_builder.current_sequence.actions = sequence.actions
        
        # Añadir nuevas acciones
        print("\nAñade nuevas acciones a la secuencia. Escribe 'fin' para terminar.")
        
        while True:
            print("\nTipos de acciones disponibles:")
            print("1. Pulsar botón")
            print("2. Esperar imagen")
            print("3. Mover cursor")
            print("4. Esperar tiempo")
            print("5. Guardar y salir")
            
            choice = input("\nSelecciona una acción (1-5): ")
            
            if choice == '5' or choice.lower() == 'fin':
                break
            
            try:
                if choice == '1':
                    self._add_button_press()
                elif choice == '2':
                    self._add_wait_for_image()
                elif choice == '3':
                    self._add_move_cursor()
                elif choice == '4':
                    self._add_wait()
                else:
                    print("Opción no válida.")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Guardar secuencia
        self.sequence_builder.save_current_sequence()
        print(f"Secuencia '{name}' actualizada correctamente.")
    
    def _delete_sequence(self, name: str):
        """
        Elimina una secuencia.
        
        Args:
            name: Nombre de la secuencia a eliminar
        """
        confirm = input(f"¿Estás seguro de que quieres eliminar la secuencia '{name}'? (s/n): ")
        
        if confirm.lower() == 's':
            if self.config_manager.delete_sequence(name):
                print(f"Secuencia '{name}' eliminada correctamente.")
            else:
                print(f"No se pudo eliminar la secuencia '{name}'.")
        else:
            print("Operación cancelada.")
    
    def _show_sequence(self, name: str):
        """
        Muestra los detalles de una secuencia.
        
        Args:
            name: Nombre de la secuencia a mostrar
        """
        sequence = self.config_manager.load_sequence(name)
        
        if sequence is None:
            print(f"No se encontró la secuencia '{name}'")
            return
        
        print(f"Secuencia: {name}")
        print(f"Descripción: {sequence.description}")
        print("\nAcciones:")
        
        for i, action in enumerate(sequence.actions, 1):
            action_type = action['type']
            params = action['params']
            
            if action_type == 'button_press':
                print(f"{i}. Pulsar botón {params['button']} durante {params.get('duration', 0.1)} segundos")
            elif action_type == 'wait_for_image':
                print(f"{i}. Esperar imagen {params['image_name']} (timeout: {params.get('timeout', 10.0)}s)")
            elif action_type == 'move_cursor':
                target_type = params['target_type']
                if target_type == 'image':
                    print(f"{i}. Mover cursor a imagen {params['image_name']}")
                elif target_type == 'coordinates':
                    print(f"{i}. Mover cursor a coordenadas ({params['x']}, {params['y']})")
                elif target_type == 'element':
                    print(f"{i}. Mover cursor a elemento {params['element_id']}")
            elif action_type == 'wait':
                print(f"{i}. Esperar {params['seconds']} segundos")
    
    def _manage_settings(self, args):
        """
        Gestiona la configuración global.
        
        Args:
            args: Argumentos de línea de comandos
        """
        settings = self.config_manager.settings
        modified = False
        
        if args.gamepad:
            settings['gamepad']['type'] = args.gamepad
            modified = True
            print(f"Tipo de gamepad actualizado a: {args.gamepad}")
        
        if args.confidence is not None:
            settings['screen_recognition']['confidence_threshold'] = args.confidence
            modified = True
            print(f"Umbral de confianza actualizado a: {args.confidence}")
        
        if args.move_speed is not None:
            settings['cursor_navigation']['move_speed'] = args.move_speed
            modified = True
            print(f"Velocidad de movimiento actualizada a: {args.move_speed}")
        
        if modified:
            self.config_manager.save_settings()
            print("Configuración guardada correctamente.")
        else:
            # Mostrar configuración actual
            print("Configuración actual:")
            print(f"- Tipo de gamepad: {settings['gamepad']['type']}")
            print(f"- Umbral de confianza: {settings['screen_recognition']['confidence_threshold']}")
            print(f"- Velocidad de movimiento: {settings['cursor_navigation']['move_speed']}")


if __name__ == "__main__":
    cli = ConfigCLI()
    cli.run()
