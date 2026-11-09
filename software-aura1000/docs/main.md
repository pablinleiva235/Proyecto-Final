# Punto de entrada y ciclo de vida (`main.py`)

`main.py` crea `QApplication` y `SettingsManager`, presenta `StartupModeDialog` y solo después crea el backend seleccionado y sus controladores. El modo real está seleccionado por defecto; cancelar el diálogo cierra la aplicación sin inicializar hardware.

## Ensamblaje

1. Se crea `QApplication` y `SettingsManager`; el popup modal ofrece modo real o simulado.
2. Al continuar en modo real, se crea `Hardware`; en modo simulado, `MockHardware` y `SimulationController`.
3. Se construyen `StartupScreen`, `MainWindow`, secuencias y controladores para ese backend.
4. En modo real, `ApplicationController.start()` muestra `StartupScreen` y comienza el sondeo físico. En modo simulado, ejecuta automáticamente la secuencia de arranque.
5. Si falla la inicialización del backend seleccionado, se muestra un error y la aplicación termina.

```python
application_controller = ApplicationController(
    startup_controller=startup_controller,
    power_controller=power_controller,
    shutdown_controller=shutdown_controller,
    startup_screen=startup_screen,
    main_window=main_window,
)
application_controller.start()
```

Fragmento de `main.py`: el arranque y la visibilidad de las ventanas los coordina `ApplicationController`, no una máquina de estados alojada en `MainWindow`.

## Flujo de alimentación

`PowerController` sondea `POWER_ON_SWITCH` cada 100 ms hasta detectar el pedido de encendido. El evento inicia `StartupSequence`, que activa y verifica `POWER_ON` y `FILAMENT_ENABLE`, puede inicializar la placa analógica y emite progreso. Al completar, `ApplicationController` oculta `StartupScreen`, muestra `MainWindow` y activa el monitoreo de `SYS_POWER`.

La duración predeterminada de `StartupSequence` es de 30 segundos; en modo simulado la aplicación configura 3 segundos. Estos valores describen el código y no certifican el tiempo validado para el equipo físico.

## Apagado y excepciones

La salida desde la barra superior solicita confirmación mediante `ApplicationController`; al aceptar, detiene el sondeo de alimentación e inicia `ShutdownSequence`. El botón físico (`SYS_POWER`) también inicia esa secuencia. El cierre de la ventana se produce después de la señal de apagado completado.

El hook de excepciones no manejadas intenta `hardware.shutdown_state()` y presenta un mensaje crítico. La rutina informa errores si no puede completar el estado seguro; no debe interpretarse como garantía física de que todas las salidas llegaron al estado esperado.

Para el detalle de pantallas, controladores y señales, consultar [GUI](gui/index.md), [lógica](logic/index.md) y [Hardware](services/hardware.md).
