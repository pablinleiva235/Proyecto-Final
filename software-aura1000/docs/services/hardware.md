# `hardware.py`

El módulo `hardware.py` implementa la clase `Hardware`, la cual actúa como una **API de servicios de alto nivel**. Su propósito fundamental es unificar el control de las dos placas de adquisición (**USBDIO96H** y **USB-2527**) para que puedan ser controladas por la GUI. Traduce los alias definidos en las tablas de configuración (`config/`) hacia comandos de hardware puros, encargándose de la conversión de puertos de 96 bits, enmascaramiento de estados activos/inactivos y lazos automáticos de parada de emergencia.

---

## <span style="color: #2196F3;">Inicialización y Configuración de Arranque</span>

??? note "Constructor del Sistema: `__init__(self)`"
    Define las direcciones lógicas asignadas por la *Universal Library* para cada placa (`dio_board = 0` y `ad_board = 1`). Lanza inmediatamente la inicialización física de los puertos digitales para garantizar que el hardware arranque en un estado controlado de entrada/salida.

    ```python
    def __init__(self):
        # ---------- USBDIO96H ----------
        self.dio_board = 0
        # ---------- USB-2527 ----------
        self.ad_board = 1

        self.initialize_DIO()
    ```

??? note "Configuración Física Digital: `initialize_DIO(self)`"
    Configura de manera explícita la dirección de datos (Entrada o Salida) de los 16 puertos lógicos que componen los 96 bits de la placa **USBDIO96H**. Al finalizar el mapeo direccional, invoca la rutina de estado seguro para asegurar que ningún actuador se enclave de forma imprevista durante el arranque eléctrico.

    ```python
    def initialize_DIO(self):
        # 1) ------------ Inicializacion de puertos como I/O----------------
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

        # 2) ------------ Inicializacion de salidas ----------------
        self.digital_safe_state()
    ```

??? note "Configuración Física Analógica: `initialize_AD(self)`"
    Inicializa el subsistema analógico de la placa **USB-2527**. Su función principal es asegurar que los convertidores digital-analógicos (DAC) se listen en cero voltios para apagar por completo las consignas de los controladores de flujo de gas (MFC).

    ```python
    def initialize_AD(self):
        self.analog_safe_state()
    ```

---

## <span style="color: #2196F3;">Rutinas Críticas de Interlock y Parada de Emergencia</span>

??? note "Lazo de Desconexión Segura: `shutdown_state(self)`"
    Es el método maestro de seguridad invocado por el `closeEvent` de la GUI. Lleva todas las líneas de salida físicas (digitales y analógicas) a sus valores de reposo e inhibición eléctrica, desactivando válvulas neumáticas, relés de potencia y consignas de flujo para prevenir accidentes en la cámara del reactor.

    ```python
    def shutdown_state(self):
        # 1) Llevar salidas a estado seguro
        self.digital_safe_state()
        #self.analog_safe_state() DESCOMENTAR ESTO EN NOTEBOOK DE SALA!!!!
    ```

---

## <span style="color: #2196F3;">Lógica de Conmutación de Registros (96 Bits)</span>

??? note "Lógica de Re-mapeo del Driver: `map_to_ul_bit(self, port, bit)`"
    **Algoritmo Crítico:** Resuelve una limitación de direccionamiento de la librería nativa para la placa de 96 bits. En lugar de operar puertos aislados, calcula un desplazamiento lineal de bits (`global_bit`) basándose en una matriz de offsets fijos. Retorna las coordenadas indexadas desde `FIRSTPORTA` para que la función de bajo nivel (`cbDBitOut`/`cbDBitIn`) pueda hallar el pin físico exacto.

    ```python
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
    ```

---

## <span style="color: #2196F3;">Operaciones Digitales de Alto Nivel</span>

??? note "Inhibición Digital de Reposo: `digital_safe_state(self)`"
    Recorre el diccionario completo de señales digitales (`DIGITALSIGNALS`). Identifica de forma automática cuáles están configuradas como salidas (`OUT`), traduce sus coordenadas mediante `map_to_ul_bit` y escribe en el hardware el valor binario declarado en su clave `initial_state`.

    ```python
    def digital_safe_state(self):
        for _, signal in DIGITALSIGNALS.items():
            if signal["dir"] == "OUT":
                # 1) Traducimos el puerto y bit usando la lógica de 96 bits de la placa
                port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
                # 2) Ahora sí llamamos a bajo nivel con las coordenadas que la UL entiende
                dio.write_bit(self.dio_board, port_base, bit_offset, signal["initial_state"])
    ```

??? note "Escritura digital: `digital_set(self, signal_name, active)`"
    Permite a la GUI escribir estados lógicos pasando como parametros el nombre de la señal y estado activo o inactivo de la misma que ya esta definido en el diccionario digital, abstrayendo asi la logica que use la señal deseada. 

    ```python
    def digital_set(self, signal_name, active):
        signal = DIGITALSIGNALS[signal_name]
        if active:
            value = signal["active_state"]
        else:
            value = int(not signal["active_state"])
        # Traducimos usando la lógica completa de 96 bits
        port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
        dio.write_bit(self.dio_board, port_base, bit_offset, value)
    ```

??? note "Lectura Digital: `digital_read(self, signal_name)`"
    Permite a la GUI leer estados lógicos pasando como parametro el nombre de la señal, la misma devuelve el estado en que se encuentra la misma, siendo activo o inactivo, por lo tanto al usarla para ver si una entrada cambio de estado preguntaremos si la misma == ACTIVE abstrayendonos asi de la logica que utilice la entrada

    ```python
    def digital_read(self, signal_name):
        signal = DIGITALSIGNALS[signal_name]
        
        # Traducimos usando la lógica completa de 96 bits
        port_base, bit_offset = self.map_to_ul_bit(signal["port"], signal["bit"])
        
        raw_value = dio.read_bit(self.dio_board, port_base, bit_offset)
        return raw_value == signal["active_state"]
    ```

---

## <span style="color: #2196F3;">Operaciones Analógicas de Alto Nivel</span>

??? note "Inhibición de Setpoints de MFCs: `analog_safe_state(self)`"
    Escribe un valor estricto de `0.0` voltios en las líneas de Setpoint de los cuatro controladores de flujo de masa (MFC).

    ```python
    def analog_safe_state(self):
        self.analog_write("MFC1_SETPOINT", 0.0)
        self.analog_write("MFC2_SETPOINT", 0.0)
        self.analog_write("MFC3_SETPOINT", 0.0)
        self.analog_write("MFC4_SETPOINT", 0.0)
    ```

??? note "Escritura Analógica: `analog_write(self, signal_name, voltage)`"
    Controla los canales de salida del DAC de la placa **USB-2527** pasando como parametros el nombre de la señal y la tension a escribir. Aplica un algoritmo de *clamping* o saturación utilizando los límites `min_voltage` y `max_voltage` declarados en la configuración. Esto previene errores de software que intenten enviar tensiones destructivas o fuera de escala a las entradas analógicas proporcionales de los MFC.

    ```python
    def analog_write(self, signal_name, voltage):
        signal = ANALOG_OUTPUTS[signal_name]
        voltage = max(signal["min_voltage"], min(signal["max_voltage"], voltage))
        ad.write_voltage(board=self.ad_board, channel=signal["channel"], voltage=voltage, voltage_range=signal["range"])
    ```

??? note "Lectura Analógica: `analog_read(self, signal_name)`"
    Lee un canal del ADC configurado (como la presión del sensor Baratron o el caudal del MFC) pasando como parametro el nombre de la señal y devuelve el valor leido en tension.

    ```python
    def analog_read(self, signal_name):
        signal = ANALOG_INPUTS[signal_name]
        return ad.read_voltage(board=self.ad_board, channel=signal["channel"], voltage_range=signal["range"])    
    ```

??? note "Lectura de termocupla: `analog_read_temperature(self, tc_name)`"
    Invoca las funciones del driver analógico asociadas al bloque de compensación de junta fría integrado de la placa para leer de forma directa la temperatura de la cámara en grados centígrados, abstrayendo el cálculo polinomial de las termocuplas de proceso.

    ```python
    def analog_read_temperature(self, tc_name):
        tc = THERMOCOUPLE[tc_name]
        return ad.read_temperature(board=self.ad_board, channel=tc["channel"])    
    ```