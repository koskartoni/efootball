# eFootball Automation - Versión Mejorada

## Descripción

Esta aplicación automatiza diversas acciones dentro del juego eFootball. La solución ha evolucionado para incorporar nuevas técnicas de reconocimiento de pantalla, incluyendo:
- Detección visual basada en plantillas cargadas dinámicamente desde un archivo JSON.
- Fallback mediante OCR en zonas definidas, para mejorar la detección en pantallas dinámicas o con animaciones.
- Gestión avanzada de plantillas y zonas OCR mediante una interfaz gráfica (GUI) en Tkinter.

La aplicación está diseñada para facilitar la automatización de acciones como fichar jugadores, entrenar, jugar partidos y navegar en menús complejos, aprovechando además la filosofía visual del juego para resaltar la opción seleccionada.

## Nuevas Características

### 1. Reconocimiento de Pantalla con OCR Fallback
- **Matching de Plantillas:**  
  Se utiliza mss y OpenCV para capturar la pantalla y comparar con plantillas almacenadas en `templates_mapping.json`.
- **OCR Dinámico:**  
  Cuando el matching visual falla, se aplica OCR en regiones específicas definidas en `ocr_regions.json` para extraer texto y detectar el estado de la pantalla.

### 2. Gestión y Actualización de Plantillas y Zonas OCR
- **Estrategia de Nombramiento:**  
  Se recomienda un esquema de nombres que incluya:
  - Nombre base del estado (ej.: `menu_home_contrato`)
  - Sufijo que indique la condición (por ejemplo, `_normal` para la versión sin resaltar y `_sel` para la versión resaltada)
  - Marca de tiempo (formato `YYYYMMDD_HHMMSS`)
  - Opcional: índice o versión si se generan varias capturas para el mismo estado.

  **Ejemplo:**  
  `menu_home_contrato_sel_20250403_181042.png`

- **Template Manager GUI:**  
  El módulo `template_manager_gui.py` permite:
  - Capturar plantillas desde pantalla o seleccionar imágenes existentes.
  - Marcar y confirmar interactivamente una o varias zonas OCR sobre una imagen.
  - Guardar la información en archivos JSON (`templates_mapping.json` y `ocr_regions.json`), facilitando la reutilización y actualización de las capturas sin renombrarlas manualmente.

### 3. Interfaz Gráfica y Configuración
- Se ofrece una GUI intuitiva para gestionar plantillas y zonas OCR, permitiendo:
  - Seleccionar el origen de la imagen (captura en vivo o archivo).
  - Previsualizar la imagen cargada.
  - Marcar y confirmar una o varias regiones OCR mediante una interfaz basada en Tkinter.
  - Asignar nombres a las plantillas y zonas OCR siguiendo la estrategia de nombramiento definida.

## Requisitos

- Windows 10 o superior
- Python 3.8 o superior
- Gamepad compatible (Xbox o DualSense)
- eFootball instalado
- Dependencias de Python:
  - `mss`
  - `opencv-python`
  - `pytesseract`
  - `Pillow`

## Instalación

1. Extraiga todos los archivos del ZIP en una carpeta.
2. Ejecute `install.bat` para instalar las dependencias necesarias (o use `pip install -r requirements.txt`).

## Estructura de Directorios

- `src/`: Código fuente de la aplicación
  - `config_interface/`: Módulos de interfaz de configuración
  - `gamepad_controller.py`: Control del gamepad
  - **`screen_recognizer.py`**: Módulo de reconocimiento de pantalla con OCR fallback
  - **`template_manager_gui.py`**: Interfaz gráfica para gestionar plantillas y zonas OCR
  - `cursor_navigator.py`: Navegación por cursor
  - `config_system.py`: Sistema de archivos de configuración
  - `sequence_wizard.py`: Asistente de configuración
  - `main.py`: Punto de entrada principal
- `images/`: Imágenes de referencia para reconocimiento
- `config/`: Archivos de configuración
  - `profiles/`: Perfiles de usuario
  - `sequences/`: Secuencias guardadas
  - `templates/`: Plantillas de configuración

## Uso

### Asistente de Configuración

Ejecute:
`wizard.bat`


El asistente lo guiará en la creación de secuencias personalizadas para automatizar acciones en el juego.

### Línea de Comandos

Utilice:
`run.bat [comando] [opciones]`


Comandos disponibles:
- `skip`: Salta los banners iniciales
- `sign`: Ficha jugadores específicos
- `train`: Realiza entrenamientos de habilidad
- `play`: Juega partidos contra la CPU
- `all`: Ejecuta todas las funcionalidades
- `config`: Gestiona configuraciones
- `sequence`: Ejecuta una secuencia personalizada

**Ejemplos:**
`run.bat sign --position Delantero --club Barcelona run.bat train "Raquel" run.bat play --event run.bat sequence "mi_secuencia_personalizada"`



## Pruebas y Solución de Problemas

### Reconocimiento de Pantalla y OCR
- Verifique que eFootball esté en modo pantalla completa y que la resolución sea compatible.
- En caso de variaciones o animaciones, el sistema aplicará OCR en las regiones definidas en `ocr_regions.json`.
- Use el módulo `template_manager_gui.py` para actualizar o marcar nuevas zonas OCR según sea necesario.

### Plantillas y Nombramiento
- Asegúrese de que las plantillas siguen el esquema de nombres:  
  `[estado]_[condición]_[timestamp].png`  
  Ejemplo: `menu_home_contrato_sel_20250403_181042.png`
- Actualice el JSON (`templates_mapping.json`) usando la herramienta de gestión para mantener la coherencia.

## Contacto y Soporte

Para reportar problemas o solicitar ayuda, por favor contacte al desarrollador.