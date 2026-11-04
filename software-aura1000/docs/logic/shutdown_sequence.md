# Secuencia de apagado seguro (`shutdown_sequence.py`)

`ShutdownSequence` intenta detener módulos y aplicar estado seguro global, registra resultados en `ShutdownLog` y emite `sequence_error(str)` si hubo fallas y siempre `sequence_completed()` al terminar el procedimiento.

## Orden del proceso

1. Crear el registro e intentar habilitar y confirmar `DRIVER_ENABLE`.
2. Si se confirma, llamar a `shutdown()` en venteo, vacío principal y Soft Vacuum, en ese orden. Un error de subsistema se registra y no impide intentar los restantes.
3. Ejecutar `Hardware.shutdown_state(result_callback=...)`, que comprueba escrituras digitales y pone setpoints analógicos a cero.
4. Si no se pudo habilitar el driver al inicio, omitir la escritura de los módulos y tratar de restaurar `DRIVER_ENABLE` a su estado inicial.
5. Cerrar el log, emitir los errores agregados si existen y emitir finalización.

No hay salida de widget aquí: `ShutdownController` recibe las señales y `ApplicationController` resuelve la interfaz/cierre. Las señales físicas afectadas dependen del mapa `DIGITALSIGNALS` y `ANALOG_OUTPUTS`; el detalle y lectura de retorno están documentados en [Hardware](../services/hardware.md).

La finalización de software no garantiza por sí sola que los actuadores hayan alcanzado su posición segura. Revisar el log y validar en el equipo.
