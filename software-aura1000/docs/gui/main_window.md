# `main_window.py`

El módulo `main_window.py` constituye el componente de interfaz gráfica de usuario (GUI) y el núcleo coordinador de estados del sistema. Implementa la clase `MainWindow`, la cual hereda de `QtWidgets.QMainWindow`. Vinculan la interfaz autogenerada de PyQt5 con el servicio de hardware y delegando la ejecución secuencial de los timers y la lógica I/O a los administradores externos de la carpeta `/logic`.

---

## <span style="color: #2196F3;">Métodos de Inicialización y Máquina de Estados</span>

??? note "Inicialización del Constructor: `__init__(self, hardware)`"
    Instancia la clase base, inicializa un flag para determinar como se cerro el programa y configura los elementos visuales autogenerados. En lugar de contener timers locales, instancia el administrador externo de tiempos (`timersIOManager`) pasándose a sí mismo como referencia (`self`) y enciende el lazo de I/O principal de 100 ms. Finalmente, fuerza la entrada del sistema al estado de pre-encendido.

    ```python
    def __init__(self, hardware):
        super().__init__()
        
        self.hw = hardware
        self.offClose = 0
        self.startup_progress = 0  # Almacena el progreso de la barra

        # Crear interfaz autogenerada
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Instanciar el manager de timers pasándole 'self' (esta ventana)
        self.timer_manager = timersIOManager(self)
        self.timer_manager.start_all_core_timers()

        # Iniciar la máquina de estados en PRE_ENCENDIDO
        self.current_state = systemState.PRE_ENCENDIDO
        self.change_state(systemState.PRE_ENCENDIDO)
    ```

??? note "Transición de la Máquina de Estados: `change_state(self, new_state)`"
    Gestiona de forma centralizada las transiciones de la máquina de estados. Actualiza el registro de estado interno (`current_state`) y deriva el flujo operacional. Si ingresa a `PRE_ENCENDIDO`, delega la inicialización visual y de variables al módulo externo `preEncendido.init(self)`. Si ingresa a `MAIN_MENU`, invoca el método local de carga de la pantalla principal.

    ```python
    def change_state(self, new_state):
        print(f"STATE: {self.current_state} -> {new_state}")
        self.current_state = new_state
        
        if new_state == systemState.PRE_ENCENDIDO:
            preEncendido.init(self)
        elif new_state == systemState.MAIN_MENU:
            self.MainMenu_init()
    ```

---

## <span style="color: #2196F3;">Acciones Invocadas por la Lógica Externa</span>

??? note "Inicio de Secuencia de encendido: `preEncendido_startup_sequence(self)`"
    Funciona como un punto de entrada de callback. Cuando el lazo de lectura de entradas detecta que el operador presionó el pulsador físico de marcha (`POWER_ON_SWITCH`), invoca esta función, la cual desvía inmediatamente el control al script de lógica específico (`preEncendido.startup(self)`) para procesar el enclavamiento y la barra de progreso de 10 segundos.

    ```python
    def preEncendido_startup_sequence(self):
        # La lógica de timers detectó el botón ON y le ordena a la ventana ejecutar el startup
        preEncendido.startup(self)
    ```

??? note "Inicialización del Menú Inicial: `MainMenu_init(self)`"
    Se encarga exclusivamente de la conmutación de la interfaz gráfica a nivel visual, forzando al contenedor multipágina (`stackedWidget`) a desplegar la pantalla indexada del entorno operativo principal (`MenuPrincipal`).

    ```python
    def MainMenu_init(self):
        # Inicializa visualmente el menú principal
        self.ui.stackedWidget.setCurrentWidget(self.ui.MenuPrincipal)
        # Próximamente llamarás acá a: logic.vacuum.init_menu(self)
    ```

??? note "Apagado por Hardware: `trigger_hardware_off(self)`"
    Es invocado por el administrador de timers externo cuando detecta un nivel alto en la línea digital `SYS_POWER` (pulsador físico de OFF). Eleva la bandera de control (`offClose = 1`) para indicar un cierre por hardware y ejecuta la llamada al método nativo `self.close()`, lo que desvía el flujo de manera segura hacia el manejador de eventos `closeEvent`.

    ```python
    def trigger_hardware_off(self):
        # Fuerza el cierre seguro por pulsador físico OFF
        self.offClose = 1
        self.close() # Esto llama a closeEvent
    ```

---

## <span style="color: #2196F3;">Control de Cierre Seguro de Ventana</span>

??? note "Cierre de la interfaz: `closeEvent(self, event)`"
    Sobrescribe el método nativo de PyQt para el cierre de la ventana, actuando como un enclavamiento de seguridad crítico de la aplicación. Lo primero que realiza es congelar inmediatamente todos los lazos y timers activos del sistema (`stop_all_timers()`). Luego discrimina el tipo de apagado: si es por interfaz manual (`offClose == 0`), exige confirmación del usuario; si es por pulsador físico (`offClose == 1`), muestra un cuadro informativo directo. En ambos casos confirmados, invoca la rutina de desactivación del hardware.

    ```python
    def closeEvent(self, event):
        # Frenamos todos los lazos de tiempo antes de abrir diálogos
        self.timer_manager.stop_all_timers()

        if self.offClose == 0:
            # --- CASO 1: Cierre por la "X" del software ---
            reply = QtWidgets.QMessageBox.question(
                self, 'Confirmar Salida', '¿Está seguro de que desea cerrar la aplicación?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self._safely_shutdown()
                event.accept()
            else:
                # Si cancela, reactivamos los timers de lectura
                self.timer_manager.start_all_core_timers()
                event.ignore()
        else:
            # --- CASO 2: Cierre por pulsador físico OFF ---
            QtWidgets.QMessageBox.information(
                self, 'Apagado del Sistema', 'El programa se cerrará dejando las placas en estado seguro.', QtWidgets.QMessageBox.Ok
            )
            self._safely_shutdown()
            event.accept()
    ```

??? note "Desactivación Crítica de Periféricos: `_safely_shutdown(self)`"
    Método privado encargado de la seguridad de la sala limpia. Llama de forma directa a las funciones de bajo nivel encapsuladas en `hw.shutdown_state()`, garantizando de forma obligatoria que todos los actuadores, válvulas y relés de potencia de RF se desactiven y queden en un estado pasivo y seguro, previniendo daños eléctricos ante errores de la app.

    ```python
    def _safely_shutdown(self):
        try:
            self.hw.shutdown_state()
            print("Hardware llevado a estado seguro correctamente.")
        except Exception as e:
            print(f"Error al intentar llevar el hardware a estado seguro: {e}")
    ```