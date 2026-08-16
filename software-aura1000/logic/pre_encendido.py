"""
Secuencia de pre-encendido del Plasma Asher.

Este módulo contiene únicamente la lógica asociada a la secuencia física
de encendido del equipo.

Responsabilidades:
- Activar las señales necesarias para iniciar el equipo.
- Inicializar el hardware analógico.
- Controlar el tiempo mínimo de precalentamiento.
- Informar el progreso de la secuencia.
- Informar cuándo la secuencia finaliza.

Este módulo no:
- Modifica widgets.
- Cambia pantallas.
- Conoce MainWindow.
- Muestra textos al usuario.
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


class StartupSequence(QObject):
    """Gestiona la secuencia física de pre-encendido."""

    startup_started = pyqtSignal()
    progress_changed = pyqtSignal(int)
    startup_completed = pyqtSignal()
    startup_error = pyqtSignal(str)

    STARTUP_DURATION_MS = 30_000
    TIMER_INTERVAL_MS = 100

    def __init__(self, hardware, parent=None):
        super().__init__(parent)

        self._hardware = hardware
        self._elapsed_ms = 0
        self._running = False

        self._timer = QTimer(self)
        self._timer.setInterval(self.TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._update_progress)

    def start(self):
        """Inicia la secuencia de pre-encendido."""

        if self._running:
            return

        try:
            self._running = True
            self._elapsed_ms = 0

            self.startup_started.emit()
            self.progress_changed.emit(0)

            # Activa la retención de encendido.
            self._hardware.digital_set(
                "POWER_ON",
                ACTIVE,
            )

            # Activa el filamento del magnetrón para iniciar el precalentamiento.
            self._hardware.digital_set(
                "FILAMENT_ENABLE",
                ACTIVE,
            )

            # Inicializa la placa analógica USB-2527.
            self._hardware.initialize_AD()

            self._timer.start()

        except Exception as error:
            self._handle_error(error)

    def stop(self):
        """Detiene el temporizador de la secuencia."""

        self._timer.stop()
        self._running = False

    @property
    def is_running(self):
        """Indica si la secuencia está actualmente en ejecución."""

        return self._running

    def _update_progress(self):
        """Actualiza el progreso según el tiempo transcurrido."""

        self._elapsed_ms += self.TIMER_INTERVAL_MS

        progress = int(
            min(
                100,
                (
                    self._elapsed_ms
                    / self.STARTUP_DURATION_MS
                )
                * 100,
            )
        )

        self.progress_changed.emit(progress)

        if self._elapsed_ms >= self.STARTUP_DURATION_MS:
            self._complete_startup()

    def _complete_startup(self):
        """Finaliza correctamente la secuencia de pre-encendido."""

        try:
            self._timer.stop()

            # El contactor ya queda autoretenido, por lo que se libera
            # la salida POWER_ON.
            self._hardware.digital_set(
                "POWER_ON",
                INACTIVE,
            )

            self._running = False

            self.progress_changed.emit(100)
            self.startup_completed.emit()

        except Exception as error:
            self._handle_error(error)

    def _handle_error(self, error):
        """Detiene la secuencia e informa un error."""

        self._timer.stop()
        self._running = False

        self.startup_error.emit(
            str(error)
        )



# main branch
# logic/pre_encendido.py
'''
from config.digital_signals import ACTIVE, INACTIVE
from services.system_state import systemState

def init(win):
    """Configura el estado visual inicial del Pre-Encendido"""
    win.ui.stackedWidget.setCurrentWidget(win.ui.PreEncendido)
    win.ui.PreEncendido_progressBar.hide()
    win.ui.PreEncendido_progressBar.setRange(0, 100)
    win.startup_progress = 0.0  

def startup(win):
    """Lógica pesada al detectar el flanco de ON"""
    # 1. Activar retención en hardware digital
    win.hw.digital_set("POWER_ON", ACTIVE)

    # 2. Activa el filamento del magnetron, para asegurar que va a precalentar por 30s minimo
    win.hw.digital_set("FILAMENT_ENABLE", ACTIVE)
    
    # 3. Inicializa USB-2527
    win.hw.initialize_AD()  
    
    # 4. Modificar la interfaz gráfica directamente
    win.ui.PreEncendido_label2.setText("Iniciando, espere ...")
    win.ui.PreEncendido_progressBar.show()
    win.ui.PreEncendido_progressBar.setValue(0)
    win.startup_progress = 0
    
    # 5. Vincular y arrancar el timer de progress bar
    try:
        win.timer_manager.timers['startup'].timeout.disconnect()
    except TypeError:
        pass # No estaba conectado antes
        
    win.timer_manager.timers['startup'].timeout.connect(lambda: update_progressBar(win))
    win.timer_manager.timers['startup'].start(100)

def update_progressBar(win):
    """Callback del timer de startup (cada 100ms)"""
    # 100% total / 300 ciclos = 1/3% por cada ciclo de 100ms
    win.startup_progress += 100.0 / 300.0  # incremento exacto (~0.333333)

    # setValue solo acepta int, casteamos la variable float
    win.ui.PreEncendido_progressBar.setValue(int(win.startup_progress))

    # Cuando llegue al 100% (transcurridos los 30s)
    if win.startup_progress >= 100.0:
        win.ui.PreEncendido_progressBar.setValue(100)
        win.timer_manager.timers['startup'].stop()

        # Deja de accionar el SSR pues el contactor queda autoretenido
        win.hw.digital_set("POWER_ON", INACTIVE)
        win.change_state(systemState.MAIN_MENU)
'''