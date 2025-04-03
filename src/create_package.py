"""
Script para crear un paquete de distribución de la aplicación de automatización de eFootball

Este script crea un archivo ZIP con todos los componentes necesarios para
que el usuario pueda instalar y utilizar la aplicación.
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
    print("Creando paquete de distribución...")
    
    # Directorios
    base_dir = "/home/ubuntu/efootball_automation"
    src_dir = os.path.join(base_dir, "src")
    dist_dir = os.path.join(base_dir, "dist")
    
    # Asegurar que el directorio de distribución existe
    os.makedirs(dist_dir, exist_ok=True)
    
    # Nombre del archivo ZIP
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = os.path.join(dist_dir, f"efootball_automation_{timestamp}.zip")
    
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
                    arcname = os.path.join("src", file)
                    zipf.write(file_path, arcname)
                    print(f"Añadido: {arcname}")
        
        # Crear y añadir un archivo requirements.txt
        requirements_path = os.path.join(base_dir, "requirements.txt")
        with open(requirements_path, 'w') as req_file:
            req_file.write("opencv-python>=4.5.0\n")
            req_file.write("numpy>=1.19.0\n")
            req_file.write("pyautogui>=0.9.52\n")
            req_file.write("vgamepad>=0.0.8\n")
            req_file.write("inputs>=0.5\n")
            req_file.write("pygame>=2.0.0\n")
        
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
        
        # Crear y añadir un archivo de instrucciones rápidas
        quickstart_path = os.path.join(base_dir, "QUICKSTART.md")
        with open(quickstart_path, 'w') as quickstart_file:
            quickstart_file.write("# Inicio Rápido - Automatización de eFootball\n\n")
            quickstart_file.write("## Instalación\n\n")
            quickstart_file.write("1. Extraiga todos los archivos de este ZIP en una carpeta.\n")
            quickstart_file.write("2. Ejecute `install.bat` para instalar las dependencias necesarias.\n\n")
            quickstart_file.write("## Uso\n\n")
            quickstart_file.write("### Método 1: Usando run.bat\n\n")
            quickstart_file.write("Ejecute `run.bat` con los argumentos deseados. Por ejemplo:\n\n")
            quickstart_file.write("```\n")
            quickstart_file.write("run.bat skip                    # Para saltar banners iniciales\n")
            quickstart_file.write("run.bat sign --position Delantero --club Barcelona  # Para fichar un jugador\n")
            quickstart_file.write("run.bat train \"Raquel\"          # Para entrenar un jugador\n")
            quickstart_file.write("run.bat play --event            # Para jugar partidos en modo evento\n")
            quickstart_file.write("run.bat all                     # Para ejecutar todas las funcionalidades\n")
            quickstart_file.write("```\n\n")
            quickstart_file.write("### Método 2: Usando Python directamente\n\n")
            quickstart_file.write("```\n")
            quickstart_file.write("python src/main.py --help       # Para ver todas las opciones disponibles\n")
            quickstart_file.write("```\n\n")
            quickstart_file.write("## Documentación\n\n")
            quickstart_file.write("Para instrucciones más detalladas, consulte el archivo `README.md`.\n")
        
        zipf.write(quickstart_path, os.path.basename(quickstart_path))
        print(f"Añadido: {os.path.basename(quickstart_path)}")
    
    print(f"\nPaquete de distribución creado exitosamente: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    zip_path = create_distribution_package()
    print(f"La aplicación está lista para ser entregada al usuario: {zip_path}")
