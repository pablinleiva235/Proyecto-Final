# Control de puerta (`door_sequence.py`)

`DoorSequence` ordena abrir o cerrar la puerta, mantiene un estado lógico y emite cambios/errores. La GUI la invoca desde mantenimiento o receta y recibe `state_changed(object)` y `sequence_error(str)`.

## Estados y operación

`DoorState`: `OPEN`, `CLOSED`, `OPENING`, `CLOSING`, `ERROR`. `toggle()` abre desde `CLOSED` y cierra desde `OPEN`; ignora solicitudes durante transición. Apertura consulta `can_open`, configurado por `InterlockController`; ambas direcciones consultan permiso general de operación cuando fue configurado.

- Abrir: establece `OPENING`, desactiva `DOOR_CLOSE_CMD`, activa `DOOR_OPEN_CMD`, luego informa `OPEN`.
- Cerrar: establece `CLOSING`, desactiva `DOOR_OPEN_CMD`, activa `DOOR_CLOSE_CMD`, luego informa `CLOSED`.

Cada escritura comprueba que `DRIVER_ENABLE` esté activo. Los comandos son salidas `DOOR_OPEN_CMD`/`DOOR_CLOSE_CMD`; no hay una entrada analógica involucrada. El estado OPEN/CLOSED refleja que se enviaron comandos, no que un feedback haya confirmado físicamente la posición.

Ante excepción intenta desactivar ambos comandos, pasa a `ERROR` y emite el mensaje. La lectura de sensores `DOOR_OPEN`/`DOOR_CLOSE` y los permisos para receta/interlocks se gestionan fuera de esta clase.
