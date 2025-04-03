"""
Módulo de inicialización para el paquete de interfaz de configuración.

Este módulo permite importar las clases principales del paquete de configuración.
"""

from .config_manager import ConfigManager, SequenceBuilder, ActionSequence, ActionExecutor
from .config_cli import ConfigCLI

__all__ = [
    'ConfigManager',
    'SequenceBuilder',
    'ActionSequence',
    'ActionExecutor',
    'ConfigCLI'
]
