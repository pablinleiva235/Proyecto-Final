import ctypes

daq = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\DaqX\Drivers\USB\DaqX.dll")

daq.daqOpen.restype = ctypes.c_int
daq.daqOpen.argtypes = [ctypes.c_char_p]

daq.daqDacSetOutputMode.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_int]
daq.daqDacWt.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_ushort]
daq.daqClose.argtypes = [ctypes.c_int]

DddtLocal = 0
DdomVoltage = 0


def open_device(name=b"DaqBoard3001USB"):
    return daq.daqOpen(name)


def set_output_mode(handle):
    daq.daqDacSetOutputMode(handle, DddtLocal, 0, DdomVoltage)


def write_dac(handle, value):
    daq.daqDacWt(handle, DddtLocal, 0, value)


def close_device(handle):
    daq.daqClose(handle)