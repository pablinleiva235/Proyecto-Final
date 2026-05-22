import ctypes

cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw32.dll")

cbw.cbDConfigPort.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
cbw.cbDBitOut.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

FIRSTPORTA = 10
DIGITALOUT = 1


def config_port(board, port):
    return cbw.cbDConfigPort(board, port, DIGITALOUT)


def write_bit(board, port, bit, value):
    cbw.cbDBitOut(board, port, bit, value)