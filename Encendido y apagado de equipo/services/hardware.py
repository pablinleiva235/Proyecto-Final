from drivers import dio_driver as dio
from drivers import analog_driver as ad
from config.digital_signals import DIGITALSIGNALS
from config.analog_signals import ANALOG_INPUTS
from config.analog_signals import ANALOG_OUTPUTS
from config.analog_signals import THERMOCOUPLE

class Hardware:
    def __init__(self):
        # ---------- USBDIO96H ----------
        self.dio_board = 0

        # ---------- USB-2527 ----------
        self.ad_board = 1

    # ===========================================================================================
    #                           FUNCION DE INICIALIZACION PLACA DIGITAL
    # ===========================================================================================
    def initialize_DIO(self):

        # 1) ------------  Inicializacion de puertos como I/O----------------
        ports = [
            (dio.FIRSTPORTA, dio.DIGITALIN),
            (dio.FIRSTPORTB, dio.DIGITALIN),
            # FIRSTPORTCL solo usa P1.48 para señal Power On, el resto las pongo en 0V
            (dio.FIRSTPORTCL, dio.DIGITALOUT),
             # FIRSTPORTCH no conectado, lo dejamos como entrada
            (dio.FIRSTPORTCH, dio.DIGITALIN),

            (dio.SECONDPORTA, dio.DIGITALOUT),
            (dio.SECONDPORTB, dio.DIGITALOUT),
            # SECONDPORTC no conectado, lo dejamos como entrada
            (dio.SECONDPORTCL, dio.DIGITALIN),
            (dio.SECONDPORTCH, dio.DIGITALIN),
                
            (dio.THIRDPORTA, dio.DIGITALIN),
            (dio.THIRDPORTB, dio.DIGITALIN),
            (dio.THIRDPORTCL, dio.DIGITALOUT),
            (dio.THIRDPORTCH, dio.DIGITALIN),

            (dio.FOURTHPORTA, dio.DIGITALOUT),
            (dio.FOURTHPORTB, dio.DIGITALOUT),
            # FOURTHPORTCL no conectado, lo dejamos como entrada
            (dio.FOURTHPORTCL, dio.DIGITALIN),
            # Del FOURTHPORTCH solo usa P2.67 para señal Driver Enable, el resto las pongo en 0V
            (dio.FOURTHPORTCH, dio.DIGITALOUT)
        ]
        for port, direction in ports:
            err = dio.config_port(self.dio_board, port, direction)
            if err != 0:
                raise Exception(f"Error configurando puerto {port}")

        # 2) ------------  Inicializacion de señales ----------------
        self.digital_safe_state()

    # ===========================================================================================
    #                           FUNCION DE INICIALIZACION PLACA ANALOGICA
    # ===========================================================================================
    def initialize_AD(self):
        self.analog_safe_state()

    # ===========================================================================================
    #                    FUNCION DE ESTADO SEGURO EN EL APAGADO/EMERGENCIA
    # ===========================================================================================
    def shutdown_state(self):
        # 1) Llevar salidas a estado seguro
        self.digital_safe_state()
        #self.analog_safe_state() DESCOMENTAR EN LA PRUEBA EN LA NOTEBOOK
        # 2) Configurar todos los puertos digitales como entrada
        all_ports = [
            dio.FIRSTPORTA,
            dio.FIRSTPORTB,
            dio.FIRSTPORTCL,
            dio.FIRSTPORTCH,

            dio.SECONDPORTA,
            dio.SECONDPORTB,
            dio.SECONDPORTCL,
            dio.SECONDPORTCH,

            dio.THIRDPORTA,
            dio.THIRDPORTB,
            dio.THIRDPORTCL,
            dio.THIRDPORTCH,

            dio.FOURTHPORTA,
            dio.FOURTHPORTB,
            dio.FOURTHPORTCL,
            dio.FOURTHPORTCH,
        ]
        for port in all_ports:
            dio.config_port(self.dio_board, port, dio.DIGITALIN)
        
    # ===========================================================================================
    #                             FUNCIONES DIGITALES DE ALTO NIVEL
    # ===========================================================================================

    # -------- Estado inicial/seguro de salidas digitales --------
    def digital_safe_state(self):
        for _, signal in DIGITALSIGNALS.items():
            if signal["dir"] == "OUT":
                # 1) Traducimos el puerto y bit usando la lógica de 96 bits de la placa
                port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
                # 2) Ahora sí llamamos a bajo nivel con las coordenadas que la UL entiende
                dio.write_bit(self.dio_board, port_base, bit_offset, signal["initial_state"])

    # -------- Funcion de conversion de Puerto y Bit a formato Universal Library --------
    def map_to_ul_bit(self, port, bit):

        port_offsets = {
            dio.FIRSTPORTA: 0,
            dio.FIRSTPORTB: 8,
            dio.FIRSTPORTCL: 16,
            dio.FIRSTPORTCH: 20,

            dio.SECONDPORTA: 24,
            dio.SECONDPORTB: 32,
            dio.SECONDPORTCL: 40,
            dio.SECONDPORTCH: 44,

            dio.THIRDPORTA: 48,
            dio.THIRDPORTB: 56,
            dio.THIRDPORTCL: 64,
            dio.THIRDPORTCH: 68,

            dio.FOURTHPORTA: 72,
            dio.FOURTHPORTB: 80,
            dio.FOURTHPORTCL: 88,
            dio.FOURTHPORTCH: 92,
        }
        global_bit = port_offsets[port] + bit
        return dio.FIRSTPORTA, global_bit

    # -------- Seteo de salidas digitales --------
    def digital_set(self, signal_name, active):
        signal = DIGITALSIGNALS[signal_name]
        if active:
            value = signal["active_state"]
        else:
            value = int(not signal["active_state"])
        # Traducimos usando la lógica completa de 96 bits
        port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
        dio.write_bit(self.dio_board, port_base, bit_offset, value)

    # -------- Lectura de entradas digitales --------
    def digital_read(self, signal_name):
        signal = DIGITALSIGNALS[signal_name]
        
        # Traducimos usando la lógica completa de 96 bits
        port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
        
        raw_value = dio.read_bit(self.dio_board, port_base, bit_offset)
        return raw_value == signal["active_state"]

    # ===========================================================================================
    #                             FUNCIONES ANALOGICAS DE ALTO NIVEL
    # ===========================================================================================

    # -------- Estado inicial/seguro de salidas analogicas --------
    def analog_safe_state(self):
        self.analog_write("MFC1_SETPOINT", 0.0)
        self.analog_write("MFC2_SETPOINT", 0.0)
        self.analog_write("MFC3_SETPOINT", 0.0)
        self.analog_write("MFC4_SETPOINT", 0.0)

    # -------- Escritura de salidas analogicas --------
    def analog_write(self, signal_name, voltage):
        signal = ANALOG_OUTPUTS[signal_name]
        voltage = max(signal["min_voltage"], min(signal["max_voltage"], voltage))
        ad.write_voltage(board=self.ad_board, channel=signal["channel"], voltage=voltage, voltage_range=signal["range"])

    # -------- Lectura de entradas analogicas --------
    def analog_read(self, signal_name):
        signal = ANALOG_INPUTS[signal_name]
        return ad.read_voltage(board=self.ad_board, channel=signal["channel"], voltage_range=signal["range"])    

    # -------- Lectura de termocupla --------
    def analog_read_temperature(self, tc_name):
        tc = THERMOCOUPLE[tc_name]
        return ad.read_temperature(board=self.ad_board, channel=tc["channel"])    


    