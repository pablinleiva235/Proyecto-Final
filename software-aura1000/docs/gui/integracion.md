# Integración de la GUI: eventos y señales

La GUI solicita acciones mediante señales Qt. `MainWindow` las conecta con controladores o secuencias; estos realizan la validación, acceso al servicio `Hardware` y operación. Sus señales de estado/valor/error vuelven a los widgets. Las páginas visuales no conocen el número de puerto ni el nivel eléctrico de los pines.

## Señales digitales

`config_gui/maintainer_signals.py` toma todas las claves de `config.digital_signals.DIGITALSIGNALS`; por eso `MaintainerScreen` genera tarjetas para cada señal configurada y las clasifica por `dir` (`IN` o `OUT`). No constituye un segundo mapa físico.

| Grupo visible/monitoreado | Señales o fuente | Uso en GUI |
|---|---|---|
| Todas las entradas/salidas declaradas | `MAINTAINER_SIGNALS` (todas las claves del mapa) | Tarjetas de diagnóstico; estado actualizado por `SignalController` cada 100 ms. |
| Solicitudes de salida | `MAINTAINER_OUTPUT_SIGNALS` menos `SEQUENCE_CONTROLLED_OUTPUT_SIGNALS` | Toggles manuales sujetos a permisos del controlador y del `MainWindow`. |
| Alimentación | `POWER_ON_SWITCH`, `SYS_POWER` | `PowerController` detecta encendido/apagado, cada 100 ms, antes o después del arranque respectivamente. |
| Atmósfera y venteo | `ATM_SWITCH` y salidas/señales de secuencia | `SignalController` alimenta la actualización de estado y `VentSequence`/`RecipeSequence`. |
| Throttle | `THROTTLE_OPEN`, `THROTTLE_CLOSED`, `STEPPER_STEP`, `STEPPER_DIR`, `STEPPER_HALF_STEP`, `STEPPER_OUTPUT_ENABLE` | `ThrottleController` mueve y supervisa límites; sus salidas no se operan como toggles arbitrarios. |
| Procesos y seguridad | `DRIVER_ENABLE`, `LAMP1/2/3_ON_CMD`, `LAMP1/2/3_FAIL`, `RF_ON_CMD`, `PLASMA_FAIL`, `MAGNETRON_WARNING`, `MAGNETRON_OVERHEAT` y señales de válvulas | Controladores de proceso/interlocks gestionan habilitación, fallas y estados visuales. |
| Secuencias de cámara | `DOOR_OPEN_CMD`, `DOOR_CLOSE_CMD`, `DOOR_OPEN`, `DOOR_CLOSE`, `SOFT_START_CONTROL`, `MAIN_VACUUM_CONTROL`, `VENT_VALVE_CONTROL`, `ATM_SWITCH` | Secuencias dedicadas con permisos de interlock y feedback observado. |
| MFC | `MFC1_OPEN`, `MFC2_OPEN` | Válvulas manejadas por `MFCController`; otras salidas del mapa pueden aparecer como solo lectura si están clasificadas como controladas por secuencia. |

La lista completa, junto con puerto, bit, dirección, polaridad activa y estado inicial, está en [Señales digitales](../config/digital_signals.md). La pantalla muestra también señales no utilizadas directamente por procesos actuales porque el selector incluye el mapa completo.

## Señales analógicas

`AnalogSignalController` sondea cada 100 ms el conjunto `BARATRON`, `CHAMBER_TEMP`, `MFC1_FLOW`, `MFC2_FLOW` y `EOP`. La temperatura usa `Hardware.analog_read_temperature`; las demás pasan por `analog_read`. Los valores se enrutan a pantallas, MFC, controladores de presión/temperatura y secuencia de receta. `MFCController` convierte setpoints de MFC 1 y 2 a `MFC1_SETPOINT`/`MFC2_SETPOINT`; el mapa también define los canales MFC3/4, pero eso no significa que la GUI actual los muestre o controle en ese flujo.

| Señal | Función visible/operativa |
|---|---|
| `BARATRON` | Presión de cámara, control de presión y condiciones de secuencia/receta. |
| `CHAMBER_TEMP` | Lectura de temperatura y control de temperatura de proceso. |
| `MFC1_FLOW`, `MFC2_FLOW` | Caudal medido y realimentación de control de MFC. |
| `EOP` | Lectura de proceso disponible para visualización/registro según la pantalla. |
| `MFC1_SETPOINT`, `MFC2_SETPOINT` | Salidas analógicas para consignas de caudal. |

Canales, rangos y límites están en [Señales analógicas](../config/analog_signals.md). Las escalas a unidades de ingeniería se aplican en controladores, servicios o presentación y deben verificarse contra calibración física.

## Permisos, errores y cuidado al interpretar estados

`InterlockController` determina los permisos de secuencias; `MainWindow` comprueba habilitación del driver, errores de lectura y procesos activos antes de algunas operaciones. Los errores de digital/analógico se muestran como estados de error y pueden detener o abortar recetas/procesos.

Una tarjeta que muestra una salida refleja la lectura/estado confirmado que entrega el controlador; el mapa por sí solo no permite asegurar que exista realimentación eléctrica independiente. `Hardware.shutdown_state()` intenta escribir el estado inicial y verificar lecturas digitales, reporta fallas y envía setpoints analógicos a 0 V; los resultados y la respuesta física se deben validar con el equipo.
