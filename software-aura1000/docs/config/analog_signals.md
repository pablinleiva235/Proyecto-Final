# Mapa de Señales Analógicas (`analog_signals.py`)

Este módulo centraliza la asignación física de los canales analógicos de la placa de adquisición **USB-2527**. Define los canales de lectura de sensores (Baratron, EOP y Readout de MFCs), las señales de control de flujo de los MFCs (*Setpoints*) y el canal dedicado al monitoreo térmico de la cámara.

---

## <span style="color: #2196F3;">Estructura de Diccionarios Analógicos</span>

Se mapean en 3 grupos de diccionarios, entradas analogicas, salidas analogicas y entrada de termocupla:

??? note "1. Entradas Analógicas - `ANALOG_INPUTS`"
    Registra los canales para los caudales de gas leídos de los controladores de flujo (MFC), la presión absoluta de la cámara mediante el sensor capacitivo Baratron y la señal del End-Of-Process (EOP).
    ```python
    from drivers import analog_driver as ad

    ANALOG_INPUTS = {
        "MFC1_FLOW": {"channel": 1, "range": ad.BIP5VOLTS},
        "MFC2_FLOW": {"channel": 2, "range": ad.BIP5VOLTS},
        "MFC3_FLOW": {"channel": 3, "range": ad.BIP5VOLTS},
        "MFC4_FLOW": {"channel": 4, "range": ad.BIP5VOLTS},
        "BARATRON":  {"channel": 5, "range": ad.BIP10VOLTS},
        "EOP":       {"channel": 6, "range": ad.BIP10VOLTS}
    }
    ```

??? note "2. Salidas Analógicas - `ANALOG_OUTPUTS`"
    Define los canales de control analógico para enviar los (*Setpoints*) de los cuatro MFC.

    !!! info "Aclaración sobre el DAC de la Placa USB-2527"
        El convertidor digital-analógico (DAC) de la placa opera con un rango de hardware fijo de `BIP10VOLTS`. Dado que los MFC del equipo reciben un rango de control de 0 a 5V, el software limita y garantiza el escalado correcto mediante las claves `min_voltage` y `max_voltage`.

    ```python
    ANALOG_OUTPUTS = {
        "MFC1_SETPOINT": {"channel": 0, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0},
        "MFC2_SETPOINT": {"channel": 2, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0},
        "MFC3_SETPOINT": {"channel": 1, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0},
        "MFC4_SETPOINT": {"channel": 3, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0},
    }
    ```

??? note "3. Termocupla - `THERMOCOUPLE`"
    Canal dedicado a la lectura directa de temperatura del proceso dentro del reactor mediante el bloque de compensación nativo del hardware.
    ```python
    THERMOCOUPLE = {
        "CHAMBER_TEMP": {"channel": 0}
    }
    ```