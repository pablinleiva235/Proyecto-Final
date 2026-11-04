# Interfaz gráfica (`gui/`)

La GUI actual está construida principalmente en Python con PyQt5. `MainWindow` combina una barra superior persistente con un `QStackedWidget`; las pantallas emiten solicitudes por señales Qt y los controladores realizan las operaciones y devuelven estados para representar.

## Estructura de archivos

### Ventana y pantallas

| Archivo | Responsabilidad |
|---|---|
| `gui/main_window.py` | Construye pantallas, navegación, controladores y conexiones; enruta lecturas, permisos, resultados y errores. No es una máquina de estados `PRE_ENCENDIDO/MAIN_MENU`. |
| `gui/startup_screen.py` | Presenta espera de alimentación, progreso de encendido y errores de arranque. |
| `gui/welcome_screen.py` | Entrada a mantenimiento, estadísticas y operación normal. |
| `gui/maintainer_screen.py` | Pruebas de mantenimiento, control de módulos, estados digitales y lecturas analógicas. |
| `gui/normal_operation_screen.py` | Preparación, visualización y ejecución de recetas; estado de equipo y confirmaciones de oblea. |
| `gui/statistics_screen.py` | Selección y visualización de registros de receta y mantenimiento. |
| `gui/login_dialog.py` | Diálogo modal de acceso de mantenimiento con credenciales de `config_gui/users.py`. |
| `gui/settings_dialog.py` | Selección de idioma y tema mediante `SettingsManager`. |
| `gui/recipe_dialogs.py` | Edición/validación y consulta de recetas. |
| `gui/pyqt_gui.py`, `gui/pyqt_gui.ui` | Interfaz anterior de Qt Designer. `MainWindow` actual no instancia `Ui_MainWindow`; estos archivos no definen sus pantallas activas. |

### Widgets reutilizables (`gui/widgets/`)

| Archivo | Responsabilidad |
|---|---|
| `top_bar_widget.py` | Título, reloj, solicitud de ajustes y solicitud de salida. |
| `signal_widget.py` | Representación de señal digital, estados visuales y solicitud de toggle cuando está habilitada. |
| `status_indicator.py` | Dibujo vectorial de estados `on`, `running`, `warning`, `fault` y `off`. |
| `mfc_control_card.py` | Solicitudes de caudal, válvula y calibración; presenta caudal medido y estados. |
| `analog_readout_card.py` | Lectura analógica con estados de valor no disponible y error. |
| `localization.py` | Traducción/aplicación de textos localizados en el árbol de widgets. |
| `widgets/__init__.py`, `gui/__init__.py` | Paquetes Python; no agregan comportamiento de interfaz. |

## Capas de interacción

`main.py` crea `StartupScreen` y `MainWindow`. `ApplicationController` gestiona el cambio entre ambos al terminar el encendido. Dentro de `MainWindow`, `NavigationController` registra y muestra `WelcomeScreen`, `MaintainerScreen`, `StatisticsScreen` y `NormalOperationScreen`. El diálogo de login se presenta antes de permitir acceso a mantenimiento; ajustes y salida se solicitan desde `TopBarWidget`.

Los componentes visuales emiten señales de intención (por ejemplo, `start_recipe_requested` o `output_toggle_requested`); la GUI conecta estas señales con controladores/secuencias. Una operación confirmada vuelve a la pantalla como un estado o valor. Los detalles de sondeo, señales y enclavamientos están en [integración y señales](integracion.md).

## Documentación relacionada

- [MainWindow y navegación](main_window.md)
- [Pantallas, diálogos y widgets](pantallas.md)
- [Integración, señales físicas y analógicas](integracion.md)
- [Interfaz heredada de Qt Designer](pyqt_gui.md)
