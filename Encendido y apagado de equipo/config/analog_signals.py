from drivers import analog_driver as ad

ANALOG_INPUTS = {
    "MFC1_FLOW": {"channel": 1, "range": ad.UNI5VOLTS},
    "MFC2_FLOW": {"channel": 2, "range": ad.UNI5VOLTS},
    "MFC3_FLOW": {"channel": 3, "range": ad.UNI5VOLTS},
    "MFC4_FLOW": {"channel": 4, "range": ad.UNI5VOLTS},
    "BARATRON":  {"channel": 5, "range": ad.UNI10VOLTS},
    "EOP":       {"channel": 6, "range": ad.UNI10VOLTS}
}

ANALOG_OUTPUTS = {
    "MFC1_SETPOINT": {"channel": 0, "range": ad.UNI5VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
    "MFC2_SETPOINT": {"channel": 2, "range": ad.UNI5VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
    "MFC3_SETPOINT": {"channel": 1, "range": ad.UNI5VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
    "MFC4_SETPOINT": {"channel": 3, "range": ad.UNI5VOLTS, "min_voltage": 0.0, "max_voltage": 5.0,},
}

THERMOCOUPLE = {
    "CHAMBER_TEMP": {"channel": 0}
}