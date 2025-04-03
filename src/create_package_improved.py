"""
Script para crear un paquete de distribución mejorado de la aplicación de automatización de eFootball

Este script crea un archivo ZIP con todos los componentes necesarios para
que el usuario pueda instalar y utilizar la versión mejorada de la aplicación.
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_distribution_package():
    """
    Crea un paquete de distribución con todos los archivos necesarios.
    """
    print("Creando paquete de distribución mejorado...")
    
    # Directorios
    base_dir = "/home/ubuntu/efootball_automation"
    src_dir = os.path.join(base_dir, "src")
    config_interface_dir = os.path.join(src_dir, "config_interface")
    images_dir = os.path.join(base_dir, "images")
    dist_dir = os.path.join(base_dir, "dist")
    
    # Asegurar que el directorio de distribución existe
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # Nombre del archivo ZIP
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = os.path.join(dist_dir, f"efootball_automation_mejorado_{timestamp}.zip")
    
    # Crear el archivo ZIP
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Añadir README.md
        readme_path = os.path.join(base_dir, "README.md")
        if os.path.exists(readme_path):
            zipf.write(readme_path, os.path.basename(readme_path))
            print(f"Añadido: {os.path.basename(readme_path)}")
        
        # Añadir archivos de código fuente
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    # Determinar la ruta relativa para mantener la estructura de directorios
                    rel_path = os.path.relpath(file_path, base_dir)
                    zipf.write(file_path, rel_path)
                    print(f"Añadido: {rel_path}")
        
        # Añadir imágenes
        for root, _, files in os.walk(images_dir):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, base_dir)
                    zipf.write(file_path, rel_path)
                    print(f"Añadido: {rel_path}")
        
        # Crear y añadir un archivo requirements.txt
        requirements_path = os.path.join(base_dir, "requirements.txt")
        with open(requirements_path, 'w') as req_file:
            req_file.write("opencv-python>=4.5.0\n")
            req_file.write("numpy>=1.19.0\n")
            req_file.write("pyautogui>=0.9.52\n")
            req_file.write("vgamepad>=0.0.8\n")
            req_file.write("inputs>=0.5\n")
            req_file.write("pygame>=2.0.0\n")
            req_file.write("pynput>=1.7.6\n")
            req_file.write("pyyaml>=6.0\n")
            req_file.write("pillow>=9.0.0\n")
            req_file.write("pytesseract>=0.3.8\n")
        
        zipf.write(requirements_path, os.path.basename(requirements_path))
        print(f"Añadido: {os.path.basename(requirements_path)}")
        
        # Crear y añadir un script de instalación para Windows
        install_script_path = os.path.join(base_dir, "install.bat")
        with open(install_script_path, 'w') as install_file:
            install_file.write("@echo off\n")
            install_file.write("echo Instalando dependencias para la automatización de eFootball...\n")
            install_file.write("pip install -r requirements.txt\n")
            install_file.write("echo Instalación completada.\n")
            install_file.write("echo Para ejecutar la aplicación, use: python src/main.py --help\n")
            install_file.write("echo Para usar el asistente de configuración, use: python src/sequence_wizard.py\n")
            install_file.write("pause\n")
        
        zipf.write(install_script_path, os.path.basename(install_script_path))
        print(f"Añadido: {os.path.basename(install_script_path)}")
        
        # Crear y añadir un script de ejecución para Windows
        run_script_path = os.path.join(base_dir, "run.bat")
        with open(run_script_path, 'w') as run_file:
            run_file.write("@echo off\n")
            run_file.write("echo Ejecutando la aplicación de automatización de eFootball...\n")
            run_file.write("python src/main.py %*\n")
            run_file.write("pause\n")
        
        zipf.write(run_script_path, os.path.basename(run_script_path))
        print(f"Añadido: {os.path.basename(run_script_path)}")
        
        # Crear y añadir un script para ejecutar el asistente de configuración
        wizard_script_path = os.path.join(base_dir, "wizard.bat")
        with open(wizard_script_path, 'w') as wizard_file:
            wizard_file.write("@echo off\n")
            wizard_file.write("echo Iniciando el asistente de configuración de eFootball Automation...\n")
            wizard_file.write("python src/sequence_wizard.py\n")
            wizard_file.write("pause\n")
        
        zipf.write(wizard_script_path, os.path.basename(wizard_script_path))
        print(f"Añadido: {os.path.basename(wizard_script_path)}")
        
        # Crear y añadir un archivo de instrucciones rápidas
        quickstart_path = os.path.join(base_dir, "QUICKSTART.md")
        with open(quickstart_path, 'w') as quickstart_file:
            quickstart_file.write("# Inicio Rápido - Automatización de eFootball (Versión Mejorada)\n\n")
            quickstart_file.write("## Instalación\n\n")
            quickstart_file.write("1. Extraiga todos los archivos de este ZIP en una carpeta.\n")
            quickstart_file.write("2. Ejecute `install.bat` para instalar las dependencias necesarias.\n\n")
            quickstart_file.write("## Uso\n\n")
            quickstart_file.write("### Método 1: Usando el Asistente de Configuración (Recomendado)\n\n")
            quickstart_file.write("Ejecute `wizard.bat` para iniciar el asistente gráfico que le permitirá:\n\n")
            quickstart_file.write("- Crear secuencias personalizadas de acciones\n")
            quickstart_file.write("- Grabar acciones automáticamente\n")
            quickstart_file.write("- Configurar movimientos precisos del cursor\n")
            quickstart_file.write("- Guardar y cargar configuraciones\n\n")
            quickstart_file.write("### Método 2: Usando run.bat\n\n")
            quickstart_file.write("Ejecute `run.bat` con los argumentos deseados. Por ejemplo:\n\n")
            quickstart_file.write("```\n")
            quickstart_file.write("run.bat skip                    # Para saltar banners iniciales\n")
            quickstart_file.write("run.bat sign --position Delantero --club Barcelona  # Para fichar un jugador\n")
            quickstart_file.write("run.bat train \"Raquel\"          # Para entrenar un jugador\n")
            quickstart_file.write("run.bat play --event            # Para jugar partidos en modo evento\n")
            quickstart_file.write("run.bat all                     # Para ejecutar todas las funcionalidades\n")
            quickstart_file.write("```\n\n")
            quickstart_file.write("### Método 3: Usando Python directamente\n\n")
            quickstart_file.write("```\n")
            quickstart_file.write("python src/main.py --help       # Para ver todas las opciones disponibles\n")
            quickstart_file.write("python src/sequence_wizard.py   # Para iniciar el asistente de configuración\n")
            quickstart_file.write("```\n\n")
            quickstart_file.write("## Nuevas Características\n\n")
            quickstart_file.write("Esta versión mejorada incluye:\n\n")
            quickstart_file.write("1. **Interfaz de configuración de acciones**: Permite definir secuencias personalizadas para diferentes escenarios del juego.\n")
            quickstart_file.write("2. **Sistema mejorado de navegación por cursor**: Control preciso del cursor para seleccionar opciones en el juego.\n")
            quickstart_file.write("3. **Sistema de archivos de configuración**: Permite guardar y cargar diferentes configuraciones para distintos escenarios.\n")
            quickstart_file.write("4. **Asistente de configuración**: Interfaz gráfica para crear y editar secuencias de acciones fácilmente.\n\n")
            quickstart_file.write("## Documentación\n\n")
            quickstart_file.write("Para instrucciones más detalladas, consulte el archivo `README.md`.\n")
        
        zipf.write(quickstart_path, os.path.basename(quickstart_path))
        print(f"Añadido: {os.path.basename(quickstart_path)}")
        
        # Crear y añadir un archivo README actualizado
        updated_readme_path = os.path.join(base_dir, "README_UPDATED.md")
        with open(updated_readme_path, 'w') as readme_file:
            readme_file.write("# eFootball Automation - Versión Mejorada\n\n")
            readme_file.write("## Descripción\n\n")
            readme_file.write("Esta aplicación automatiza diversas acciones dentro del juego eFootball, incluyendo:\n\n")
            readme_file.write("1. Fichar jugadores específicos\n")
            readme_file.write("2. Realizar entrenamientos de habilidad a jugadores\n")
            readme_file.write("3. Jugar partidos contra la CPU para completar eventos\n")
            readme_file.write("4. Saltar banners iniciales hasta llegar al menú principal\n\n")
            readme_file.write("## Nuevas Características\n\n")
            readme_file.write("Esta versión mejorada incluye:\n\n")
            readme_file.write("### 1. Interfaz de Configuración de Acciones\n\n")
            readme_file.write("- Sistema completo para definir secuencias de acciones personalizadas\n")
            readme_file.write("- Interfaz de línea de comandos y gráfica para gestionar configuraciones\n")
            readme_file.write("- Capacidad para guardar y cargar secuencias predefinidas\n\n")
            readme_file.write("### 2. Sistema Mejorado de Navegación por Cursor\n\n")
            readme_file.write("- Control preciso del cursor con aceleración/desaceleración adaptativa\n")
            readme_file.write("- Reconocimiento avanzado de elementos en pantalla\n")
            readme_file.write("- Navegación inteligente por menús complejos\n\n")
            readme_file.write("### 3. Sistema de Archivos de Configuración\n\n")
            readme_file.write("- Perfiles de configuración personalizables\n")
            readme_file.write("- Plantillas para diferentes escenarios del juego\n")
            readme_file.write("- Copias de seguridad y restauración de configuraciones\n\n")
            readme_file.write("### 4. Asistente de Configuración\n\n")
            readme_file.write("- Interfaz gráfica intuitiva para crear secuencias\n")
            readme_file.write("- Grabación automática de acciones\n")
            readme_file.write("- Detección de elementos interactivos en pantalla\n")
            readme_file.write("- Edición visual de secuencias de acciones\n\n")
            readme_file.write("## Requisitos\n\n")
            readme_file.write("- Windows 10 o superior\n")
            readme_file.write("- Python 3.8 o superior\n")
            readme_file.write("- Gamepad compatible (Xbox o DualSense)\n")
            readme_file.write("- eFootball instalado\n\n")
            readme_file.write("## Instalación\n\n")
            readme_file.write("1. Extraiga todos los archivos del ZIP en una carpeta\n")
            readme_file.write("2. Ejecute `install.bat` para instalar las dependencias necesarias\n\n")
            readme_file.write("## Uso\n\n")
            readme_file.write("### Asistente de Configuración\n\n")
            readme_file.write("```\n")
            readme_file.write("wizard.bat\n")
            readme_file.write("```\n\n")
            readme_file.write("El asistente le guiará en la creación de secuencias personalizadas para automatizar diferentes acciones en el juego.\n\n")
            readme_file.write("### Línea de Comandos\n\n")
            readme_file.write("```\n")
            readme_file.write("run.bat [comando] [opciones]\n")
            readme_file.write("```\n\n")
            readme_file.write("Comandos disponibles:\n\n")
            readme_file.write("- `skip`: Salta los banners iniciales\n")
            readme_file.write("- `sign`: Ficha jugadores específicos\n")
            readme_file.write("- `train`: Realiza entrenamientos de habilidad\n")
            readme_file.write("- `play`: Juega partidos contra la CPU\n")
            readme_file.write("- `all`: Ejecuta todas las funcionalidades\n")
            readme_file.write("- `config`: Gestiona configuraciones\n")
            readme_file.write("- `sequence`: Ejecuta una secuencia personalizada\n\n")
            readme_file.write("Ejemplos:\n\n")
            readme_file.write("```\n")
            readme_file.write("run.bat sign --position Delantero --club Barcelona\n")
            readme_file.write("run.bat train \"Raquel\"\n")
            readme_file.write("run.bat play --event\n")
            readme_file.write("run.bat sequence \"mi_secuencia_personalizada\"\n")
            readme_file.write("```\n\n")
            readme_file.write("## Estructura de Directorios\n\n")
            readme_file.write("- `src/`: Código fuente de la aplicación\n")
            readme_file.write("  - `config_interface/`: Módulos de interfaz de configuración\n")
            readme_file.write("  - `gamepad_controller.py`: Control del gamepad\n")
            readme_file.write("  - `screen_recognizer.py`: Reconocimiento de pantalla\n")
            readme_file.write("  - `cursor_navigator.py`: Navegación por cursor\n")
            readme_file.write("  - `config_system.py`: Sistema de archivos de configuración\n")
            readme_file.write("  - `sequence_wizard.py`: Asistente de configuración\n")
            readme_file.write("  - `main.py`: Punto de entrada principal\n")
            readme_file.write("- `images/`: Imágenes de referencia para reconocimiento\n")
            readme_file.write("- `config/`: Archivos de configuración\n")
            readme_file.write("  - `profiles/`: Perfiles de usuario\n")
            readme_file.write("  - `sequences/`: Secuencias guardadas\n")
            readme_file.write("  - `templates/`: Plantillas de configuración\n\n")
            readme_file.write("## Solución de Problemas\n\n")
            readme_file.write("### El gamepad no es detectado\n\n")
            readme_file.write("- Asegúrese de que el gamepad esté conectado antes de iniciar la aplicación\n")
            readme_file.write("- Verifique que los controladores del gamepad estén instalados correctamente\n")
            readme_file.write("- Pruebe con otro puerto USB\n\n")
            readme_file.write("### La aplicación no reconoce elementos en pantalla\n\n")
            readme_file.write("- Asegúrese de que eFootball esté en modo de pantalla completa\n")
            readme_file.write("- Verifique que la resolución del juego sea compatible (1920x1080 recomendado)\n")
            readme_file.write("- Intente recalibrar el reconocimiento de pantalla usando el asistente\n\n")
            readme_file.write("### Errores en la ejecución de secuencias\n\n")
            readme_file.write("- Verifique que las secuencias estén correctamente configuradas\n")
            readme_file.write("- Asegúrese de que el juego esté en el menú correcto antes de iniciar la secuencia\n")
            readme_file.write("- Intente aumentar los tiempos de espera en las acciones\n\n")
            readme_file.write("## Contacto y Soporte\n\n")
            readme_file.write("Para reportar problemas o solicitar ayuda, por favor contacte al desarrollador.\n")
        
        zipf.write(updated_readme_path, "README.md")
        print(f"Añadido: README.md (actualizado)")
        
        # Crear directorios de configuración vacíos
        config_dirs = ["config", "config/profiles", "config/sequences", "config/templates"]
        for config_dir in config_dirs:
            dir_path = os.path.join(base_dir, config_dir)
            os.makedirs(dir_path, exist_ok=True)
            # Añadir un archivo .gitkeep para mantener la estructura de directorios
            gitkeep_path = os.path.join(dir_path, ".gitkeep")
            with open(gitkeep_path, 'w') as f:
                f.write("")
            zipf.write(gitkeep_path, os.path.join(config_dir, ".gitkeep"))
            print(f"Añadido: {os.path.join(config_dir, '.gitkeep')}")
    
    print(f"\nPaquete de distribución mejorado creado exitosamente: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    zip_path = create_distribution_package()
    print(f"La aplicación mejorada está lista para ser entregada al usuario: {zip_path}")
