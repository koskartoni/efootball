"""
Sistema de archivos de configuración para eFootball Automation.

Este módulo proporciona funcionalidades para gestionar archivos de configuración
que permiten personalizar el comportamiento de la aplicación para diferentes
escenarios del juego eFootball.
"""

import os
import json
import yaml
import logging
import shutil
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_system')

class ConfigSystem:
    """
    Sistema de gestión de archivos de configuración para eFootball Automation.
    """
    def __init__(self, base_dir: str = None):
        """
        Inicializa el sistema de configuración.
        
        Args:
            base_dir: Directorio base para los archivos de configuración
        """
        if base_dir is None:
            # Directorio por defecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, 'config')
        self.profiles_dir = os.path.join(self.config_dir, 'profiles')
        self.templates_dir = os.path.join(self.config_dir, 'templates')
        self.sequences_dir = os.path.join(self.config_dir, 'sequences')
        self.settings_file = os.path.join(self.config_dir, 'settings.yaml')
        
        # Crear directorios si no existen
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.sequences_dir, exist_ok=True)
        
        # Cargar configuración global
        self.settings = self._load_settings()
        
        # Perfil activo
        self.active_profile = self.settings.get('active_profile', 'default')
        
        # Cargar perfil activo
        self.profile = self._load_profile(self.active_profile)
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Carga la configuración global desde el archivo settings.yaml.
        
        Returns:
            Diccionario con la configuración global
        """
        if not os.path.exists(self.settings_file):
            # Crear configuración por defecto
            default_settings = {
                'active_profile': 'default',
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
                    'precision_threshold': 10,  # píxeles
                    'max_attempts': 3,
                    'move_delay': 0.05,
                    'acceleration': 1.5,
                    'deceleration': 0.5,
                    'element_detection_confidence': 0.7,
                    'use_adaptive_speed': True,
                    'use_path_correction': True,
                    'debug_mode': False
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
        # Asegurar que el perfil activo esté actualizado
        self.settings['active_profile'] = self.active_profile
        
        with open(self.settings_file, 'w') as f:
            yaml.dump(self.settings, f, default_flow_style=False)
        
        logger.info(f"Configuración global guardada en {self.settings_file}")
    
    def _load_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Carga un perfil de configuración.
        
        Args:
            profile_name: Nombre del perfil
            
        Returns:
            Diccionario con la configuración del perfil
        """
        profile_file = os.path.join(self.profiles_dir, f"{profile_name}.yaml")
        
        if not os.path.exists(profile_file):
            # Crear perfil por defecto
            default_profile = {
                'name': profile_name,
                'description': f"Perfil de configuración {profile_name}",
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'menu_paths': {
                    'main_to_contract': ['Contrato'],
                    'main_to_my_team': ['Mi equipo'],
                    'main_to_match': ['Partido'],
                    'contract_to_normal_players': ['Jugadores normales'],
                    'my_team_to_player_list': ['Jugadores'],
                    'my_team_to_player_training': ['Jugadores', 'Seleccionar jugador', 'Entrenar']
                },
                'screen_elements': {
                    'main_menu': {
                        'contract_button': {'type': 'image', 'value': 'Menu_principal_sel_contratacion.png'},
                        'match_button': {'type': 'image', 'value': 'Menu_principal_sel_Partido.png'},
                        'my_team_button': {'type': 'image', 'value': 'Mi_equipo.png'}
                    },
                    'contract_menu': {
                        'normal_players_button': {'type': 'image', 'value': 'Menu_contratos_1.png'}
                    },
                    'player_list': {
                        'sort_button': {'type': 'image', 'value': 'Mi_equipo_jugadores_accion_ordenar_1.png'}
                    }
                },
                'sequences': {
                    'skip_banners': 'skip_banners',
                    'sign_player': 'sign_player',
                    'train_player': 'train_player',
                    'play_match': 'play_match'
                },
                'custom_settings': {
                    'default_player_position': 'Delantero',
                    'default_player_club': 'Barcelona',
                    'default_training_type': 'Habilidad',
                    'auto_skip_banners': True,
                    'auto_confirm_purchases': True
                }
            }
            
            with open(profile_file, 'w') as f:
                yaml.dump(default_profile, f, default_flow_style=False)
            
            return default_profile
        
        with open(profile_file, 'r') as f:
            profile = yaml.safe_load(f)
            
            # Actualizar fecha de último acceso
            profile['last_accessed'] = datetime.now().isoformat()
            
            with open(profile_file, 'w') as f:
                yaml.dump(profile, f, default_flow_style=False)
            
            return profile
    
    def save_profile(self) -> None:
        """
        Guarda el perfil activo.
        """
        profile_file = os.path.join(self.profiles_dir, f"{self.active_profile}.yaml")
        
        # Actualizar fecha de modificación
        self.profile['updated_at'] = datetime.now().isoformat()
        
        with open(profile_file, 'w') as f:
            yaml.dump(self.profile, f, default_flow_style=False)
        
        logger.info(f"Perfil '{self.active_profile}' guardado en {profile_file}")
    
    def create_profile(self, name: str, description: str = None, base_profile: str = None) -> bool:
        """
        Crea un nuevo perfil de configuración.
        
        Args:
            name: Nombre del nuevo perfil
            description: Descripción del perfil
            base_profile: Perfil base para copiar configuración
            
        Returns:
            True si se creó correctamente, False en caso contrario
        """
        if name in self.list_profiles():
            logger.error(f"Ya existe un perfil con el nombre '{name}'")
            return False
        
        # Crear nuevo perfil
        if base_profile and base_profile in self.list_profiles():
            # Copiar perfil base
            base_profile_file = os.path.join(self.profiles_dir, f"{base_profile}.yaml")
            new_profile_file = os.path.join(self.profiles_dir, f"{name}.yaml")
            
            shutil.copy(base_profile_file, new_profile_file)
            
            # Cargar y modificar
            with open(new_profile_file, 'r') as f:
                profile = yaml.safe_load(f)
            
            profile['name'] = name
            if description:
                profile['description'] = description
            profile['created_at'] = datetime.now().isoformat()
            profile['updated_at'] = datetime.now().isoformat()
            
            with open(new_profile_file, 'w') as f:
                yaml.dump(profile, f, default_flow_style=False)
        else:
            # Crear perfil desde cero
            self.active_profile = name
            self.profile = self._load_profile(name)
            
            if description:
                self.profile['description'] = description
            
            self.save_profile()
        
        logger.info(f"Perfil '{name}' creado correctamente")
        return True
    
    def delete_profile(self, name: str) -> bool:
        """
        Elimina un perfil de configuración.
        
        Args:
            name: Nombre del perfil a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        if name == 'default':
            logger.error("No se puede eliminar el perfil por defecto")
            return False
        
        profile_file = os.path.join(self.profiles_dir, f"{name}.yaml")
        
        if not os.path.exists(profile_file):
            logger.error(f"No existe un perfil con el nombre '{name}'")
            return False
        
        # Eliminar archivo
        os.remove(profile_file)
        
        # Si era el perfil activo, cambiar al perfil por defecto
        if self.active_profile == name:
            self.active_profile = 'default'
            self.profile = self._load_profile('default')
            self.save_settings()
        
        logger.info(f"Perfil '{name}' eliminado correctamente")
        return True
    
    def switch_profile(self, name: str) -> bool:
        """
        Cambia al perfil especificado.
        
        Args:
            name: Nombre del perfil
            
        Returns:
            True si se cambió correctamente, False en caso contrario
        """
        if name not in self.list_profiles():
            logger.error(f"No existe un perfil con el nombre '{name}'")
            return False
        
        # Guardar perfil actual
        self.save_profile()
        
        # Cambiar al nuevo perfil
        self.active_profile = name
        self.profile = self._load_profile(name)
        
        # Actualizar configuración global
        self.settings['active_profile'] = name
        self.save_settings()
        
        logger.info(f"Cambiado al perfil '{name}'")
        return True
    
    def list_profiles(self) -> List[str]:
        """
        Lista todos los perfiles disponibles.
        
        Returns:
            Lista de nombres de perfiles
        """
        profiles = []
        
        for file_name in os.listdir(self.profiles_dir):
            if file_name.endswith('.yaml'):
                profiles.append(file_name[:-5])  # Eliminar extensión .yaml
        
        return profiles
    
    def get_profile_info(self, name: str = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene información básica de un perfil.
        
        Args:
            name: Nombre del perfil (si es None, usa el perfil activo)
            
        Returns:
            Diccionario con información del perfil o None si no existe
        """
        if name is None:
            name = self.active_profile
        
        profile_file = os.path.join(self.profiles_dir, f"{name}.yaml")
        
        if not os.path.exists(profile_file):
            return None
        
        with open(profile_file, 'r') as f:
            profile = yaml.safe_load(f)
            
            # Devolver solo información básica
            return {
                'name': profile.get('name', name),
                'description': profile.get('description', ''),
                'created_at': profile.get('created_at', ''),
                'updated_at': profile.get('updated_at', ''),
                'last_accessed': profile.get('last_accessed', '')
            }
    
    def get_menu_path(self, path_id: str) -> Optional[List[str]]:
        """
        Obtiene una ruta de menú del perfil activo.
        
        Args:
            path_id: Identificador de la ruta de menú
            
        Returns:
            Lista de opciones de menú o None si no existe
        """
        if 'menu_paths' not in self.profile:
            return None
        
        return self.profile['menu_paths'].get(path_id)
    
    def set_menu_path(self, path_id: str, menu_path: List[str]) -> None:
        """
        Establece una ruta de menú en el perfil activo.
        
        Args:
            path_id: Identificador de la ruta de menú
            menu_path: Lista de opciones de menú
        """
        if 'menu_paths' not in self.profile:
            self.profile['menu_paths'] = {}
        
        self.profile['menu_paths'][path_id] = menu_path
        self.save_profile()
    
    def get_screen_element(self, menu_id: str, element_id: str) -> Optional[Dict[str, str]]:
        """
        Obtiene información de un elemento de pantalla.
        
        Args:
            menu_id: Identificador del menú
            element_id: Identificador del elemento
            
        Returns:
            Diccionario con información del elemento o None si no existe
        """
        if 'screen_elements' not in self.profile:
            return None
        
        if menu_id not in self.profile['screen_elements']:
            return None
        
        return self.profile['screen_elements'][menu_id].get(element_id)
    
    def set_screen_element(self, menu_id: str, element_id: str, element_info: Dict[str, str]) -> None:
        """
        Establece información de un elemento de pantalla.
        
        Args:
            menu_id: Identificador del menú
            element_id: Identificador del elemento
            element_info: Diccionario con información del elemento
        """
        if 'screen_elements' not in self.profile:
            self.profile['screen_elements'] = {}
        
        if menu_id not in self.profile['screen_elements']:
            self.profile['screen_elements'][menu_id] = {}
        
        self.profile['screen_elements'][menu_id][element_id] = element_info
        self.save_profile()
    
    def get_sequence_name(self, sequence_id: str) -> Optional[str]:
        """
        Obtiene el nombre de una secuencia del perfil activo.
        
        Args:
            sequence_id: Identificador de la secuencia
            
        Returns:
            Nombre de la secuencia o None si no existe
        """
        if 'sequences' not in self.profile:
            return None
        
        return self.profile['sequences'].get(sequence_id)
    
    def set_sequence_name(self, sequence_id: str, sequence_name: str) -> None:
        """
        Establece el nombre de una secuencia en el perfil activo.
        
        Args:
            sequence_id: Identificador de la secuencia
            sequence_name: Nombre de la secuencia
        """
        if 'sequences' not in self.profile:
            self.profile['sequences'] = {}
        
        self.profile['sequences'][sequence_id] = sequence_name
        self.save_profile()
    
    def get_custom_setting(self, setting_id: str) -> Any:
        """
        Obtiene una configuración personalizada del perfil activo.
        
        Args:
            setting_id: Identificador de la configuración
            
        Returns:
            Valor de la configuración o None si no existe
        """
        if 'custom_settings' not in self.profile:
            return None
        
        return self.profile['custom_settings'].get(setting_id)
    
    def set_custom_setting(self, setting_id: str, value: Any) -> None:
        """
        Establece una configuración personalizada en el perfil activo.
        
        Args:
            setting_id: Identificador de la configuración
            value: Valor de la configuración
        """
        if 'custom_settings' not in self.profile:
            self.profile['custom_settings'] = {}
        
        self.profile['custom_settings'][setting_id] = value
        self.save_profile()
    
    def export_profile(self, name: str, export_file: str) -> bool:
        """
        Exporta un perfil a un archivo.
        
        Args:
            name: Nombre del perfil
            export_file: Ruta del archivo de exportación
            
        Returns:
            True si se exportó correctamente, False en caso contrario
        """
        if name not in self.list_profiles():
            logger.error(f"No existe un perfil con el nombre '{name}'")
            return False
        
        profile_file = os.path.join(self.profiles_dir, f"{name}.yaml")
        
        try:
            shutil.copy(profile_file, export_file)
            logger.info(f"Perfil '{name}' exportado a {export_file}")
            return True
        except Exception as e:
            logger.error(f"Error al exportar perfil: {str(e)}")
            return False
    
    def import_profile(self, import_file: str, new_name: str = None) -> bool:
        """
        Importa un perfil desde un archivo.
        
        Args:
            import_file: Ruta del archivo de importación
            new_name: Nuevo nombre para el perfil importado
            
        Returns:
            True si se importó correctamente, False en caso contrario
        """
        if not os.path.exists(import_file):
            logger.error(f"No existe el archivo {import_file}")
            return False
        
        try:
            # Cargar perfil desde archivo
            with open(import_file, 'r') as f:
                profile = yaml.safe_load(f)
            
            # Obtener nombre del perfil
            if new_name:
                profile_name = new_name
            else:
                profile_name = profile.get('name', os.path.basename(import_file).split('.')[0])
            
            # Verificar si ya existe
            if profile_name in self.list_profiles() and profile_name != 'default':
                logger.warning(f"Ya existe un perfil con el nombre '{profile_name}', se sobrescribirá")
            
            # Actualizar información
            profile['name'] = profile_name
            profile['imported_at'] = datetime.now().isoformat()
            profile['updated_at'] = datetime.now().isoformat()
            
            # Guardar perfil
            profile_file = os.path.join(self.profiles_dir, f"{profile_name}.yaml")
            with open(profile_file, 'w') as f:
                yaml.dump(profile, f, default_flow_style=False)
            
            logger.info(f"Perfil importado como '{profile_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Error al importar perfil: {str(e)}")
            return False
    
    def create_template(self, name: str, description: str, content: Dict[str, Any]) -> bool:
        """
        Crea una plantilla de configuración.
        
        Args:
            name: Nombre de la plantilla
            description: Descripción de la plantilla
            content: Contenido de la plantilla
            
        Returns:
            True si se creó correctamente, False en caso contrario
        """
        template_file = os.path.join(self.templates_dir, f"{name}.yaml")
        
        if os.path.exists(template_file):
            logger.error(f"Ya existe una plantilla con el nombre '{name}'")
            return False
        
        # Crear plantilla
        template = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'content': content
        }
        
        with open(template_file, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
        
        logger.info(f"Plantilla '{name}' creada correctamente")
        return True
    
    def apply_template(self, template_name: str, target_section: str = None) -> bool:
        """
        Aplica una plantilla al perfil activo.
        
        Args:
            template_name: Nombre de la plantilla
            target_section: Sección específica a la que aplicar la plantilla
            
        Returns:
            True si se aplicó correctamente, False en caso contrario
        """
        template_file = os.path.join(self.templates_dir, f"{template_name}.yaml")
        
        if not os.path.exists(template_file):
            logger.error(f"No existe una plantilla con el nombre '{template_name}'")
            return False
        
        try:
            # Cargar plantilla
            with open(template_file, 'r') as f:
                template = yaml.safe_load(f)
            
            content = template.get('content', {})
            
            # Aplicar plantilla
            if target_section:
                if target_section not in self.profile:
                    self.profile[target_section] = {}
                
                # Actualizar solo la sección especificada
                if target_section in content:
                    self.profile[target_section].update(content[target_section])
            else:
                # Actualizar todo el perfil
                for section, section_content in content.items():
                    if section not in self.profile:
                        self.profile[section] = {}
                    
                    if isinstance(section_content, dict):
                        self.profile[section].update(section_content)
                    else:
                        self.profile[section] = section_content
            
            # Guardar perfil
            self.save_profile()
            
            logger.info(f"Plantilla '{template_name}' aplicada correctamente al perfil '{self.active_profile}'")
            return True
        
        except Exception as e:
            logger.error(f"Error al aplicar plantilla: {str(e)}")
            return False
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        Lista todas las plantillas disponibles.
        
        Returns:
            Lista de diccionarios con información de las plantillas
        """
        templates = []
        
        for file_name in os.listdir(self.templates_dir):
            if file_name.endswith('.yaml'):
                template_name = file_name[:-5]  # Eliminar extensión .yaml
                template_file = os.path.join(self.templates_dir, file_name)
                
                try:
                    with open(template_file, 'r') as f:
                        template = yaml.safe_load(f)
                    
                    templates.append({
                        'name': template_name,
                        'description': template.get('description', ''),
                        'created_at': template.get('created_at', '')
                    })
                except Exception:
                    # Si hay error al cargar, incluir solo el nombre
                    templates.append({
                        'name': template_name,
                        'description': 'Error al cargar plantilla',
                        'created_at': ''
                    })
        
        return templates
    
    def backup_all_profiles(self, backup_dir: str = None) -> str:
        """
        Crea una copia de seguridad de todos los perfiles.
        
        Args:
            backup_dir: Directorio donde guardar la copia de seguridad
            
        Returns:
            Ruta del archivo de copia de seguridad
        """
        if backup_dir is None:
            backup_dir = os.path.join(self.base_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"profiles_backup_{timestamp}.zip")
        
        # Crear archivo ZIP
        import zipfile
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            # Añadir configuración global
            zipf.write(self.settings_file, os.path.basename(self.settings_file))
            
            # Añadir perfiles
            for profile_name in self.list_profiles():
                profile_file = os.path.join(self.profiles_dir, f"{profile_name}.yaml")
                zipf.write(profile_file, os.path.join('profiles', os.path.basename(profile_file)))
            
            # Añadir plantillas
            for template in self.list_templates():
                template_file = os.path.join(self.templates_dir, f"{template['name']}.yaml")
                zipf.write(template_file, os.path.join('templates', os.path.basename(template_file)))
        
        logger.info(f"Copia de seguridad creada en {backup_file}")
        return backup_file
    
    def restore_from_backup(self, backup_file: str, overwrite: bool = False) -> bool:
        """
        Restaura perfiles desde una copia de seguridad.
        
        Args:
            backup_file: Ruta del archivo de copia de seguridad
            overwrite: Si True, sobrescribe perfiles existentes
            
        Returns:
            True si se restauró correctamente, False en caso contrario
        """
        if not os.path.exists(backup_file):
            logger.error(f"No existe el archivo de copia de seguridad {backup_file}")
            return False
        
        try:
            import zipfile
            import tempfile
            
            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraer archivo ZIP
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Restaurar configuración global
                settings_file = os.path.join(temp_dir, os.path.basename(self.settings_file))
                if os.path.exists(settings_file):
                    if overwrite:
                        shutil.copy(settings_file, self.settings_file)
                    else:
                        # Cargar y combinar configuraciones
                        with open(settings_file, 'r') as f:
                            backup_settings = yaml.safe_load(f)
                        
                        # Mantener perfil activo actual
                        active_profile = self.settings.get('active_profile')
                        
                        # Actualizar configuración
                        self.settings.update(backup_settings)
                        
                        # Restaurar perfil activo
                        if active_profile:
                            self.settings['active_profile'] = active_profile
                        
                        # Guardar configuración
                        self.save_settings()
                
                # Restaurar perfiles
                profiles_dir = os.path.join(temp_dir, 'profiles')
                if os.path.exists(profiles_dir):
                    for file_name in os.listdir(profiles_dir):
                        if file_name.endswith('.yaml'):
                            profile_name = file_name[:-5]  # Eliminar extensión .yaml
                            source_file = os.path.join(profiles_dir, file_name)
                            target_file = os.path.join(self.profiles_dir, file_name)
                            
                            if not os.path.exists(target_file) or overwrite:
                                shutil.copy(source_file, target_file)
                
                # Restaurar plantillas
                templates_dir = os.path.join(temp_dir, 'templates')
                if os.path.exists(templates_dir):
                    for file_name in os.listdir(templates_dir):
                        if file_name.endswith('.yaml'):
                            source_file = os.path.join(templates_dir, file_name)
                            target_file = os.path.join(self.templates_dir, file_name)
                            
                            if not os.path.exists(target_file) or overwrite:
                                shutil.copy(source_file, target_file)
            
            # Recargar configuración
            self.settings = self._load_settings()
            self.active_profile = self.settings.get('active_profile', 'default')
            self.profile = self._load_profile(self.active_profile)
            
            logger.info(f"Restauración desde {backup_file} completada correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al restaurar desde copia de seguridad: {str(e)}")
            return False


# Ejemplo de uso
if __name__ == "__main__":
    # Este código se ejecutaría solo si se ejecuta el módulo directamente
    config_system = ConfigSystem()
    
    print("Sistema de archivos de configuración para eFootball Automation")
    print(f"Perfil activo: {config_system.active_profile}")
    print(f"Perfiles disponibles: {config_system.list_profiles()}")
    
    # Crear un perfil de ejemplo
    if "ejemplo" not in config_system.list_profiles():
        config_system.create_profile("ejemplo", "Perfil de ejemplo para demostración")
        config_system.switch_profile("ejemplo")
        
        # Configurar algunas opciones
        config_system.set_custom_setting("default_player_position", "Mediocampista")
        config_system.set_custom_setting("default_player_club", "Real Madrid")
        
        print("\nPerfil de ejemplo creado y configurado")
    
    # Mostrar información del perfil activo
    print("\nInformación del perfil activo:")
    print(config_system.get_profile_info())
    
    # Mostrar configuración personalizada
    print("\nConfiguración personalizada:")
    print(f"Posición por defecto: {config_system.get_custom_setting('default_player_position')}")
    print(f"Club por defecto: {config_system.get_custom_setting('default_player_club')}")
    
    # Volver al perfil por defecto
    config_system.switch_profile("default")
    print(f"\nVuelto al perfil por defecto: {config_system.active_profile}")
