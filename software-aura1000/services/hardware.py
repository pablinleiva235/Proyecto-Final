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

        self.initialize_DIO()

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

        # 2) ------------  Inicializacion de salidas ----------------
        self.digital_safe_state()

    # ===========================================================================================
    #                           FUNCION DE INICIALIZACION PLACA ANALOGICA
    # ===========================================================================================
    def initialize_AD(self):
        self.analog_safe_state()

    # ===========================================================================================
    #                    FUNCION DE ESTADO SEGURO EN EL APAGADO/EMERGENCIA
    # ===========================================================================================
    def shutdown_state(self, result_callback=None):
        """Intenta cada salida de estado seguro por separado y devuelve fallas."""
        errors = []
        driver_config = DIGITALSIGNALS.get("DRIVER_ENABLE")
        for signal_name, signal in DIGITALSIGNALS.items():
            if signal["dir"] != "OUT":
                continue
            if signal_name == "DRIVER_ENABLE":
                continue
            if driver_config is not None:
                try:
                    if self.digital_read("DRIVER_ENABLE") is not True:
                        raise RuntimeError("DRIVER_ENABLE no está confirmado activo")
                except Exception as error:
                    message = f"{signal_name}: escritura omitida: {error}"
                    errors.append(message)
                    self._report_shutdown_result(result_callback, signal_name, False, message)
                    continue
            requested_value = int(signal["initial_state"])
            logical_initial = requested_value == signal["active_state"]
            try:
                port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
                dio.write_bit(self.dio_board, port_base, bit_offset, requested_value)
            except Exception as error:
                message = f"{signal_name}: escritura fallida: {error}"
                errors.append(message)
                self._report_shutdown_result(
                    result_callback,
                    signal_name,
                    False,
                    f"nivel enviado={requested_value}; escritura ERROR: {error}",
                )
                continue

            try:
                readback_value = int(
                    dio.read_bit(self.dio_board, port_base, bit_offset)
                )
            except Exception as error:
                message = f"{signal_name}: lectura de verificación fallida: {error}"
                errors.append(message)
                self._report_shutdown_result(
                    result_callback,
                    signal_name,
                    False,
                    f"escritura OK; nivel enviado={requested_value}; "
                    f"lectura de pin=ERROR: {error}; "
                    "estado lógico solicitado="
                    f"{'activo' if logical_initial else 'inactivo'}",
                )
                continue

            verified = readback_value == requested_value
            logical_readback = readback_value == signal["active_state"]
            detail = (
                f"escritura OK; nivel enviado={requested_value}; "
                f"lectura de pin={readback_value}; "
                f"estado lógico solicitado={'activo' if logical_initial else 'inactivo'}; "
                f"estado lógico leído={'activo' if logical_readback else 'inactivo'}"
            )
            if not verified:
                message = (
                    f"{signal_name}: discrepancia entre nivel enviado "
                    f"({requested_value}) y lectura ({readback_value})"
                )
                errors.append(message)
                detail += "; verificación ERROR"
            else:
                detail += "; verificación OK"
            self._report_shutdown_result(
                result_callback, signal_name, verified, detail
            )

        for signal_name in ANALOG_OUTPUTS:
            try:
                if driver_config is not None and self.digital_read("DRIVER_ENABLE") is not True:
                    raise RuntimeError("DRIVER_ENABLE no está confirmado activo")
                self.analog_write(signal_name, 0.0)
                self._report_shutdown_result(
                    result_callback,
                    signal_name,
                    True,
                    "setpoint enviado: 0.0 V; lectura física=no disponible "
                    "(sin realimentación configurada)",
                )
            except Exception as error:
                errors.append(f"{signal_name}: {error}")
                self._report_shutdown_result(
                    result_callback,
                    signal_name,
                    False,
                    f"setpoint solicitado: 0.0 V; escritura ERROR: {error}",
                )

        if driver_config is None:
            return errors
        driver_initial_active = (
            int(driver_config["initial_state"]) == int(driver_config["active_state"])
        )
        try:
            self.digital_set("DRIVER_ENABLE", driver_initial_active)
            driver_verified = self.digital_read("DRIVER_ENABLE") is driver_initial_active
            if not driver_verified:
                raise RuntimeError("la lectura física no coincide con initial_state")
            self._report_shutdown_result(
                result_callback,
                "DRIVER_ENABLE",
                True,
                f"estado inicial confirmado={driver_initial_active}",
            )
        except Exception as error:
            message = f"DRIVER_ENABLE: no se pudo aplicar initial_state: {error}"
            errors.append(message)
            self._report_shutdown_result(result_callback, "DRIVER_ENABLE", False, str(error))
        return errors

    @staticmethod
    def _report_shutdown_result(callback, name, success, detail):
        if callback is not None:
            callback(name, success, detail)

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
        if signal["dir"] != "OUT":
            raise ValueError(f"La señal {signal_name} no está configurada como salida.")
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



