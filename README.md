# eFootball Automation - Versión Mejorada

## Descripción

Esta aplicación automatiza diversas acciones dentro del juego eFootball, incluyendo:

1. Fichar jugadores específicos
2. Realizar entrenamientos de habilidad a jugadores
3. Jugar partidos contra la CPU para completar eventos
4. Saltar banners iniciales hasta llegar al menú principal

## Nuevas Características

Esta versión mejorada incluye:

### 1. Interfaz de Configuración de Acciones

- Sistema completo para definir secuencias de acciones personalizadas
- Interfaz de línea de comandos y gráfica para gestionar configuraciones
- Capacidad para guardar y cargar secuencias predefinidas

### 2. Sistema Mejorado de Navegación por Cursor

- Control preciso del cursor con aceleración/desaceleración adaptativa
- Reconocimiento avanzado de elementos en pantalla
- Navegación inteligente por menús complejos

### 3. Sistema de Archivos de Configuración

- Perfiles de configuración personalizables
- Plantillas para diferentes escenarios del juego
- Copias de seguridad y restauración de configuraciones

### 4. Asistente de Configuración

- Interfaz gráfica intuitiva para crear secuencias
- Grabación automática de acciones
- Detección de elementos interactivos en pantalla
- Edición visual de secuencias de acciones

## Requisitos

- Windows 10 o superior
- Python 3.8 o superior
- Gamepad compatible (Xbox o DualSense)
- eFootball instalado

## Instalación

1. Extraiga todos los archivos del ZIP en una carpeta
2. Ejecute `install.bat` para instalar las dependencias necesarias

## Uso

### Asistente de Configuración

```
wizard.bat
```

El asistente le guiará en la creación de secuencias personalizadas para automatizar diferentes acciones en el juego.

### Línea de Comandos

```
run.bat [comando] [opciones]
```

Comandos disponibles:

- `skip`: Salta los banners iniciales
- `sign`: Ficha jugadores específicos
- `train`: Realiza entrenamientos de habilidad
- `play`: Juega partidos contra la CPU
- `all`: Ejecuta todas las funcionalidades
- `config`: Gestiona configuraciones
- `sequence`: Ejecuta una secuencia personalizada

Ejemplos:

```
run.bat sign --position Delantero --club Barcelona
run.bat train "Raquel"
run.bat play --event
run.bat sequence "mi_secuencia_personalizada"
```

## Estructura de Directorios

- `src/`: Código fuente de la aplicación
  - `config_interface/`: Módulos de interfaz de configuración
  - `gamepad_controller.py`: Control del gamepad
  - `screen_recognizer.py`: Reconocimiento de pantalla
  - `cursor_navigator.py`: Navegación por cursor
  - `config_system.py`: Sistema de archivos de configuración
  - `sequence_wizard.py`: Asistente de configuración
  - `main.py`: Punto de entrada principal
- `images/`: Imágenes de referencia para reconocimiento
- `config/`: Archivos de configuración
  - `profiles/`: Perfiles de usuario
  - `sequences/`: Secuencias guardadas
  - `templates/`: Plantillas de configuración

## Solución de Problemas

### El gamepad no es detectado

- Asegúrese de que el gamepad esté conectado antes de iniciar la aplicación
- Verifique que los controladores del gamepad estén instalados correctamente
- Pruebe con otro puerto USB

### La aplicación no reconoce elementos en pantalla

- Asegúrese de que eFootball esté en modo de pantalla completa
- Verifique que la resolución del juego sea compatible (1920x1080 recomendado)
- Intente recalibrar el reconocimiento de pantalla usando el asistente

### Errores en la ejecución de secuencias

- Verifique que las secuencias estén correctamente configuradas
- Asegúrese de que el juego esté en el menú correcto antes de iniciar la secuencia
- Intente aumentar los tiempos de espera en las acciones

## Contacto y Soporte

Para reportar problemas o solicitar ayuda, por favor contacte al desarrollador.
