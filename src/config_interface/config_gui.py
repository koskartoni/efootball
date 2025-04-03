"""
Interfaz gráfica para la configuración de acciones en eFootball.

Este módulo proporciona una interfaz gráfica de usuario para crear, editar,
y gestionar secuencias de acciones personalizadas para la automatización de eFootball.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Añadir el directorio padre al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar el gestor de configuraciones
from config_interface.config_manager import ConfigManager, SequenceBuilder, ActionSequence

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_interface.gui')

class ConfigGUI:
    """
    Interfaz gráfica para la configuración de acciones.
    """
    def __init__(self, root):
        """
        Inicializa la interfaz gráfica.
        
        Args:
            root: Ventana principal de Tkinter
        """
        self.root = root
        self.root.title("Configuración de eFootball Automation")
        self.root.geometry("800x600")
        
        self.config_manager = ConfigManager()
        self.sequence_builder = SequenceBuilder(self.config_manager)
        self.current_sequence = None
        
        self._create_widgets()
        self._update_sequence_list()
    
    def _create_widgets(self):
        """
        Crea los widgets de la interfaz gráfica.
        """
        # Frame principal con dos paneles
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo: Lista de secuencias
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)
        
        # Panel derecho: Detalles de secuencia
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=2)
        
        # --- Panel izquierdo ---
        ttk.Label(left_frame, text="Secuencias disponibles").pack(pady=5)
        
        # Botones para gestionar secuencias
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Nueva", command=self._new_sequence).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Editar", command=self._edit_sequence).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Eliminar", command=self._delete_sequence).pack(side=tk.LEFT, padx=2)
        
        # Lista de secuencias
        self.sequence_listbox = tk.Listbox(left_frame)
        self.sequence_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.sequence_listbox.bind('<<ListboxSelect>>', self._on_sequence_select)
        
        # --- Panel derecho ---
        # Información de la secuencia
        info_frame = ttk.LabelFrame(right_frame, text="Información de la secuencia")
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, state="readonly").grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Descripción:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.desc_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.desc_var, state="readonly").grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
        # Lista de acciones
        actions_frame = ttk.LabelFrame(right_frame, text="Acciones")
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Botones para gestionar acciones
        action_btn_frame = ttk.Frame(actions_frame)
        action_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_btn_frame, text="Añadir acción", command=self._add_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Editar acción", command=self._edit_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Eliminar acción", command=self._delete_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Mover arriba", command=self._move_action_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_btn_frame, text="Mover abajo", command=self._move_action_down).pack(side=tk.LEFT, padx=2)
        
        # Treeview para mostrar acciones
        self.actions_tree = ttk.Treeview(actions_frame, columns=("type", "details"), show="headings")
        self.actions_tree.heading("type", text="Tipo")
        self.actions_tree.heading("details", text="Detalles")
        self.actions_tree.column("type", width=100)
        self.actions_tree.column("details", width=400)
        self.actions_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Botones de guardar/cancelar
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=self._save_sequence).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel_edit).pack(side=tk.RIGHT, padx=5)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def _update_sequence_list(self):
        """
        Actualiza la lista de secuencias disponibles.
        """
        self.sequence_listbox.delete(0, tk.END)
        
        sequences = self.config_manager.list_sequences()
        for name in sequences:
            self.sequence_listbox.insert(tk.END, name)
    
    def _on_sequence_select(self, event):
        """
        Maneja la selección de una secuencia en la lista.
        """
        selection = self.sequence_listbox.curselection()
        if not selection:
            return
        
        name = self.sequence_listbox.get(selection[0])
        sequence = self.config_manager.load_sequence(name)
        
        if sequence:
            self.current_sequence = sequence
            self.name_var.set(sequence.name)
            self.desc_var.set(sequence.description)
            self._update_actions_tree()
    
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
    
    def _new_sequence(self):
        """
        Crea una nueva secuencia.
        """
        dialog = NewSequenceDialog(self.root)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            name, description = dialog.result
            
            # Verificar si ya existe
            if name in self.config_manager.list_sequences():
                messagebox.showerror("Error", f"Ya existe una secuencia con el nombre '{name}'")
                return
            
            # Crear nueva secuencia
            self.current_sequence = self.sequence_builder.create_sequence(name, description)
            self.name_var.set(name)
            self.desc_var.set(description)
            self._update_actions_tree()
            self.status_var.set(f"Nueva secuencia '{name}' creada")
    
    def _edit_sequence(self):
        """
        Edita la secuencia seleccionada.
        """
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una secuencia para editar")
            return
        
        name = self.sequence_listbox.get(selection[0])
        sequence = self.config_manager.load_sequence(name)
        
        if sequence:
            dialog = EditSequenceDialog(self.root, sequence.name, sequence.description)
            self.root.wait_window(dialog.top)
            
            if dialog.result:
                new_name, new_description = dialog.result
                
                # Verificar si el nuevo nombre ya existe (si cambió)
                if new_name != name and new_name in self.config_manager.list_sequences():
                    messagebox.showerror("Error", f"Ya existe una secuencia con el nombre '{new_name}'")
                    return
                
                # Actualizar secuencia
                self.current_sequence = self.sequence_builder.create_sequence(new_name, new_description)
                self.current_sequence.actions = sequence.actions
                
                # Si cambió el nombre, eliminar la secuencia anterior
                if new_name != name:
                    self.config_manager.delete_sequence(name)
                
                # Guardar la secuencia actualizada
                self.sequence_builder.save_current_sequence()
                self._update_sequence_list()
                self.name_var.set(new_name)
                self.desc_var.set(new_description)
                self._update_actions_tree()
                self.status_var.set(f"Secuencia '{new_name}' actualizada")
    
    def _delete_sequence(self):
        """
        Elimina la secuencia seleccionada.
        """
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una secuencia para eliminar")
            return
        
        name = self.sequence_listbox.get(selection[0])
        
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que quieres eliminar la secuencia '{name}'?"):
            if self.config_manager.delete_sequence(name):
                self._update_sequence_list()
                
                if self.current_sequence and self.current_sequence.name == name:
                    self.current_sequence = None
                    self.name_var.set("")
                    self.desc_var.set("")
                    self._update_actions_tree()
                
                self.status_var.set(f"Secuencia '{name}' eliminada")
            else:
                messagebox.showerror("Error", f"No se pudo eliminar la secuencia '{name}'")
    
    def _add_action(self):
        """
        Añade una acción a la secuencia actual.
        """
        if not self.current_sequence:
            messagebox.showwarning("Advertencia", "Selecciona o crea una secuencia primero")
            return
        
        dialog = ActionDialog(self.root)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            action_type, params = dialog.result
            
            # Añadir acción a la secuencia
            self.current_sequence.add_action(action_type, **params)
            self._update_actions_tree()
            self.status_var.set(f"Acción '{action_type}' añadida")
    
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
    
    def _save_sequence(self):
        """
        Guarda la secuencia actual.
        """
        if not self.current_sequence:
            return
        
        self.sequence_builder.current_sequence = self.current_sequence
        self.sequence_builder.save_current_sequence()
        self._update_sequence_list()
        self.status_var.set(f"Secuencia '{self.current_sequence.name}' guardada")
    
    def _cancel_edit(self):
        """
        Cancela la edición de la secuencia actual.
        """
        selection = self.sequence_listbox.curselection()
        if selection:
            name = self.sequence_listbox.get(selection[0])
            sequence = self.config_manager.load_sequence(name)
            
            if sequence:
                self.current_sequence = sequence
                self.name_var.set(sequence.name)
                self.desc_var.set(sequence.description)
                self._update_actions_tree()
                self.status_var.set("Cambios descartados")
        else:
            self.current_sequence = None
            self.name_var.set("")
            self.desc_var.set("")
            self._update_actions_tree()
            self.status_var.set("Edición cancelada")


class NewSequenceDialog:
    """
    Diálogo para crear una nueva secuencia.
    """
    def __init__(self, parent):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Ventana padre
        """
        self.top = tk.Toplevel(parent)
        self.top.title("Nueva secuencia")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.result = None
        
        # Campos
        ttk.Label(self.top, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.top, text="Descripción:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.desc_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        
        # Botones
        btn_frame = ttk.Frame(self.top)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Aceptar", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Centrar diálogo
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def _on_ok(self):
        """
        Maneja el botón Aceptar.
        """
        name = self.name_var.get().strip()
        description = self.desc_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "El nombre no puede estar vacío")
            return
        
        self.result = (name, description)
        self.top.destroy()
    
    def _on_cancel(self):
        """
        Maneja el botón Cancelar.
        """
        self.top.destroy()


class EditSequenceDialog(NewSequenceDialog):
    """
    Diálogo para editar una secuencia existente.
    """
    def __init__(self, parent, name, description):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Ventana padre
            name: Nombre actual de la secuencia
            description: Descripción actual de la secuencia
        """
        super().__init__(parent)
        self.top.title("Editar secuencia")
        
        self.name_var.set(name)
        self.desc_var.set(description)


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
    Función principal para ejecutar la interfaz gráfica.
    """
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
