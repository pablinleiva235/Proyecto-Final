# Secuencia de venteo (`vent_sequence.py`)

`VentSequence` abre `VENT_VALVE_CONTROL`, consume muestras digitales `ATM_SWITCH` y cierra automáticamente la válvula tras confirmar atmósfera y esperar estabilización. Expone `state_changed(object)`, `sequence_error(str)` y `vent_completed()`.

## Estados y comportamiento

Estados: `IDLE`, `STARTING`, `RUNNING`, `STOPPING`, `ERROR`. `start()` solo opera desde `IDLE`, valida `can_start`, reinicia detección ATM, activa y confirma `DRIVER_ENABLE`, abre la válvula y cambia a `RUNNING`.

`update_atmospheric_state(bool)` solo cuenta muestras durante `RUNNING`: una muestra no atmosférica reinicia la cuenta y cancela el timer; cinco muestras atmosféricas consecutivas inician un `QTimer` de una sola ejecución de 4 s. Al vencer, la secuencia cierra la válvula, vuelve a `IDLE` y emite `vent_completed`.

`stop()` cancela la detección y cierra manualmente; `shutdown()` cancela el timer y cierra durante apagado global. Se requiere `DRIVER_ENABLE` para escribir `VENT_VALVE_CONTROL`. No intervienen señales analógicas en la detección ATM.

Ante error se cancela temporización, intenta cerrar la válvula, cambia a `ERROR` y emite el error. Los valores de 5 muestras y 4 s son parámetros de software, pendientes de validación física.
