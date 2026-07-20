# `timers_io.py`

El módulo `timers_io.py` implementa la clase `timersIOManager`, para adminsitrar los timers de sistema. Su propósito de arquitectura es centralizar y encapsular la totalidad de los objetos `QTimer` de la aplicación, controlando sus ciclos de vida y ejecutando el lazo periódico de lectura de señales en tiempo real sin bloquear el refresco visual de la interfaz de usuario.

---

## <span style="color: #4CAF50;">Estructura de la Clase `timersIOManager`</span>

??? note "Constructor y Registro de Temporizadores: `__init__(self, main_window)`"
    Almacena de forma segura las referencias de la ventana principal (`MainWindow`) y el servicio de abstracción de hardware (`Hardware`). Inicializa un diccionario indexado (`self.timers`) destinado a mapear los controladores de tiempo, registrando el lazo centralizado (`io_loop`) y el temporizador en blanco dedicado a la fase de estabilización en el encendido (`startup`).

    ```python
    def __init__(self, main_window):
        self.win = main_window      # Referencia a la ventana principal (GUI)
        self.hw = main_window.hw    # Referencia al hardware
        
        # Diccionario para registrar los timers del sistema
        self.timers = {}
        
        # 1. Timer General de Lectura de Entradas (Lazo de 100ms)
        self.timers['io_loop'] = QtCore.QTimer()
        self.timers['io_loop'].timeout.connect(self._update_inputs_loop)
        
        # 2. Timer de la barra de progreso de Pre-Encendido
        self.timers['startup'] = QtCore.QTimer()
    ```

---

## <span style="color: #4CAF50;">Métodos de manejo de timers</span>

??? note "Arranque de timer de lectura de entradas: `start_all_core_timers(self)`"
    Enciende de forma global el temporizador principal del sistema a una tasa de refresco síncrona de **100 ms**, dando inicio formal al sondeo de las líneas físicas de las tarjetas de adquisición.

    ```python
    def start_all_core_timers(self):
        """Arranca el lazo principal de I/O"""
        self.timers['io_loop'].start(100)
    ```

??? note "Parada de timers: `stop_all_timers(self)`"
    Rutina crítica de seguridad llamada de forma mandatoria al interceptarse un evento de cierre de ventana (`closeEvent`) o interlock. Recorre de manera iterativa el diccionario de temporizadores y fuerza el apagado (`.stop()`) de todo lazo que se encuentre en ejecución activa, impidiendo de forma total colisiones de subprocesos o re-lecturas de hardware durante la fase de desconexión segura de las placas.

    ```python
    def stop_all_timers(self):
        """Detiene todos los lazos activos (fundamental para cierre seguro)"""
        for timer in self.timers.values():
            if timer.isActive():
                timer.stop()
    ```

---

## <span style="color: #4CAF50;">Lectura periódica de entradas digitales, presion y temperatura</span>

??? note "Escaneo de Entradas Digitales, presion atmosferica, baratron y temperatura: `_update_inputs_loop(self)`"
    Manejador privado encargado de leer cada 100ms entradas digitales y actualizar la lectura de presion y temperatura del sistema:

    * **Fase `PRE_ENCENDIDO`**: Sondea de forma continua la línea digital del switch físico de marcha. Al registrar un flanco ascendente (`1`), corta el ciclo de sondeo y ordena a la ventana despachar la secuencia de enclavamiento de potencia.
    * **Fase `MAIN_MENU`**: Monitorea de forma prioritaria la línea de presencia de tensión en el lazo de seguridad principal (`SYS_POWER`). Si la línea cae a cero (apertura o parada por hardware), detecta el corte, escribe la alarma en el registro de la consola e invoca el método de apagado inmediato y cierre preventivo de la aplicación.
    Ademas llama cada 100ms a la funcion de lectura de presion del baratron update_pressure_display() que la muestra en la interfaz constantemente . Esta funcion a su vez lee el estado del ATM Switch, para que al ventear, si detecta presion atmosferica, lanze un timer de 4s desde ese momento para que siga venteando un tiempo mas que permite a la camara alcanzar realmente la presion atmosferica ya que el ATM Switch detecta un poco antes. Pasados esos 4s llama a finish_vent_sequence (metodo de maintenace_process.py) para finalizar el venteo.

    ```python
    def _update_inputs_loop(self):
        """Lazo centralizado que corre cada 100ms"""
        # Evalúa según el estado actual de la ventana
        if self.win.current_state == systemState.PRE_ENCENDIDO:
            if self.hw.digital_read("POWER_ON_SWITCH"):
                self.win.preEncendido_startup_sequence()
                
        elif self.win.current_state == systemState.MAIN_MENU:
            # 1. Actualización constante de presion de baratron en display y captura del estado ATM 
            is_atm = self.win.update_pressure_display()

            # 2. MONITOREO DEL VENTEO EN SEGUNDO PLANO
            if self.win.ui.MenuPrincipal_btn_vent_chamber.text() == "Venteando...":
                if is_atm:  # Si el ATM Switch detecto presion atmosferica
                    self.win.ui.MenuPrincipal_btn_vent_chamber.setText("Presión ATM alcanzada...")
                    print("ATM Detectado por lazo central. Iniciando temporización de seguridad...")
                    # Seguira venteando por 4s luego de detectar ATM para que la camara se ventee completamente
                    import logic.maintenance_process as mp
                    QtCore.QTimer.singleShot(4000, lambda: mp.finish_vent_sequence(self.win))

            # 3. Control de apagado general existente
            if self.hw.digital_read("SYS_POWER"):
                print("POWER OFF DETECTADO POR LAZO CENTRAL")
                self.win.trigger_hardware_off()
    ```