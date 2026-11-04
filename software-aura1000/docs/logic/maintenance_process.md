# Operación de mantenimiento heredada (`maintenance_process.py`)

La pantalla actual es `gui/maintainer_screen.py`. Emite solicitudes de secuencia y de control de módulos mediante señales Qt; `MainWindow` las conecta con controladores, secuencias y servicio de hardware. Esta separación permite aplicar interlocks, confirmar resultados y mostrar errores.

Los controles de puerta, vacío y venteo llaman a `DoorSequence`, `SoftVacuumSequence`, `MainVacuumSequence` y `VentSequence`. Los módulos MFC, throttle, presión, temperatura, lámparas y plasma usan controladores dedicados. Las tarjetas digitales expresan solicitudes a `SignalController`, pero las salidas clasificadas como controladas por secuencia no permiten toggle manual desde la tarjeta.

`logic/maintenance_process.py` se mantiene en el repositorio como lógica anterior basada en `MenuPrincipal` y llamadas directas al hardware. No representa el flujo conectado a la `MaintainerScreen` actual. Para permisos y señales ver [integración GUI](../gui/integracion.md); para componentes visuales, [pantallas](../gui/pantallas.md).
