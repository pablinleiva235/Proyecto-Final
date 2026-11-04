# Secuencia de vacío principal (`main_vacuum_sequence.py`)

`MainVacuumSequence` habilita/deshabilita `MAIN_VACUUM_CONTROL`. Permite inyectar validadores separados para inicio, parada y operación general. La política de seguridad concreta la provee `InterlockController`.

## Estados y flujo

Estados: `IDLE`, `STARTING`, `RUNNING`, `STOPPING`, `ERROR`; señales Qt: `state_changed(object)` y `sequence_error(str)`. `toggle()` inicia o detiene según el estado y descarta solicitudes mientras está iniciando/deteniendo.

- Inicio desde `IDLE`: valida `can_start`, emite `STARTING`, exige `DRIVER_ENABLE`, activa `MAIN_VACUUM_CONTROL` y emite `RUNNING`.
- Parada desde `RUNNING`: comprueba permiso general y `can_stop`, emite `STOPPING`, desactiva la salida y vuelve a `IDLE`.
- `shutdown()` desactiva la salida para el apagado global sin usar los validadores normales.

No lee presión ni controla directamente Soft Vacuum; las lecturas BARATRON pertenecen al controlador analógico/de presión. El estado `RUNNING` significa comando aplicado sin excepción, no una medición independiente del bombeo.

Ante error intenta desactivar `MAIN_VACUUM_CONTROL`, informa `ERROR` y emite el detalle. La operación de salida requiere `DRIVER_ENABLE` activo.
