# logic/timers_io.py
from PyQt5 import QtCore
from services.system_state import SystemState

class TimersIOManager:
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

    def start_all_core_timers(self):
        """Arranca el lazo principal de I/O"""
        self.timers['io_loop'].start(100)

    def stop_all_timers(self):
        """Detiene todos los lazos activos (fundamental para cierre seguro)"""
        for timer in self.timers.values():
            if timer.isActive():
                timer.stop()

    def _update_inputs_loop(self):
        """Lazo centralizado que corre cada 100ms"""
        # Evalúa según el estado actual de la ventana
        if self.win.current_state == SystemState.PRE_ENCENDIDO:
            if self.hw.digital_read("POWER_ON_SWITCH"):
                self.win.PreEncendido_startup_sequence()
                
        elif self.win.current_state == SystemState.MAIN_MENU:
            if self.hw.digital_read("SYS_POWER"):
                print("POWER OFF DETECTADO POR LAZO CENTRAL")
                self.win.trigger_hardware_off()