# logic/timers_io.py
from PyQt5 import QtCore
from services.system_state import systemState
import logic.analog_update as analog_up
import logic.process_faults as faults

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

        if self.win.current_state == systemState.PRE_ENCENDIDO:
            if self.hw.digital_read("POWER_ON_SWITCH"):
                self.win.preEncendido_startup_sequence()

        elif self.win.current_state == systemState.MAIN_MENU:
            # 1. Actualización constante de presión y captura del estado ATM
            is_atm = analog_up.update_pressure_display(self.win)

            # 2. Actualización en tiempo real de caudales de MFCs
            analog_up.update_mfc_displays(self.win)

            # 3. Lectura y actualización de temperatura
            analog_up.update_temp_display(self.win)

            # 4. Lectura y actualización del sensor EOP
            analog_up.update_eop_displays(self.win)

            # 5. Monitoreo del venteo
            if (self.win.ui.MenuPrincipal_btn_vent_chamber.text() == "Venteando..."):
                if is_atm:
                    self.win.ui.MenuPrincipal_btn_vent_chamber.setText("Presión ATM alcanzada...")
                    print("ATM Detectado. Iniciando temporización extra de seguridad...")
                    import logic.maintenance_process as mp
                    QtCore.QTimer.singleShot(4000, lambda: mp.finish_vent_sequence(self.win))

            # 5.1 Monitoreo de fallas de hardware (Lámparas, Plasma, Magnetrón)
            faults.check_process_faults(self.win, self.hw)

            # 6. Control de apagado general
            if self.hw.digital_read("SYS_POWER"):
                print("POWER OFF DETECTADO POR PULSADOR DE OFF")
                self.win.trigger_hardware_off()