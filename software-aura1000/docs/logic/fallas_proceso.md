# Monitoreo y propagación de fallas

No hay un módulo vigente llamado `process_faults.py`. Las reglas están repartidas entre `ProcessController`, los controladores de subsistema, `InterlockController`, `MainWindow` y `RecipeSequence`.

- `ProcessController` comprueba fallas de lámparas, plasma y magnetrón mientras los módulos correspondientes están activos; emite `alarm_raised`, `warning_raised`, `fault_monitoring_failed` y cambios de estado.
- `SignalController` y `AnalogSignalController` publican errores de lectura; `MainWindow` actualiza tarjetas/readouts y comunica errores críticos a recetas y controladores.
- `InterlockController` entrega permisos de puerta, vacío y venteo. Si las condiciones dejan de cumplirse, `MainWindow` informa la pérdida y la receta puede abortar.
- `RecipeSequence` registra fallas y comienza el cierre, salvo cuando un fallo crítico de hardware requiere abortar sin enviar más órdenes.

Las señales monitoreadas incluyen `LAMP1_FAIL`, `LAMP2_FAIL`, `LAMP3_FAIL`, `PLASMA_FAIL`, `MAGNETRON_WARNING` y `MAGNETRON_OVERHEAT`. La ventana de gracia de ignición está configurada en `ProcessController.IGNITION_DELAY_S`; los umbrales y tiempos son valores de software y deben contrastarse con el hardware antes de considerarlos validados.

Ver también [señales de GUI](../gui/integracion.md), [secuencia de receta](recipe_sequence.md) y [módulos de proceso](../gui/pantallas.md).
