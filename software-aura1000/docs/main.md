# Punto de entrada y ciclo de vida (`main.py`)

`main.py` crea `QApplication`, configura el manejador global de excepciones, instancia el hardware real o simulado, construye controladores y secuencias, y entrega el ciclo de vida a `ApplicationController`.

## Ensamblaje

1. Se crea `QApplication` y `SettingsManager`.
2. Se instancia `Hardware` o `MockHardware`, según `config_gui/app_config.py`. En modo simulado también se instala `SimulationController` como filtro de eventos.
3. `PowerController` supervisa las entradas de alimentación; `StartupSequence` y `StartupController` ejecutan y notifican el preencendido.
4. Se crean las secuencias de puerta, vacío, venteo y apagado.
5. Se construyen `StartupScreen` y `MainWindow`; este último recibe hardware, secuencias y configuración de idioma/tema.
6. `ApplicationController.start()` presenta la pantalla inicial y comienza el sondeo de encendido. Finalmente se inicia el loop de Qt.

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

La duración configurada en `logic/startup_sequence.py` es actualmente `STARTUP_DURATION_MS = 3_000` (3 segundos). Este dato describe el valor del código, no certifica que sea el tiempo validado para el equipo físico.

## Apagado y excepciones

La salida desde la barra superior solicita confirmación mediante `ApplicationController`; al aceptar, detiene el sondeo de alimentación e inicia `ShutdownSequence`. El botón físico (`SYS_POWER`) también inicia esa secuencia. El cierre de la ventana se produce después de la señal de apagado completado.

El hook de excepciones no manejadas intenta `hardware.shutdown_state()` y presenta un mensaje crítico. La rutina informa errores si no puede completar el estado seguro; no debe interpretarse como garantía física de que todas las salidas llegaron al estado esperado.

Para el detalle de pantallas, controladores y señales, consultar [GUI](gui/index.md), [lógica](logic/index.md) y [Hardware](services/hardware.md).
