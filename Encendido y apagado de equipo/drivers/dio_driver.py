import ctypes

# =========================================================
# Carga DLL MCC Universal Library
# =========================================================

cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw32.dll")

# =========================================================
# Puertos y direcciones (Universal Library constants)
# =========================================================

FIRSTPORTA  = 10
FIRSTPORTB  = 11
FIRSTPORTCL = 12
FIRSTPORTCH = 13

SECONDPORTA  = 14
SECONDPORTB  = 15
SECONDPORTCL = 16
SECONDPORTCH = 17

THIRDPORTA  = 18
THIRDPORTB  = 19
THIRDPORTCL = 20
THIRDPORTCH = 21

FOURTHPORTA  = 22
FOURTHPORTB  = 23
FOURTHPORTCL = 24
FOURTHPORTCH = 25

DIGITALOUT = 1
DIGITALIN  = 2

# =========================================================
# APIs USBDIO96H: C -> Python
# =========================================================

# -------------- Configuracion de puerto ------------------
cbw.cbDConfigPort.argtypes = [
    ctypes.c_int,   # BoardNum
    ctypes.c_int,   # PortType
    ctypes.c_int    # Direction
]

# ----------------- Escritura Digital ---------------------
cbw.cbDBitOut.argtypes = [
    ctypes.c_int,   # BoardNum
    ctypes.c_int,   # PortType
    ctypes.c_int,   # BitNum
    ctypes.c_int    # BitValue
]

# ------------------ Lectura Digital ----------------------
cbw.cbDBitIn.argtypes = [
    ctypes.c_int,                           # BoardNum
    ctypes.c_int,                           # PortType
    ctypes.c_int,                           # BitNum
    ctypes.POINTER(ctypes.c_ushort)         # BitValue
]

# =========================================================
# Funciones Digitales Low Level Python
# =========================================================

# ---------------------------------------------------------
# Configuracion de puerto
# ---------------------------------------------------------
def config_port(board, port, direction):  
    return cbw.cbDConfigPort(board, port, direction)

# ---------------------------------------------------------
# Escritura Digital
# ---------------------------------------------------------
def write_bit(board, port, bit, value):
    cbw.cbDBitOut(board, port, bit, value)

# ---------------------------------------------------------
# Lectura Digital
# ---------------------------------------------------------
def read_bit(board, port, bit):
    value = ctypes.c_ushort()
    cbw.cbDBitIn(board, port, bit, ctypes.byref(value))
    return value.value

