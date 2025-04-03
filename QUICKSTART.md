# Inicio Rápido - Automatización de eFootball (Versión Mejorada)

## Instalación

1. Extraiga todos los archivos de este ZIP en una carpeta.
2. Ejecute `install.bat` para instalar las dependencias necesarias.

## Uso

### Método 1: Usando el Asistente de Configuración (Recomendado)

Ejecute `wizard.bat` para iniciar el asistente gráfico que le permitirá:

- Crear secuencias personalizadas de acciones
- Grabar acciones automáticamente
- Configurar movimientos precisos del cursor
- Guardar y cargar configuraciones

### Método 2: Usando run.bat

Ejecute `run.bat` con los argumentos deseados. Por ejemplo:

```
run.bat skip                    # Para saltar banners iniciales
run.bat sign --position Delantero --club Barcelona  # Para fichar un jugador
run.bat train "Raquel"          # Para entrenar un jugador
run.bat play --event            # Para jugar partidos en modo evento
run.bat all                     # Para ejecutar todas las funcionalidades
```

### Método 3: Usando Python directamente

```
python src/main.py --help       # Para ver todas las opciones disponibles
python src/sequence_wizard.py   # Para iniciar el asistente de configuración
```

## Nuevas Características

Esta versión mejorada incluye:

1. **Interfaz de configuración de acciones**: Permite definir secuencias personalizadas para diferentes escenarios del juego.
2. **Sistema mejorado de navegación por cursor**: Control preciso del cursor para seleccionar opciones en el juego.
3. **Sistema de archivos de configuración**: Permite guardar y cargar diferentes configuraciones para distintos escenarios.
4. **Asistente de configuración**: Interfaz gráfica para crear y editar secuencias de acciones fácilmente.

## Documentación

Para instrucciones más detalladas, consulte el archivo `README.md`.
