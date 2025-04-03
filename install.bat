@echo off
echo Instalando dependencias para la automatización de eFootball...
pip install -r requirements.txt
echo Instalación completada.
echo Para ejecutar la aplicación, use: python src/main.py --help
echo Para usar el asistente de configuración, use: python src/sequence_wizard.py
pause
