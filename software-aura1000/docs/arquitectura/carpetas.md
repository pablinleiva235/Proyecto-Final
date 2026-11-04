# Estructura del proyecto

Árbol de los componentes principales presentes en `software-aura1000/` (se omiten recursos, registros y pruebas individuales):

```text
software-aura1000/
├── main.py                   # Composición e inicio de la aplicación
├── config/                   # Mapeos de señales físicas y límites de proceso
├── config_gui/               # Textos, usuarios, tema, ajustes y señales de mantenimiento
├── controllers/              # Navegación, adquisición y control de subsistemas
├── drivers/                  # Adaptadores de bajo nivel para las placas
├── gui/                      # Pantallas, diálogos, widgets y UI heredada de Qt Designer
├── logic/                    # Secuencias asíncronas de arranque, proceso y apagado
├── services/                 # Abstracción hardware, recetas y registros de datos
├── assets/                   # Diagramas e imágenes de la GUI
├── resources/                # Recursos de aplicación
├── logs/                     # Datos de recetas, mantenimiento y apagado
├── recipies/                 # Archivos de recetas de ejemplo (nombre legado)
├── tests/                    # Pruebas y hardware simulado
├── docs/                     # Fuente Markdown de MkDocs
└── mkdocs.yml                # Navegación y configuración del sitio
```

## Responsabilidades y flujo

- **`config/` y `config_gui/`:** separan el mapa de pines/canales físicos del texto, preferencias y selección visual de señales. `maintainer_signals.py` deriva las entradas y salidas desde `config.digital_signals`.
- **`drivers/` y `services/`:** los drivers llaman a la Universal Library; `services/hardware.py` traduce nombres lógicos, normaliza estados activos y ofrece operaciones digitales y analógicas.
- **`controllers/`:** coordinan navegación, sondeo, interlocks, MFC, throttle, presión, temperatura, procesos, arranque y apagado. Emiten señales Qt para informar cambios y errores.
- **`logic/`:** implementa secuencias (`startup_sequence.py`, `door_sequence.py`, `soft_vacuum_sequence.py`, `main_vacuum_sequence.py`, `vent_sequence.py`, `shutdown_sequence.py`, `recipe_sequence.py`). Las secuencias usan timers Qt y notifican progreso/estado por señales.
- **`gui/`:** contiene `StartupScreen`, `MainWindow`, pantallas y diálogos; widgets reutilizables están en `gui/widgets/`. `pyqt_gui.py` y `pyqt_gui.ui` son artefactos de una interfaz anterior, no la base de `MainWindow` actual.
- **`services/`:** también aloja persistencia y registros de recetas y mantenimiento.

El ensamblaje ocurre en `main.py`: primero el ciclo de arranque físico; al completarse se presenta `MainWindow`. Dentro de esa ventana, `NavigationController` cambia las páginas del `QStackedWidget`. Las solicitudes de UI viajan como señales hacia controladores y secuencias; estados, muestras y errores regresan mediante señales Qt.

## Desarrollo de la documentación

MkDocs se configura en `mkdocs.yml`. Desde `software-aura1000/` se puede construir el sitio con `mkdocs build` si MkDocs y sus plugins están instalados. No se lista `requirements.txt` porque no existe en la raíz actual del proyecto.
