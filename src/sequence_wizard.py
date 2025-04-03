"""
Asistente para configuración de secuencias en eFootball Automation.

Este módulo proporciona un asistente interactivo que facilita la creación
de secuencias personalizadas para automatizar diferentes acciones en eFootball.
"""

import os
import sys
import time
import json
import yaml
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import cv2
import numpy as np
import pyautogui
from typing import Dict, List, Any, Optional, Tuple, Union

# Añadir el directorio padre al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos necesarios
from config_interface.config_manager import ConfigManager, SequenceBuilder, ActionSequence
from src.screen_recognizer import ScreenRecognizer
from src.gamepad_controller import GamepadController
from src.cursor_navigator import CursorNavigator

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sequence_wizard')

class SequenceWizard:
    """
    Asistente para la creación de secuencias de acciones en eFootball.
    """
    def __init__(self):
        """
        Inicializa el asistente de secuencias.
        """
        self.config_manager = ConfigManager()
        self.sequence_builder = SequenceBuilder(self.config_manager)
        self.screen_recognizer = ScreenRecognizer()
        self.gamepad_controller = GamepadController()
        self.cursor_navigator = CursorNavigator(self.gamepad_controller, self.screen_recognizer)
        
        # Estado del asistente
        self.current_sequence = None
        self.recording = False
        self.last_screenshot = None
        self.selected_elements = []
        self.recorded_actions = []
        
        # Configuración
        self.config = {
            'screenshot_interval': 0.5,  # segundos
            'action_detection_threshold': 0.8,  # umbral de confianza
            'auto_save_interval': 60,  # segundos
            'max_recording_time': 300,  # segundos
            'image_save_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images'),
            'temp_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        }
        
        # Crear directorios si no existen
        os.makedirs(self.config['image_save_dir'], exist_ok=True)
        os.makedirs(self.config['temp_dir'], exist_ok=True)
    
    def start_gui(self):
        """
        Inicia la interfaz gráfica del asistente.
        """
        self.root = tk.Tk()
        self.root.title("Asistente de Secuencias - eFootball Automation")
        self.root.geometry("1000x700")
        
        self._create_widgets()
        self.root.mainloop()
    
    def _create_widgets(self):
        """
        Crea los widgets de la interfaz gráfica.
        """
        # Frame principal con dos paneles
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo: Controles y lista de acciones
        left_frame = ttk.Frame(main_frame, width=400)
        main_frame.add(left_frame, weight=1)
        
        # Panel derecho: Visualización de pantalla
        right_frame = ttk.Frame(main_frame, width=600)
        main_frame.add(right_frame, weight=2)
        
        # --- Panel izquierdo ---
        # Sección de información de secuencia
        info_frame = ttk.LabelFrame(left_frame, text="Información de la Secuencia")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Descripción:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.desc_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.desc_var).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
        # Botones de control
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.record_button = ttk.Button(control_frame, text="Iniciar Grabación", command=self._toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(control_frame, text="Añadir Acción", command=self._add_action_manually).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Guardar Secuencia", command=self._save_sequence).pack(side=tk.LEFT, padx=2)
        
        # Lista de acciones grabadas
        actions_frame = ttk.LabelFrame(left_frame, text="Acciones Grabadas")
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botones para gestionar acciones
        action_btn_frame = ttk.Frame(actions_frame)
        action_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_btn_frame, text="Editar", command=self._edit_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Eliminar", command=self._delete_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Mover Arriba", command=self._move_action_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Mover Abajo", command=self._move_action_down).pack(side=tk.LEFT, padx=2)
        
        # Treeview para mostrar acciones
        self.actions_tree = ttk.Treeview(actions_frame, columns=("type", "details"), show="headings")
        self.actions_tree.heading("type", text="Tipo")
        self.actions_tree.heading("details", text="Detalles")
        self.actions_tree.column("type", width=100)
        self.actions_tree.column("details", width=300)
        self.actions_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # --- Panel derecho ---
        # Visualización de pantalla
        screen_frame = ttk.LabelFrame(right_frame, text="Visualización de Pantalla")
        screen_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas para mostrar capturas de pantalla
        self.screen_canvas = tk.Canvas(screen_frame, bg="black")
        self.screen_canvas.pack(fill=tk.BOTH, expand=True)
        self.screen_canvas.bind("<Button-1>", self._on_canvas_click)
        
        # Controles de visualización
        view_control_frame = ttk.Frame(right_frame)
        view_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(view_control_frame, text="Capturar Pantalla", command=self._capture_screenshot).pack(side=tk.LEFT, padx=2)
        ttk.Button(view_control_frame, text="Detectar Elementos", command=self._detect_elements).pack(side=tk.LEFT, padx=2)
        ttk.Button(view_control_frame, text="Limpiar Selección", command=self._clear_selection).pack(side=tk.LEFT, padx=2)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def _toggle_recording(self):
        """
        Inicia o detiene la grabación de acciones.
        """
        if not self.recording:
            # Verificar que se haya ingresado un nombre
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Debes ingresar un nombre para la secuencia")
                return
            
            # Crear nueva secuencia
            description = self.desc_var.get().strip()
            self.current_sequence = self.sequence_builder.create_sequence(name, description)
            self.recorded_actions = []
            
            # Iniciar grabación
            self.recording = True
            self.record_button.config(text="Detener Grabación")
            self.status_var.set("Grabando acciones...")
            
            # Iniciar hilo de grabación
            self.recording_thread = threading.Thread(target=self._recording_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
        else:
            # Detener grabación
            self.recording = False
            self.record_button.config(text="Iniciar Grabación")
            self.status_var.set("Grabación detenida")
            
            # Actualizar lista de acciones
            self._update_actions_tree()
    
    def _recording_loop(self):
        """
        Bucle principal de grabación de acciones.
        """
        start_time = time.time()
        last_save_time = start_time
        
        try:
            while self.recording:
                # Verificar tiempo máximo de grabación
                current_time = time.time()
                if current_time - start_time > self.config['max_recording_time']:
                    self.root.after(0, lambda: messagebox.showinfo("Información", "Se ha alcanzado el tiempo máximo de grabación"))
                    self.root.after(0, self._toggle_recording)
                    break
                
                # Auto-guardar periódicamente
                if current_time - last_save_time > self.config['auto_save_interval']:
                    self.root.after(0, lambda: self.status_var.set("Auto-guardando secuencia..."))
                    self._save_sequence_internal()
                    last_save_time = current_time
                
                # Capturar pantalla
                self._capture_screenshot_internal()
                
                # Detectar acciones
                self._detect_actions()
                
                # Actualizar interfaz
                self.root.after(0, self._update_actions_tree)
                
                # Esperar intervalo
                time.sleep(self.config['screenshot_interval'])
        
        except Exception as e:
            logger.error(f"Error en bucle de grabación: {str(e)}")
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, self._toggle_recording)
    
    def _capture_screenshot_internal(self):
        """
        Captura una imagen de la pantalla (para uso interno).
        """
        try:
            # Capturar pantalla
            screenshot = pyautogui.screenshot()
            self.last_screenshot = np.array(screenshot)
            self.last_screenshot = cv2.cvtColor(self.last_screenshot, cv2.COLOR_RGB2BGR)
            
            # Guardar captura temporal
            temp_file = os.path.join(self.config['temp_dir'], "last_screenshot.png")
            cv2.imwrite(temp_file, self.last_screenshot)
            
            # Actualizar canvas
            self.root.after(0, self._update_canvas)
        
        except Exception as e:
            logger.error(f"Error al capturar pantalla: {str(e)}")
    
    def _capture_screenshot(self):
        """
        Captura una imagen de la pantalla (acción manual).
        """
        self._capture_screenshot_internal()
        self.status_var.set("Captura de pantalla realizada")
    
    def _update_canvas(self):
        """
        Actualiza el canvas con la última captura de pantalla.
        """
        if self.last_screenshot is None:
            return
        
        # Convertir imagen para Tkinter
        img = cv2.cvtColor(self.last_screenshot, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (800, 450))  # Ajustar tamaño para visualización
        
        # Convertir a formato PhotoImage
        from PIL import Image, ImageTk
        img_pil = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        
        # Actualizar canvas
        self.screen_canvas.config(width=img_tk.width(), height=img_tk.height())
        self.screen_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        self.screen_canvas.image = img_tk  # Mantener referencia
        
        # Dibujar elementos seleccionados
        for i, element in enumerate(self.selected_elements):
            x, y, w, h = element['bbox']
            # Ajustar coordenadas a la escala del canvas
            scale_x = 800 / self.last_screenshot.shape[1]
            scale_y = 450 / self.last_screenshot.shape[0]
            x1 = int(x * scale_x)
            y1 = int(y * scale_y)
            x2 = int((x + w) * scale_x)
            y2 = int((y + h) * scale_y)
            
            # Dibujar rectángulo
            self.screen_canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)
            self.screen_canvas.create_text(x1, y1-10, text=f"#{i+1}", fill="red", anchor=tk.W)
    
    def _on_canvas_click(self, event):
        """
        Maneja clics en el canvas.
        """
        if self.last_screenshot is None:
            return
        
        # Convertir coordenadas del canvas a coordenadas de la imagen original
        scale_x = self.last_screenshot.shape[1] / 800
        scale_y = self.last_screenshot.shape[0] / 450
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)
        
        # Añadir acción de clic
        self._add_click_action(x, y)
    
    def _add_click_action(self, x, y):
        """
        Añade una acción de clic en las coordenadas especificadas.
        """
        if self.current_sequence is None:
            name = self.name_var.get().strip()
            description = self.desc_var.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Debes ingresar un nombre para la secuencia")
                return
            
            self.current_sequence = self.sequence_builder.create_sequence(name, description)
        
        # Añadir acción de movimiento del cursor
        self.current_sequence.add_action('move_cursor', target_type='coordinates', x=x, y=y)
        
        # Añadir acción de clic
        self.current_sequence.add_action('button_press', button='A')
        
        # Actualizar lista de acciones
        self._update_actions_tree()
        
        self.status_var.set(f"Añadida acción de clic en ({x}, {y})")
    
    def _detect_elements(self):
        """
        Detecta elementos interactivos en la pantalla.
        """
        if self.last_screenshot is None:
            messagebox.showinfo("Información", "Primero debes capturar una imagen de la pantalla")
            return
        
        try:
            # Detectar elementos
            elements = self.screen_recognizer.detect_ui_elements(self.last_screenshot)
            
            if not elements:
                messagebox.showinfo("Información", "No se detectaron elementos interactivos")
                return
            
            # Guardar elementos detectados
            self.selected_elements = elements
            
            # Actualizar canvas
            self._update_canvas()
            
            self.status_var.set(f"Se detectaron {len(elements)} elementos interactivos")
        
        except Exception as e:
            logger.error(f"Error al detectar elementos: {str(e)}")
            messagebox.showerror("Error", f"Error al detectar elementos: {str(e)}")
    
    def _clear_selection(self):
        """
        Limpia la selección de elementos.
        """
        self.selected_elements = []
        self._update_canvas()
        self.status_var.set("Selección limpiada")
    
    def _detect_actions(self):
        """
        Detecta acciones del usuario durante la grabación.
        """
        # Esta función detectaría acciones del usuario como pulsaciones de botones,
        # movimientos del cursor, etc. durante la grabación.
        # Por simplicidad, aquí solo simularemos algunas detecciones.
        
        # Detectar pulsaciones de botones del gamepad
        if hasattr(self.gamepad_controller, 'get_last_button_press'):
            button = self.gamepad_controller.get_last_button_press()
            if button:
                self.current_sequence.add_action('button_press', button=button)
                self.recorded_actions.append({
                    'type': 'button_press',
                    'params': {'button': button}
                })
        
        # Detectar movimientos del cursor
        if hasattr(self.gamepad_controller, 'get_cursor_position'):
            position = self.gamepad_controller.get_cursor_position()
            if position and hasattr(self.gamepad_controller, 'get_last_cursor_position'):
                last_position = self.gamepad_controller.get_last_cursor_position()
                if last_position and (abs(position[0] - last_position[0]) > 10 or abs(position[1] - last_position[1]) > 10):
                    self.current_sequence.add_action('move_cursor', target_type='coordinates', x=position[0], y=position[1])
                    self.recorded_actions.append({
                        'type': 'move_cursor',
                        'params': {'target_type': 'coordinates', 'x': position[0], 'y': position[1]}
                    })
    
    def _add_action_manually(self):
        """
        Añade una acción manualmente.
        """
        if self.current_sequence is None:
            name = self.name_var.get().strip()
            description = self.desc_var.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Debes ingresar un nombre para la secuencia")
                return
            
            self.current_sequence = self.sequence_builder.create_sequence(name, description)
        
        # Mostrar diálogo para añadir acción
        dialog = ActionDialog(self.root)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            action_type, params = dialog.result
            
            # Añadir acción a la secuencia
            self.current_sequence.add_action(action_type, **params)
            
            # Actualizar lista de acciones
            self._update_actions_tree()
            
            self.status_var.set(f"Acción '{action_type}' añadida manualmente")
    
    def _update_actions_tree(self):
        """
        Actualiza el árbol de acciones con las acciones de la secuencia actual.
        """
        self.actions_tree.delete(*self.actions_tree.get_children())
        
        if not self.current_sequence:
            return
        
        for i, action in enumerate(self.current_sequence.actions):
            action_type = action['type']
            params = action['params']
            
            details = ""
            if action_type == 'button_press':
                details = f"Botón: {params['button']}, Duración: {params.get('duration', 0.1)}s"
            elif action_type == 'wait_for_image':
                details = f"Imagen: {params['image_name']}, Timeout: {params.get('timeout', 10.0)}s"
            elif action_type == 'move_cursor':
                target_type = params['target_type']
                if target_type == 'image':
                    details = f"A imagen: {params['image_name']}"
                elif target_type == 'coordinates':
                    details = f"A coordenadas: ({params['x']}, {params['y']})"
                elif target_type == 'element':
                    details = f"A elemento: {params['element_id']}"
            elif action_type == 'wait':
                details = f"Tiempo: {params['seconds']}s"
            
            self.actions_tree.insert("", tk.END, values=(action_type, details))
    
    def _edit_action(self):
        """
        Edita la acción seleccionada.
        """
        selection = self.actions_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una acción para editar")
            return
        
        index = self.actions_tree.index(selection[0])
        action = self.current_sequence.actions[index]
        
        dialog = ActionDialog(self.root, action['type'], action['params'])
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            action_type, params = dialog.result
            
            # Actualizar acción
            self.current_sequence.actions[index] = {
                'type': action_type,
                'params': params
            }
            
            self._update_actions_tree()
            self.status_var.set(f"Acción '{action_type}' actualizada")
    
    def _delete_action(self):
        """
        Elimina la acción seleccionada.
        """
        selection = self.actions_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una acción para eliminar")
            return
        
        index = self.actions_tree.index(selection[0])
        
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres eliminar esta acción?"):
            del self.current_sequence.actions[index]
            self._update_actions_tree()
            self.status_var.set("Acción eliminada")
    
    def _move_action_up(self):
        """
        Mueve la acción seleccionada hacia arriba.
        """
        selection = self.actions_tree.selection()
        if not selection:
            return
        
        index = self.actions_tree.index(selection[0])
        if index > 0:
            # Intercambiar acciones
            self.current_sequence.actions[index], self.current_sequence.actions[index-1] = \
                self.current_sequence.actions[index-1], self.current_sequence.actions[index]
            
            self._update_actions_tree()
            self.actions_tree.selection_set(self.actions_tree.get_children()[index-1])
            self.status_var.set("Acción movida hacia arriba")
    
    def _move_action_down(self):
        """
        Mueve la acción seleccionada hacia abajo.
        """
        selection = self.actions_tree.selection()
        if not selection:
            return
        
        index = self.actions_tree.index(selection[0])
        if index < len(self.current_sequence.actions) - 1:
            # Intercambiar acciones
            self.current_sequence.actions[index], self.current_sequence.actions[index+1] = \
                self.current_sequence.actions[index+1], self.current_sequence.actions[index]
            
            self._update_actions_tree()
            self.actions_tree.selection_set(self.actions_tree.get_children()[index+1])
            self.status_var.set("Acción movida hacia abajo")
    
    def _save_sequence_internal(self):
        """
        Guarda la secuencia actual (para uso interno).
        """
        if not self.current_sequence:
            return False
        
        try:
            self.sequence_builder.current_sequence = self.current_sequence
            self.sequence_builder.save_current_sequence()
            return True
        except Exception as e:
            logger.error(f"Error al guardar secuencia: {str(e)}")
            return False
    
    def _save_sequence(self):
        """
        Guarda la secuencia actual.
        """
        if not self.current_sequence:
            messagebox.showwarning("Advertencia", "No hay una secuencia activa para guardar")
            return
        
        # Actualizar nombre y descripción por si cambiaron
        name = self.name_var.get().strip()
        description = self.desc_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Debes ingresar un nombre para la secuencia")
            return
        
        # Si cambió el nombre, crear una nueva secuencia
        if name != self.current_sequence.name:
            old_name = self.current_sequence.name
            old_actions = self.current_sequence.actions
            
            self.current_sequence = self.sequence_builder.create_sequence(name, description)
            self.current_sequence.actions = old_actions
            
            # Eliminar secuencia anterior si existía
            if old_name:
                self.config_manager.delete_sequence(old_name)
        else:
            # Solo actualizar descripción
            self.current_sequence.description = description
        
        # Guardar secuencia
        if self._save_sequence_internal():
            messagebox.showinfo("Información", f"Secuencia '{name}' guardada correctamente")
            self.status_var.set(f"Secuencia '{name}' guardada")
        else:
            messagebox.showerror("Error", "Error al guardar la secuencia")
    
    def run_cli(self):
        """
        Ejecuta el asistente en modo línea de comandos.
        """
        print("=== Asistente de Secuencias para eFootball Automation ===")
        print("Este asistente te ayudará a crear secuencias de acciones personalizadas.")
        
        # Solicitar información básica
        name = input("Nombre de la secuencia: ").strip()
        if not name:
            print("Error: El nombre no puede estar vacío")
            return
        
        description = input("Descripción (opcional): ").strip()
        
        # Crear secuencia
        self.current_sequence = self.sequence_builder.create_sequence(name, description)
        
        print("\nCreando secuencia. Selecciona el tipo de acción a añadir:")
        
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
                    self._cli_add_button_press()
                elif choice == '2':
                    self._cli_add_wait_for_image()
                elif choice == '3':
                    self._cli_add_move_cursor()
                elif choice == '4':
                    self._cli_add_wait()
                else:
                    print("Opción no válida.")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Guardar secuencia
        self.sequence_builder.save_current_sequence()
        print(f"\nSecuencia '{name}' guardada correctamente.")
    
    def _cli_add_button_press(self):
        """
        Añade una acción de pulsación de botón en modo CLI.
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
    
    def _cli_add_wait_for_image(self):
        """
        Añade una acción de espera de imagen en modo CLI.
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
    
    def _cli_add_move_cursor(self):
        """
        Añade una acción de movimiento del cursor en modo CLI.
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
    
    def _cli_add_wait(self):
        """
        Añade una acción de espera en modo CLI.
        """
        seconds = input("Tiempo de espera (segundos): ")
        
        try:
            seconds = float(seconds)
            self.sequence_builder.add_wait(seconds)
            print(f"Acción añadida: Esperar {seconds} segundos")
        except ValueError:
            print("Tiempo no válido")


class ActionDialog:
    """
    Diálogo para añadir o editar una acción.
    """
    def __init__(self, parent, action_type=None, params=None):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Ventana padre
            action_type: Tipo de acción (para edición)
            params: Parámetros de la acción (para edición)
        """
        self.top = tk.Toplevel(parent)
        self.top.title("Acción")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.result = None
        self.action_type = action_type
        self.params = params or {}
        
        # Tipo de acción
        ttk.Label(self.top, text="Tipo de acción:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.type_var = tk.StringVar()
        if action_type:
            self.type_var.set(action_type)
        
        type_combo = ttk.Combobox(self.top, textvariable=self.type_var, state="readonly")
        type_combo["values"] = ("button_press", "wait_for_image", "move_cursor", "wait")
        type_combo.grid(row=0, column=1, padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # Frame para parámetros (cambia según el tipo)
        self.params_frame = ttk.Frame(self.top)
        self.params_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Botones
        btn_frame = ttk.Frame(self.top)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Aceptar", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Si se está editando, mostrar los parámetros
        if action_type:
            self._on_type_change(None)
        
        # Centrar diálogo
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def _on_type_change(self, event):
        """
        Maneja el cambio de tipo de acción.
        """
        # Limpiar frame de parámetros
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        action_type = self.type_var.get()
        
        if action_type == "button_press":
            self._create_button_press_params()
        elif action_type == "wait_for_image":
            self._create_wait_for_image_params()
        elif action_type == "move_cursor":
            self._create_move_cursor_params()
        elif action_type == "wait":
            self._create_wait_params()
    
    def _create_button_press_params(self):
        """
        Crea los widgets para los parámetros de pulsación de botón.
        """
        ttk.Label(self.params_frame, text="Botón:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.button_var = tk.StringVar()
        if 'button' in self.params:
            self.button_var.set(self.params['button'])
        
        button_combo = ttk.Combobox(self.params_frame, textvariable=self.button_var)
        button_combo["values"] = ("A", "B", "X", "Y", "LB", "RB", "LT", "RT", "START", "SELECT", 
                                 "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT")
        button_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.params_frame, text="Duración (s):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.duration_var = tk.StringVar()
        if 'duration' in self.params:
            self.duration_var.set(str(self.params['duration']))
        else:
            self.duration_var.set("0.1")
        
        ttk.Entry(self.params_frame, textvariable=self.duration_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    def _create_wait_for_image_params(self):
        """
        Crea los widgets para los parámetros de espera de imagen.
        """
        ttk.Label(self.params_frame, text="Imagen:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.image_var = tk.StringVar()
        if 'image_name' in self.params:
            self.image_var.set(self.params['image_name'])
        
        image_entry = ttk.Entry(self.params_frame, textvariable=self.image_var, width=30)
        image_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(self.params_frame, text="Examinar...", command=self._browse_image).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(self.params_frame, text="Timeout (s):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.timeout_var = tk.StringVar()
        if 'timeout' in self.params:
            self.timeout_var.set(str(self.params['timeout']))
        else:
            self.timeout_var.set("10.0")
        
        ttk.Entry(self.params_frame, textvariable=self.timeout_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    def _create_move_cursor_params(self):
        """
        Crea los widgets para los parámetros de movimiento del cursor.
        """
        ttk.Label(self.params_frame, text="Tipo de objetivo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.target_type_var = tk.StringVar()
        if 'target_type' in self.params:
            self.target_type_var.set(self.params['target_type'])
        else:
            self.target_type_var.set("image")
        
        target_combo = ttk.Combobox(self.params_frame, textvariable=self.target_type_var, state="readonly")
        target_combo["values"] = ("image", "coordinates", "element")
        target_combo.grid(row=0, column=1, padx=5, pady=5)
        target_combo.bind("<<ComboboxSelected>>", self._on_target_type_change)
        
        # Frame para parámetros específicos del tipo de objetivo
        self.target_params_frame = ttk.Frame(self.params_frame)
        self.target_params_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Mostrar parámetros según el tipo de objetivo
        self._on_target_type_change(None)
    
    def _on_target_type_change(self, event):
        """
        Maneja el cambio de tipo de objetivo para el movimiento del cursor.
        """
        # Limpiar frame de parámetros de objetivo
        for widget in self.target_params_frame.winfo_children():
            widget.destroy()
        
        target_type = self.target_type_var.get()
        
        if target_type == "image":
            ttk.Label(self.target_params_frame, text="Imagen:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            
            self.target_image_var = tk.StringVar()
            if 'image_name' in self.params:
                self.target_image_var.set(self.params['image_name'])
            
            ttk.Entry(self.target_params_frame, textvariable=self.target_image_var, width=30).grid(row=0, column=1, padx=5, pady=5)
            ttk.Button(self.target_params_frame, text="Examinar...", command=self._browse_target_image).grid(row=0, column=2, padx=5, pady=5)
        
        elif target_type == "coordinates":
            ttk.Label(self.target_params_frame, text="X:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            
            self.target_x_var = tk.StringVar()
            if 'x' in self.params:
                self.target_x_var.set(str(self.params['x']))
            
            ttk.Entry(self.target_params_frame, textvariable=self.target_x_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
            
            ttk.Label(self.target_params_frame, text="Y:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            
            self.target_y_var = tk.StringVar()
            if 'y' in self.params:
                self.target_y_var.set(str(self.params['y']))
            
            ttk.Entry(self.target_params_frame, textvariable=self.target_y_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        elif target_type == "element":
            ttk.Label(self.target_params_frame, text="ID del elemento:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            
            self.target_element_var = tk.StringVar()
            if 'element_id' in self.params:
                self.target_element_var.set(self.params['element_id'])
            
            ttk.Entry(self.target_params_frame, textvariable=self.target_element_var, width=30).grid(row=0, column=1, padx=5, pady=5)
    
    def _create_wait_params(self):
        """
        Crea los widgets para los parámetros de espera.
        """
        ttk.Label(self.params_frame, text="Tiempo (s):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.wait_seconds_var = tk.StringVar()
        if 'seconds' in self.params:
            self.wait_seconds_var.set(str(self.params['seconds']))
        else:
            self.wait_seconds_var.set("1.0")
        
        ttk.Entry(self.params_frame, textvariable=self.wait_seconds_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    def _browse_image(self):
        """
        Abre un diálogo para seleccionar una imagen.
        """
        filename = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if filename:
            self.image_var.set(os.path.basename(filename))
    
    def _browse_target_image(self):
        """
        Abre un diálogo para seleccionar una imagen objetivo.
        """
        filename = filedialog.askopenfilename(
            title="Seleccionar imagen objetivo",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if filename:
            self.target_image_var.set(os.path.basename(filename))
    
    def _on_ok(self):
        """
        Maneja el botón Aceptar.
        """
        action_type = self.type_var.get()
        
        if not action_type:
            messagebox.showerror("Error", "Selecciona un tipo de acción")
            return
        
        params = {}
        
        try:
            if action_type == "button_press":
                button = self.button_var.get()
                if not button:
                    messagebox.showerror("Error", "Selecciona un botón")
                    return
                
                params['button'] = button
                params['duration'] = float(self.duration_var.get())
            
            elif action_type == "wait_for_image":
                image_name = self.image_var.get()
                if not image_name:
                    messagebox.showerror("Error", "Especifica una imagen")
                    return
                
                params['image_name'] = image_name
                params['timeout'] = float(self.timeout_var.get())
            
            elif action_type == "move_cursor":
                target_type = self.target_type_var.get()
                params['target_type'] = target_type
                
                if target_type == "image":
                    image_name = self.target_image_var.get()
                    if not image_name:
                        messagebox.showerror("Error", "Especifica una imagen objetivo")
                        return
                    
                    params['image_name'] = image_name
                
                elif target_type == "coordinates":
                    params['x'] = int(self.target_x_var.get())
                    params['y'] = int(self.target_y_var.get())
                
                elif target_type == "element":
                    element_id = self.target_element_var.get()
                    if not element_id:
                        messagebox.showerror("Error", "Especifica un ID de elemento")
                        return
                    
                    params['element_id'] = element_id
            
            elif action_type == "wait":
                params['seconds'] = float(self.wait_seconds_var.get())
        
        except ValueError:
            messagebox.showerror("Error", "Valor numérico no válido")
            return
        
        self.result = (action_type, params)
        self.top.destroy()
    
    def _on_cancel(self):
        """
        Maneja el botón Cancelar.
        """
        self.top.destroy()


def main():
    """
    Función principal para ejecutar el asistente.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Asistente de Secuencias para eFootball Automation')
    parser.add_argument('--cli', action='store_true', help='Ejecutar en modo línea de comandos')
    
    args = parser.parse_args()
    
    wizard = SequenceWizard()
    
    if args.cli:
        wizard.run_cli()
    else:
        wizard.start_gui()


if __name__ == "__main__":
    main()
