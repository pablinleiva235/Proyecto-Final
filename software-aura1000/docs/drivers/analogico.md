# `analog_driver.py`

Este módulo implementa la abstracción de bajo nivel para la placa de adquisición analógica **USB-2527**, utilizando `ctypes` para mapear las funciones nativas de la biblioteca `cbw32.dll`.

!!! info "Carga de librería cbw32.dll"
    ```python
    cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw32.dll")
    ```

---

## <span style="color: #2196F3;">Constantes de la API</span>

Se mapean las constantes nativas de la *Universal Library* para asegurar la compatibilidad de rangos y escalas:

* **Rangos de Voltaje:** `BIP5VOLTS` (-5V a +5V), `BIP10VOLTS` (-10V a +10V).
* **Escalas de Temperatura:** `CELSIUS` (0), `FAHRENHEIT` (1), `KELVIN` (2).
* **Filtros de Hardware:** `FILTER` (0), `NOFILTER` (1024).

---

## <span style="color: #2196F3;">Funciones de Control API (Python)</span>

Estas son las funciones de alto nivel que el software del Asher utiliza para interactuar con los canales analógicos.

??? note "Lectura de Voltaje: `read_voltage(board, channel, voltage_range)`"
    Realiza una conversión analógica-digital (ADC). Lee las cuentas binarias crudas mediante `cbAIn` y las convierte de forma transparente a magnitudes de ingeniería (Voltios) usando `cbToEngUnits`.

    ```python
    def read_voltage(board, channel, voltage_range):
        raw_value = ctypes.c_ushort()
        err = cbw.cbAIn(board, channel, voltage_range, ctypes.byref(raw_value))
        if err != 0: raise Exception(f"cbAIn error {err}")
        
        voltage_volts = ctypes.c_float()
        err = cbw.cbToEngUnits(board, voltage_range, raw_value.value, ctypes.byref(voltage_volts))
        if err != 0: raise Exception(f"cbToEngUnits error {err}")
        return voltage_volts.value
    ```

??? note "Escritura de Voltaje: `write_voltage(board, channel, voltage, voltage_range)`"
    Realiza la operación inversa (DAC). Traduce un valor analógico en voltios a cuentas binarias mediante `cbFromEngUnits` y escribe el registro físico de la placa con `cbAOut`.

??? note "Lectura de Temperatura: `read_temperature(board, channel, scale, options)`"
    Interfaz directa para la lectura de termocuplas utilizando el comando `cbTIn`. Maneja la compensación de junta fría y el filtrado por hardware de manera nativa.