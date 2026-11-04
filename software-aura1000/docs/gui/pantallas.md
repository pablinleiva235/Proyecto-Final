# Pantallas, diálogos y widgets

Esta página resume el comportamiento visible de los componentes implementados bajo `gui/`. Los textos y temas se obtienen principalmente de `config_gui/strings.py`, `settings_manager.py` y `theme.py`.

## Pantallas

- **`StartupScreen` (`startup_screen.py`):** muestra espera del pulsador, arranque, progreso y error. Recibe el progreso/error desde `ApplicationController`; no opera el hardware directamente.
- **`WelcomeScreen` (`welcome_screen.py`):** emite solicitudes para acceder al modo mantenimiento, estadísticas u operación normal.
- **`MaintainerScreen` (`maintainer_screen.py`):** contiene pestañas de secuencias/módulos y de señales digitales. También ofrece controles MFC, throttle, presión, temperatura, lámparas y plasma; muestra estados de operación y errores. Sus señales expresan solicitudes, no ejecutan por sí mismas las secuencias.
- **`NormalOperationScreen` (`normal_operation_screen.py`):** permite crear, cargar, guardar, consultar y ejecutar recetas; muestra diagrama, valores de proceso, estados y confirmaciones de carga/remoción de oblea. La receta y el hardware son coordinados por `MainWindow` y `RecipeSequence`.
- **`StatisticsScreen` (`statistics_screen.py`):** localiza registros CSV de receta/mantenimiento, permite seleccionar un archivo y grafica datos disponibles.

## Diálogos

- **`LoginDialog`:** valida usuario y contraseña frente a las constantes de `config_gui/users.py`; es una puerta visual de acceso al modo mantenedor, no un mecanismo de autenticación externa.
- **`SettingsDialog`:** ofrece idioma y tema y persiste/aplica los cambios mediante `SettingsManager`.
- **`RecipeEditorDialog` / `RecipeViewerDialog`:** edición con validaciones de receta y vista de solo consulta; son usados desde operación normal.

## Widgets comunes

- **`TopBarWidget`:** muestra título, fecha y hora (actualización cada segundo) y emite `settings_requested` y `exit_requested`.
- **`SignalWidget`:** presenta nombre, estado y categoría de una señal. Solo emite `toggle_requested` cuando es interactiva, está habilitada y no se encuentra procesando.
- **`StatusIndicatorWidget`:** representa visualmente estados semánticos sin leer hardware.
- **`MFCControlCard`:** reúne controles de caudal/válvula/calibración y la lectura medida.
- **`AnalogReadoutCard`:** muestra magnitud, ausencia de dato y error de lectura.
- **`localization.py`:** adapta textos localizados a widgets y árboles de widgets.

## Archivos UI heredados

`pyqt_gui.ui` y `pyqt_gui.py` describen una interfaz anterior con la página `MenuPrincipal` y controles de coordenadas fijas. La `MainWindow` actual crea `NormalOperationScreen` y `MaintainerScreen` directamente en Python y no importa `Ui_MainWindow`. Por eso, cambios a estas pantallas activas se realizan en las clases Python; regenerar `pyqt_gui.py` no actualiza la GUI actual.
