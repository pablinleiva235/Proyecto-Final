import ctypes

# =========================================================
# Carga DLL MCC Universal Library
# =========================================================

cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw64.dll") # Cambiar a cbw.32.dll en la notebook de Sala!!

# =========================================================
# RANGOS ANALOGICOS
# (Universal Library constants)
# =========================================================
UNI10VOLTS = 100    # 0-10V
UNI5VOLTS  = 101    # 0-5V

# =========================================================
# ESCALAS DE TEMPERATURA
# =========================================================
CELSIUS    = 0
FAHRENHEIT = 1
KELVIN     = 2

# =========================================================
# OPCIONES
# =========================================================
NOFILTER = 0
FILTER   = 1

# =========================================================
# APIs USB-2527: C -> Python
# =========================================================

# ------------------ Lectura Analogica --------------------
cbw.cbVIn.argtypes = [
    ctypes.c_int,                     # BoardNum
    ctypes.c_int,                     # Channel
    ctypes.c_int,                     # Range
    ctypes.POINTER(ctypes.c_float),   # DataValue
    ctypes.c_int                      # Options
]
cbw.cbVIn.restype = ctypes.c_int

# ------------------ Escritura Analogica ------------------
cbw.cbVOut.argtypes = [
    ctypes.c_int,     # BoardNum
    ctypes.c_int,     # Channel
    ctypes.c_int,     # Range
    ctypes.c_float,   # DataValue
    ctypes.c_int      # Options
]
cbw.cbVOut.restype = ctypes.c_int

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
# Lectura analogica en VOLTS
# 0-5VDC para MFCS / 0-10VDC para EOP y Baratron
# ---------------------------------------------------------
def read_voltage(board, channel, voltage_range):
    value = ctypes.c_float()
    err = cbw.cbVIn(board, channel, voltage_range, ctypes.byref(value), 0)
    if err != 0:
        raise Exception(f"cbVIn error {err}")
    return value.value

# ---------------------------------------------------------
# Escritura analogica en VOLTS
# ---------------------------------------------------------
def write_voltage(board, channel, voltage, voltage_range=UNI5VOLTS):
    err = cbw.cbVOut(board, channel, voltage_range, ctypes.c_float(voltage), 0)
    if err != 0:
        raise Exception(f"cbVOut error {err}")

# ---------------------------------------------------------
# Lectura de termocupla
# ---------------------------------------------------------
def read_temperature(board, channel, scale=CELSIUS, options=FILTER):
    value = ctypes.c_float()
    err = cbw.cbTIn(board, channel, scale, ctypes.byref(value), options)
    if err != 0:
        raise Exception(f"cbTIn error {err}")
    return value.value