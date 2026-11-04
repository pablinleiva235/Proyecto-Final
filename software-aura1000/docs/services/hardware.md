# Servicio de hardware (`services/hardware.py`)

`Hardware` ofrece la interfaz de alto nivel usada por controladores y secuencias. Traduce identificadores lógicos desde `config/digital_signals.py` y `config/analog_signals.py` hacia llamadas a `drivers/`; la GUI no direcciona puertos ni bits directamente.

## Inicialización y operación

El constructor asigna los números de placa y configura direcciones de puerto de la USBDIO96H; después escribe el estado inicial de las salidas digitales. `initialize_AD()` escribe 0 V en los cuatro canales de setpoint. Las lecturas/escrituras digitales normalizan polaridades por `active_state`; las escrituras verifican que la señal esté configurada como salida. Las escrituras analógicas limitan tensión a `min_voltage`/`max_voltage`.

```python
def digital_set(self, signal_name, active):
    signal = DIGITALSIGNALS[signal_name]
    if signal["dir"] != "OUT":
        raise ValueError(f"La señal {signal_name} no está configurada como salida.")
    value = signal["active_state"] if active else int(not signal["active_state"])
```

Extracto de `Hardware.digital_set()`: los llamadores usan estado lógico activo/inactivo, aunque la salida física sea activa en bajo.

## Apagado seguro

`shutdown_state(result_callback=None)` intenta individualmente llevar las salidas digitales a `initial_state`, verifica lectura de retorno, envía 0 V a cada salida analógica configurada y finalmente vuelve el `DRIVER_ENABLE` a su estado inicial. Antes de escribir otras salidas requiere que `DRIVER_ENABLE` se lea activo; si no, registra las escrituras omitidas. Retorna una lista de errores y puede notificar cada resultado mediante callback.

Por eso, la página anterior era incorrecta al afirmar que el cierre de GUI siempre invoca directamente el servicio y que `shutdown_state()` deja analógicas sin poner a cero. El apagado normal se coordina en `ShutdownSequence`; el hook global de excepciones también intenta la rutina. Que la escritura/lectura retorne éxito no sustituye la validación de los actuadores con el equipo.

## Mapeo de señales

El mapa físico vive en [señales digitales](../config/digital_signals.md) y [analógicas](../config/analog_signals.md). Los drivers se describen en [digital](../drivers/digital.md) y [analógico](../drivers/analogico.md).
