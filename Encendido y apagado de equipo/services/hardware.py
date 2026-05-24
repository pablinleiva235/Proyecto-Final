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
    #                    FUNCION DE ESTADO SEGURO ANTE ALGUNA FALLA/EMERGENCIA
    # ===========================================================================================
    def safe_state(self):
        self.digital_safe_state()
        self.analog_safe_state()
        
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
        # --- CONECTOR P1: Bloque 1 ---
        if 10 <= port <= 13:
            port_base = 10  # FIRSTPORTA
            bit_offset = bit if port == 10 else (8 + bit if port == 11 else (16 + bit if port == 12 else 20 + bit))
        # --- CONECTOR P1: Bloque 2 ---
        elif 14 <= port <= 17:
            port_base = 14  # SECONDPORTA
            bit_offset = bit if port == 14 else (8 + bit if port == 15 else (16 + bit if port == 16 else 20 + bit))
        # --- CONECTOR P2: Bloque 3 ---
        elif 18 <= port <= 21:
            port_base = 18  # THIRDPORTA
            bit_offset = bit if port == 18 else (8 + bit if port == 19 else (16 + bit if port == 20 else 20 + bit))
        # --- CONECTOR P2: Bloque 4 ---
        elif 22 <= port <= 25:
            port_base = 22  # FOURTHPORTA
            bit_offset = bit if port == 22 else (8 + bit if port == 23 else (16 + bit if port == 24 else 20 + bit))
        else:
            raise ValueError(f"Puerto {port} fuera de rango legal de la UL (10 a 25).")
        return port_base, bit_offset

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


    