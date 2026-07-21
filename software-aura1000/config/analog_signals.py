from drivers import analog_driver as ad

ANALOG_INPUTS = {
    "MFC1_FLOW": {"channel": 1, "range": ad.BIP10VOLTS}, #MFC de O2 --> Rango: 0 a 10 SPLM
    "MFC2_FLOW": {"channel": 2, "range": ad.BIP1VOLTS},  #MFC de N2 --> Rango: 0 a  1 SPLM
    "MFC3_FLOW": {"channel": 3, "range": ad.BIP5VOLTS},
    "MFC4_FLOW": {"channel": 4, "range": ad.BIP5VOLTS},
    "BARATRON":  {"channel": 5, "range": ad.BIP10VOLTS},
    "EOP":       {"channel": 6, "range": ad.BIP10VOLTS}
}

ANALOG_OUTPUTS = {
    # El rango se cambia a BIP10VOLTS porque el DAC de la USB-2527 es fijo.
    # El escalado de 0-5V se garantiza con min_voltage y max_voltage.
    "MFC1_SETPOINT": {"channel": 0, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
    "MFC2_SETPOINT": {"channel": 2, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
    "MFC3_SETPOINT": {"channel": 1, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
    "MFC4_SETPOINT": {"channel": 3, "range": ad.BIP10VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
}

THERMOCOUPLE = {
    "CHAMBER_TEMP": {"channel": 0}
}