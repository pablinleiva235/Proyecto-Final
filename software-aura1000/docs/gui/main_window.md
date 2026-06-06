# `main_window.py`

El módulo `main_window.py` constituye el componente central de la interfaz gráfica de usuario (GUI) y el motor de ejecución del sistema. Implementa la clase `MainWindow`, la cual hereda de `QtWidgets.QMainWindow`, y actúa como el **orquestador principal** del equipo, vinculando los elementos visuales de PyQt5 con las acciones físicas sobre el hardware, la lógica de la máquina de estados y las rutinas críticas de interlock.

---

## <span style="color: #2196F3;">Métodos de Inicialización y Control General</span>

??? note "Inicialización del Constructor: `__init__(self, hardware)`"
    Instancia la clase base, almacena la referencia del hardware compartido para interactuar con las placas de adquisición y configura las condiciones iniciales de la UI. Lanza el temporizador cíclico principal (`io_timer`) a un intervalo de **100 ms** para lectura de entradas e inicializa la máquina de estados en la fase de pre-encendido.

    ```python
    def __init__(self, hardware):
        super().__init__()

        self.hw = hardware
        self.offClose = 0

        # Crear interfaz
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Inicio de timer general de lectura de entradas
        self.io_timer = QtCore.QTimer()
        self.io_timer.timeout.connect(self.update_inputs)
        self.io_timer.start(100)

        # Paso al primer estado: PRE_ENCENDIDO
        self.current_state = SystemState.PRE_ENCENDIDO
        self.change_state(SystemState.PRE_ENCENDIDO)
    ```

??? note "Transición de la Máquina de Estados: `change_state(self, new_state)`"
    Gestiona de forma centralizada los cambios de estado del sistema. Imprime en la consola el flanco de transición, actualiza la variable de estado actual (`current_state`) y deriva el flujo hacia el método de inicialización (*init*) de la fase entrante (`PRE_ENCENDIDO` o `MAIN_MENU`).

    ```python
    def change_state(self, new_state):
        print(f"STATE: {self.current_state} -> {new_state}")
        self.current_state = new_state
        if new_state == SystemState.PRE_ENCENDIDO:
            self.PreEncendido_init()
        elif new_state == SystemState.MAIN_MENU:
            self.MainMenu_init()
    ```

??? note "Lectura de entradas: `update_inputs(self)`"
    Es llamado cuando pasan los 100ms del `io_timer`. Evalúa de forma condicional el estado lógico en el que se encuentra la máquina y luego llama a las funciones de lectura de las entradas de interes en ese estado

    ```python
    def update_inputs(self):
        # Lectura de entradas del estado PRE_ENCENDIDO
        if self.current_state == SystemState.PRE_ENCENDIDO:
            self.PreEncendido_check_power_on()
        # Lectura de entradas del estado MAIN_MENU
        elif self.current_state == SystemState.MAIN_MENU:
            self.MainMenu_check_power_off()
    ```

---

## <span style="color: #2196F3;">Métodos del Estado 0: PRE-ENCENDIDO</span>

??? note "Preparación del Entorno de Arranque: `PreEncendido_init(self)`"
    Se llama al iniciar el programa, fuerza al contenedor multi-página (`stackedWidget`) de la UI a conmutar hacia la pantalla visual indexada como `PreEncendido`, oculta inicialmente la barra de progreso, reseteea el acumulador a cero e instancia el temporizador dedicado (`startup_timer`) para controlar la barra de progreso.

    ```python
    def PreEncendido_init(self):
        #Inicio en pagina 1 de la GUI
        self.ui.stackedWidget.setCurrentWidget(self.ui.PreEncendido)
        # Ocultar barra inicialmente
        self.ui.PreEncendido_progressBar.hide()
        # Variables startup
        self.startup_progress = 0
        # Timer para update de progressbar
        self.startup_timer = QtCore.QTimer()
        self.startup_timer.timeout.connect(self.PreEncendido_update_progressbar)
    ```

??? note "Monitoreo del Pulsador de Marcha: `PreEncendido_check_power_on(self)`"
    Consulta cíclicamente mediante la abstracción de hardware el estado de la línea digital asociada al interruptor físico de marcha (`POWER_ON_SWITCH`). Al detectar un nivel alto (pulsador activo) invoca la secuencia de inicio del equipo.

    ```python
    def PreEncendido_check_power_on(self):
        if self.hw.digital_read("POWER_ON_SWITCH"):
            self.PreEncendido_startup_sequence()
    ```

??? note "Secuencia de Enclavamiento de Potencia: `PreEncendido_startup_sequence(self)`"
    Gobernado por la activación del pulsador físico de marcha, ejecuta de manera secuencial el enclavamiento eléctrico por software de la línea `POWER_ON`, reconfigura las etiquetas informativas de la UI, visualiza la barra de progreso e inicia el temporizador para aumentar la barra cada 100ms.

    ```python
    def PreEncendido_startup_sequence(self):
        # Activar retención
        self.hw.digital_set("POWER_ON", ACTIVE)
        # Cambiar texto
        self.ui.PreEncendido_label2.setText("Iniciando, espere ...")
        # Mostrar barra
        self.ui.PreEncendido_progressBar.show()
        # Reset barra
        self.startup_progress = 0
        self.ui.PreEncendido_progressBar.setValue(0)
        # Inicializar placa analogica
        # self.hw.initialize_AD() DESCOMENTAR ESTO EN NOTEBOOK DE SALA!!!!
        # Arrancar timer
        self.startup_timer.start(100)
    ```

??? note "Control de Estabilización del Sistema: `PreEncendido_update_progressbar(self)`"
    Incrementa linealmente el acumulador en una unidad y actualiza el valor del widget visual de la barra de progreso. Al estar configurado a un paso por cada 100 ms, alcanzar el límite de **100 pasos** garantiza un delay de **10 segundos** de estabilización térmica/eléctrica. Cumplido el tiempo, frena el timer y transiciona el sistema a `MAIN_MENU`.

    ```python
    def PreEncendido_update_progressbar(self):
        self.startup_progress += 1
        self.ui.PreEncendido_progressBar.setValue(self.startup_progress)
        # 100 pasos x 100ms = 10 segundos
        if self.startup_progress >= 100:
            self.startup_timer.stop()
            # Paso a estado MAIN_MENU
            self.change_state(SystemState.MAIN_MENU)
    ```

---

## <span style="color: #2196F3;">Métodos del Estado 1: MAIN_MENU y Cierre Seguro</span>

??? note "Inicialización del Menú de Operación: `MainMenu_init(self)`"
    Produce el cambio de página en el contenedor gráfico de Qt para desplegar el entorno operativo principal (`MenuPrincipal`), donde se exponen el menu principal del equipo

    ```python
    def MainMenu_init(self):
        # Ir al menú principal --> cambio de pagina
        self.ui.stackedWidget.setCurrentWidget(self.ui.MenuPrincipal)
        # Logica de botones Abrir puerta y Habilitar Driver
    ```

??? note "Monitoreo del Interruptor de Apagado General: `MainMenu_check_power_off(self)`"
    Monitorea de forma continua la línea digital de entrada `SYS_POWER` desde el menú principal. Si se detecta una caída de tensión o flanco inactivo en el lazo de potencia del equipo, setea el flag `offClose = 1` para saltearse la confirmación de software y fuerza el disparo del método nativo `close()`.

    ```python
    def MainMenu_check_power_off(self):
        if self.hw.digital_read("SYS_POWER"):
            print("POWER OFF DETECTADO")
            self.offClose = 1
            self.close()
    ```
---

## <span style="color: #2196F3;">Método de cierre del programa</span>

??? note "`closeEvent(self, event)`"
    Sobrescribe el evento nativo de destrucción de la ventana de Qt para actuar como un interlock de seguridad crítico. Discrimina el origen del cierre: si es manual por la "X" (`offClose == 0`), lanza un cuadro interactivo (`QMessageBox.question`) de confirmación; si es provocado por hardware (`offClose == 1`), muestra un aviso informativo directo. En ambos casos aceptados, fuerza la llamada a `hw.shutdown_state()` para desactivar relés y actuadores, detiene el lazo de timers y apaga el sistema en un estado pasivo seguro.

    ```python
    def closeEvent(self, event):
        if self.offClose == 0:
            # --- CASO 1: Cierre por la "X" (Pregunta Confirmación) ---
            reply = QtWidgets.QMessageBox.question(
                self, 
                'Confirmar Salida',
                '¿Está seguro de que desea cerrar la aplicación?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                try:
                    # Llevamos el hardware a estado seguro y frenamos el lazo de I/O
                    self.hw.shutdown_state()
                    self.io_timer.stop()
                    print("Hardware llevado a estado seguro correctamente.")
                except Exception as e:
                    print(f"Error al intentar llevar el hardware a estado seguro: {e}")
                
                event.accept()
            else:
                event.ignore()
                
        else:
            # --- CASO 2: Cierre por pulsador físico OFF (Aviso obligatorio) ---
            QtWidgets.QMessageBox.information(
                self,
                'Apagado del Sistema',
                'El programa se cerrará dejando las placas en estado seguro.',
                QtWidgets.QMessageBox.Ok
            )
            
            try:
                # Forzamos de igual manera el estado seguro y apagamos el timer
                self.hw.shutdown_state()
                self.io_timer.stop()
                print("Hardware llevado a estado seguro de forma automática por pulsador OFF.")
            except Exception as e:
                print(f"Error al intentar llevar el hardware a estado seguro en apagado directo: {e}")
            
            # Aceptamos el cierre directamente sin más preguntas
            event.accept()
    ```