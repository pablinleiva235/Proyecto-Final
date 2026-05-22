from drivers import daq_driver as daq
from drivers import dio_driver as dio


class Hardware:
    def __init__(self):
        self.handle = None
        self.board = 0
        self.port = dio.FIRSTPORTA
        self.bit = 0

    # -------- INIT --------
    def initialize(self):
        self.handle = daq.open_device()

        if self.handle == -1:
            raise Exception("Error abriendo DAQ")

        daq.set_output_mode(self.handle)

        err = dio.config_port(self.board, self.port)
        if err != 0:
            raise Exception("Error configurando DIO")

        print("Hardware OK")

    # -------- DIGITAL --------
    def digital_on(self):
        dio.write_bit(self.board, self.port, self.bit, 1)

    def digital_off(self):
        dio.write_bit(self.board, self.port, self.bit, 0)

    # -------- ANALOG --------
    def set_voltage(self, value):
        dac_value = int(32768 + (value / 2) * (65535 / 10))
        daq.write_dac(self.handle, dac_value)

    # -------- CLOSE --------
    def close(self):
        if self.handle:
            daq.write_dac(self.handle, 32768)
            daq.close_device(self.handle)