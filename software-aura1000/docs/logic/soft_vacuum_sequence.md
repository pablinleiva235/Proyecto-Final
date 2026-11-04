# Secuencia de vacío inicial (`soft_vacuum_sequence.py`)

`SoftVacuumSequence` enciende o apaga la salida de vacío inicial. Recibe `hardware` y opcionalmente validadores `can_start` y `can_operate`; no contiene timers ni actualiza widgets.

## Estados, entradas y salidas

Estados: `IDLE`, `STARTING`, `RUNNING`, `STOPPING`, `ERROR`. `toggle()` inicia desde `IDLE` y detiene desde `RUNNING`; mientras cambia de estado ignora nuevas solicitudes.

- Inicio: verifica `can_start` si existe, emite `STARTING`, comprueba `DRIVER_ENABLE`, activa `SOFT_START_CONTROL` y emite `RUNNING`.
- Parada: verifica permiso general si existe, emite `STOPPING`, comprueba `DRIVER_ENABLE`, desactiva `SOFT_START_CONTROL` y vuelve a `IDLE`.
- Apagado global: `shutdown()` desactiva esa salida y restaura `IDLE` sin el chequeo de `can_operate`.

Emite `state_changed(object)` y `sequence_error(str)`. No lee señales analógicas ni confirma presión; interlocks y la transición al vacío principal pertenecen a `InterlockController`, `MainVacuumSequence` y `MainWindow`.

Ante excepción intenta desactivar `SOFT_START_CONTROL`, pasa a `ERROR` y notifica. El valor de estado `RUNNING` confirma la orden lógica del software, no mide el vacío físico.
