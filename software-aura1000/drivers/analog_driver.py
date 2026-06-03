import ctypes

# =========================================================
# Carga DLL MCC Universal Library
# =========================================================

cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw32.dll") # Cambiar a cbw.32.dll en la notebook de Sala!!

# =========================================================
# RANGOS ANALOGICOS
# (Universal Library constants)
# =========================================================
BIP5VOLTS  = 0     # -5V a +5V
BIP10VOLTS = 1     # -10V a +10V

# =========================================================
# ESCALAS DE TEMPERATURA
# =========================================================
CELSIUS    = 0
FAHRENHEIT = 1
KELVIN     = 2

# =========================================================
# OPCIONES
# =========================================================
FILTER   = 0
NOFILTER = 1024

# =========================================================
# APIs USB-2527: C -> Python
# =========================================================

# ------------------ Lectura Analogica --------------------
cbw.cbAIn.argtypes = [
    ctypes.c_int,                     # BoardNum
    ctypes.c_int,                     # Channel
    ctypes.c_int,                     # Range
    ctypes.POINTER(ctypes.c_ushort)   # DataValue (WORD / unsigned short)
]
cbw.cbAIn.restype = ctypes.c_int

# ------------------ Escritura Analogica ------------------
cbw.cbAOut.argtypes = [
    ctypes.c_int,     # BoardNum
    ctypes.c_int,     # Channel
    ctypes.c_int,     # Range
    ctypes.c_ushort   # DataValue (WORD / unsigned short)
]
cbw.cbAOut.restype = ctypes.c_int

# ------------------ Conversión de Lectura (ADC -> Volts) ------------------
cbw.cbToEngUnits.argtypes = [
    ctypes.c_int,                     # BoardNum
    ctypes.c_int,                     # Range
    ctypes.c_ushort,                  # DataValue (Counts)
    ctypes.POINTER(ctypes.c_float)    # EngUnits (Volts)
]
cbw.cbToEngUnits.restype = ctypes.c_int

# ------------------ Conversión de Escritura (Volts -> DAC) ----------------
cbw.cbFromEngUnits.argtypes = [
    ctypes.c_int,                     # BoardNum
    ctypes.c_int,                     # Range
    ctypes.c_float,                   # EngUnits (Volts)
    ctypes.POINTER(ctypes.c_ushort)   # DataValue (Counts)
]
cbw.cbFromEngUnits.restype = ctypes.c_int

# ------------------ Lectura Termocupla -------------------
cbw.cbTIn.argtypes = [
    ctypes.c_int,                     # BoardNum
    ctypes.c_int,                     # Channel
    ctypes.c_int,                     # Scale
    ctypes.POINTER(ctypes.c_float),   # TempValue
    ctypes.c_int                      # Options
]
cbw.cbTIn.restype = ctypes.c_int

# =========================================================
# Funciones Analogicas Python
# =========================================================
# ---------------------------------------------------------
# Lectura analógica en VOLTS
# ---------------------------------------------------------
def read_voltage(board, channel, voltage_range):
    raw_value = ctypes.c_ushort()
    # 1. Lee las cuentas binarias del hardware
    err = cbw.cbAIn(board, channel, voltage_range, ctypes.byref(raw_value)) [cite: 7]
    if err != 0:
        raise Exception(f"cbAIn error {err}")
    # 2. Convierte las cuentas a voltios por software
    voltage_volts = ctypes.c_float()
    err = cbw.cbToEngUnits(board, voltage_range, raw_value.value, ctypes.byref(voltage_volts))
    if err != 0:
        raise Exception(f"cbToEngUnits error {err}")
        
    return voltage_volts.value

# ---------------------------------------------------------
# Escritura analógica en VOLTS
# ---------------------------------------------------------
def write_voltage(board, channel, voltage, voltage_range):
    raw_counts = ctypes.c_ushort()
    # 1. Convierte los voltios deseados a cuentas binarias por software
    err = cbw.cbFromEngUnits(board, voltage_range, ctypes.c_float(voltage), ctypes.byref(raw_counts))
    if err != 0:
        raise Exception(f"cbFromEngUnits error {err}")
    # 2. Envía las cuentas calculadas al DAC de la placa
    err = cbw.cbAOut(board, channel, voltage_range, raw_counts.value) [cite: 40]
    if err != 0:
        raise Exception(f"cbAOut error {err}")

# ---------------------------------------------------------
# Lectura de termocupla
# ---------------------------------------------------------
def read_temperature(board, channel, scale=CELSIUS, options=FILTER):
    value = ctypes.c_float()
    err = cbw.cbTIn(board, channel, scale, ctypes.byref(value), options)
    if err != 0:
        raise Exception(f"cbTIn error {err}")
    return value.value