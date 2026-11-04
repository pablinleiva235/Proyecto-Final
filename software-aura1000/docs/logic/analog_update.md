# Actualización analógica heredada (`analog_update.py`)

`logic/analog_update.py` todavía contiene funciones auxiliares del flujo anterior y no es el origen del sondeo analógico normal de la GUI.

En el flujo vigente, `AnalogSignalController` solicita muestras de `BARATRON`, `CHAMBER_TEMP`, `MFC1_FLOW`, `MFC2_FLOW` y `EOP` cada 100 ms y emite `signal_value_changed` o `signal_error`. `MainWindow` enruta esos eventos a `MaintainerScreen`, `NormalOperationScreen`, controladores de presión/temperatura y `RecipeSequence`. Los valores MFC también se entregan a `MFCController` para su control/realimentación.

El mapa de canales y rangos está en [config/analog_signals.py](../config/analog_signals.md); las reglas de uso desde la GUI están en [integración](../gui/integracion.md).

La página antigua describía actualización directa de `QLCDNumber` dentro de `MenuPrincipal` y conversiones locales. Esa interfaz no es la pantalla activa; verificar con hardware las escalas y unidades empleadas en cada controlador antes de documentarlas como calibradas.
