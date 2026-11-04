# Sondeo de entradas y lecturas (`controllers/`)

No existe `logic/timers_io.py` en el código actual. Los sondeos se reparten entre controladores Qt, que emiten eventos para `MainWindow`, las secuencias y la GUI.

| Controlador | Frecuencia/configuración | Lecturas y finalidad |
|---|---:|---|
| `PowerController` | 100 ms | `POWER_ON_SWITCH` en espera y `SYS_POWER` durante operación; emite solicitudes de arranque/apagado. |
| `SignalController` | 100 ms | Señales digitales seleccionadas, estado confirmado, muestras, errores y gestión de toggles. |
| `AnalogSignalController` | 100 ms | `BARATRON`, `CHAMBER_TEMP`, `MFC1_FLOW`, `MFC2_FLOW`, `EOP`. |
| `MainWindow.module_monitor_timer` | 100 ms | Supervisión de módulos migrados y sincronización de permisos/estados. |
| Temporizadores especializados | según módulo | Startup, venteo, throttle, presión, temperatura, receta y muestras de registro. |

El resultado de `ATM_SWITCH` se entrega a `VentSequence`; sus cinco muestras consecutivas y los cuatro segundos de estabilización se describen en [secuencia de venteo](vent_sequence.md). Las fallas de proceso y su propagación se explican en [monitoreo de fallas](fallas_proceso.md).

Un intervalo de QTimer es una configuración de sondeo, no una garantía de tiempo real ni de latencia física.
