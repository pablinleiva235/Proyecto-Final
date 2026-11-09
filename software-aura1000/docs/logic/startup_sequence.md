# Secuencia de arranque (`startup_sequence.py`)

`StartupSequence` realiza el preencendido físico y emite eventos para que los controladores actualicen `StartupScreen`. No modifica widgets ni navega.

## Flujo y señales

`ApplicationController` inicia `StartupController` después de que `PowerController` detecta `POWER_ON_SWITCH`. El controlador llama `start()` y reenvía las señales de esta secuencia:

| Señal Qt | Contenido |
|---|---|
| `startup_started` | Comenzó el arranque. |
| `progress_changed(int)` | Progreso entre 0 y 100. |
| `startup_completed` | Preencendido terminado. |
| `startup_error(str)` | Error de operación o liberación de salidas. |

El orden de `start()` es: emitir inicio/progreso cero, activar y comprobar `POWER_ON`, activar y comprobar `FILAMENT_ENABLE`, comprobar otra vez `POWER_ON`, inicializar el subsistema analógico si `initialize_analog=True` y comenzar el timer.

```python
STARTUP_DURATION_MS = 30_000
SIMULATED_STARTUP_DURATION_MS = 3_000
TIMER_INTERVAL_MS = 100
```

`duration_ms` permite configurar la duración de cada instancia y por defecto usa `STARTUP_DURATION_MS`. La aplicación pasa 3 segundos en modo simulado y conserva 30 segundos en modo real. `QTimer` incrementa el progreso según la duración elegida; al completarse, la secuencia desactiva `POWER_ON`, emite progreso 100 y `startup_completed`. El tiempo configurado no equivale a validación física del precalentamiento.

## Señales y errores

Usa las salidas digitales `POWER_ON` y `FILAMENT_ENABLE`; puede invocar `Hardware.initialize_AD()` para poner a cero consignas analógicas. Ante error detiene el timer, intenta poner ambas salidas inactivas e informa cualquier fallo de limpieza en el mensaje de error. `stop()` también informa la detención como error.
