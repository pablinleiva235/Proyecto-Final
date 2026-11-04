# `MainWindow`: coordinación de la GUI

`MainWindow` es la ventana principal de operación una vez completado el preencendido. Construye widgets y controladores, conecta señales Qt y coordina la respuesta visual a estados, errores y lecturas. La secuencia que la hace visible pertenece a `ApplicationController` (ver [punto de entrada](../main.md)).

## Composición y navegación

La ventana contiene `TopBarWidget` y un `QStackedWidget`. `NavigationController` registra cuatro páginas lógicas: `WELCOME_SCREEN`, `MAINTAINER_SCREEN`, `STATISTICS_SCREEN` y `NORMAL_OPERATION_SCREEN`. Al construirse, se presenta bienvenida.

```python
self.top_bar = TopBarWidget()
self.stack = QStackedWidget()
self.welcome_screen = WelcomeScreen()
self.maintainer_screen = MaintainerScreen()
self.statistics_screen = StatisticsScreen()
self.normal_operation_screen = NormalOperationScreen(
    use_mock_hardware=self.use_mock_hardware
)
```

Fragmento de `MainWindow.create_widgets()`: las páginas actuales son widgets Python independientes; el `Ui_MainWindow` de `pyqt_gui.py` no participa en esta construcción.

La pantalla de bienvenida navega a operación o estadísticas directamente. Para entrar a mantenimiento se solicita autenticación mediante `LoginDialog`. El botón de volver en las pantallas internas retorna a bienvenida. El botón de configuración abre `SettingsDialog`; cambios de idioma se propagan mediante `SettingsManager`, y el tema se aplica a operación normal.

## Controladores conectados

`MainWindow` instancia y coordina:

- `NavigationController` para el `QStackedWidget`.
- `SignalController` para lectura y solicitudes de salida digital.
- `AnalogSignalController` para muestras analógicas.
- `InterlockController` para permisos de secuencias de puerta, vacío y venteo.
- `MFCController`, `ThrottleController`, `PressureController`, `ProcessController` y `TemperatureController` para módulos de proceso.
- `RecipeSequence` para coordinar recetas con secuencias y módulos.

También crea temporizadores Qt para supervisión de módulos migrados y registro de mantenimiento. `closeEvent()` detiene la grabación de mantenimiento; el apagado seguro se coordina con `ApplicationController` y `ShutdownSequence`, no con los timers heredados descritos en documentación antigua.

## Flujo de señal digital

Una tarjeta de mantenimiento emite `output_toggle_requested`; `SignalController` valida permisos y escribe mediante `Hardware`. Durante la operación, la tarjeta muestra `processing`; luego presenta el estado confirmado o el error. Las muestras relevantes alimentan además interlocks y receta.

```python
self.signal_controller = SignalController(
    hardware=self.hardware,
    monitored_signals=MAINTAINER_SIGNALS,
    output_signals=MAINTAINER_OUTPUT_SIGNALS,
    poll_interval_ms=100,
    can_toggle=self._can_toggle_manual_output,
)
```

Fragmento de `MainWindow.create_widgets()`: el sondeo digital de mantenimiento se configura a 100 ms. El estado del driver y los interlocks pueden bloquear solicitudes; no todas las salidas visibles se pueden accionar manualmente.

## Comentarios/documentación reemplazados

La descripción anterior de este archivo hacía referencia a `timersIOManager`, `preEncendido`, `offClose`, `trigger_hardware_off`, `stackedWidget` generado y métodos como `MainMenu_init`. Esos elementos no describen el flujo actual de `MainWindow`; el arranque vive en `StartupScreen`/controladores/secuencia, y la interfaz se arma en Python.
