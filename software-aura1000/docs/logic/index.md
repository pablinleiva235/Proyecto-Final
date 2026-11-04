# Controladores y secuencias

El flujo actual separa adquisición/permisos de las secuencias temporizadas. Los controladores están en `controllers/`; las secuencias de operación y receta están en `logic/`. Las páginas heredadas que documentaban un bucle único en `timers_io.py` se conservan como referencia de transición, no como descripción de la ejecución vigente.

## Controladores (`controllers/`)

| Módulo | Responsabilidad actual |
|---|---|
| `application_controller.py` | Ciclo de vida de startup, presentación de ventanas y coordinación de apagado/salida. |
| `power_controller.py` | Sondeo de `POWER_ON_SWITCH` y `SYS_POWER`; emite solicitudes de encendido/apagado. |
| `startup_controller.py` | Adapta progreso, estado y error de `StartupSequence` al ciclo de aplicación. |
| `shutdown_controller.py` | Coordina `ShutdownSequence` y propaga resultado/error. |
| `navigation_controller.py` | Registra widgets de pantalla y selecciona página del `QStackedWidget`. |
| `signal_controller.py` | Sondeo de señales digitales, estado confirmado, solicitudes de toggle y errores. |
| `analog_signal_controller.py` | Sondeo analógico y emisión de valores/errores. |
| `interlock_controller.py` | Calcula permisos de puerta, vacío y venteo según estado de secuencias y procesos. |
| `mfc_controller.py` | Control de flujo, válvulas y calibración de MFC; convierte flujo/voltaje. |
| `throttle_controller.py` | Movimiento, límites, homing, pulsos y retornos de seguridad del actuador throttle. |
| `pressure_controller.py` | Control de presión mediante throttle, con límites y estados/error. |
| `temperature_controller.py` | Control y supervisión de temperatura con el controlador de proceso. |
| `process_controller.py` | Lámparas, plasma, monitoreo de fallas e interacciones relacionadas. |

## Secuencias (`logic/`)

| Módulo | Responsabilidad |
|---|---|
| `startup_sequence.py` | Retención de alimentación, filamento, inicialización opcional del subsistema analógico y progreso de precalentamiento. |
| `door_sequence.py` | Apertura/cierre de puerta y confirmaciones/interlocks. |
| `soft_vacuum_sequence.py` | Secuencia de vacío inicial. |
| `main_vacuum_sequence.py` | Secuencia de vacío principal y condiciones de inicio/parada. |
| `vent_sequence.py` | Venteo, observación de ATM y finalización. |
| `shutdown_sequence.py` | Apagado coordinado y captura de errores del estado seguro. |
| `recipe_sequence.py` | Orquestación del proceso automatizado, muestras, acciones y confirmaciones. |
| `maintenance_process.py` | Rutinas de mantenimiento heredadas; no es el manejador principal de controles de `MaintainerScreen` actual. |
| `analog_update.py`, `throttle_test.py` | Utilidades/pruebas heredadas; no constituyen el sondeo principal de la GUI actual. |

Las solicitudes visuales se conectan desde `MainWindow`. Los controladores y secuencias emiten señales Qt; la GUI las representa sin concentrar todo el sondeo en un timer central.

## Documentación por módulo de secuencia

- [Arranque](startup_sequence.md)
- [Puerta](door_sequence.md)
- [Soft Vacuum](soft_vacuum_sequence.md)
- [Main Vacuum](main_vacuum_sequence.md)
- [Venteo](vent_sequence.md)
- [Apagado seguro](shutdown_sequence.md)
- [Recetas](recipe_sequence.md)

## Sondeo y responsabilidades transversales

- [Sondeo de controladores](sondeo_controladores.md)
- [Monitoreo de fallas](fallas_proceso.md)

## Módulos heredados que aún existen

- [Mantenimiento anterior](maintenance_process.md)
- [Actualización analógica anterior](analog_update.md)
