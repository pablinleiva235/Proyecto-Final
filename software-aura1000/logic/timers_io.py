# logic/timers_io.py
from PyQt5 import QtCore
from services.system_state import systemState

class timersIOManager:
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

        # 3. Timer rápido dedicado exclusivamente a los pulsos del motor paso a paso
        self.timers['stepper_pulse'] = QtCore.QTimer()

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