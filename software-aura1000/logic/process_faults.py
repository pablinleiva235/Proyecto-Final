# logic/process_faults.py
import time
from PyQt5 import QtWidgets
from config.digital_signals import ACTIVE, INACTIVE

# Tiempo de gracia para dar margen a la ionización del plasma antes de evaluar la falla
PLASMA_IGNITION_DELAY = 2.0  # en segundos

def check_process_faults(win, hw):
    if getattr(win, "alarm_active", False):
        return

    now = time.time()
    
    # 1. Leer estado de los comandos
    cmd_lamps13 = getattr(win, "state_lamps13_pulsing", False)
    cmd_lamp2 = getattr(win, "lamp2_on", False)
    cmd_rf = getattr(win, "rf_on", False)

    if cmd_rf:
        elapsed = now - getattr(win, "rf_on_time", 0.0)
        signal = hw.digital_read("PLASMA_FAIL")
        print(
            f"[DIAGNOSTICO PLASMA] T: {elapsed:.1f}s | PLASMA_FAIL pin: {signal}"
        )
        
    # 2. Lámparas: evaluación inmediata (responden rápido)
    lamp1_fail = cmd_lamps13 and hw.digital_read("LAMP1_FAIL")
    lamp2_fail = cmd_lamp2 and hw.digital_read("LAMP2_FAIL")
    lamp3_fail = cmd_lamps13 and hw.digital_read("LAMP3_FAIL")

    # 3. Plasma: se evalúa SOLO si pasaron más de 2 segundos desde el comando de encendido
    rf_grace_period_passed = (now - getattr(win, "rf_on_time", 0.0)) > PLASMA_IGNITION_DELAY
    plasma_fail = (cmd_rf and rf_grace_period_passed and hw.digital_read("PLASMA_FAIL"))

    # 4. Magnetrón (monitoreo continuo)
    mag_warning = hw.digital_read("MAGNETRON_WARNING")
    mag_overheat = hw.digital_read("MAGNETRON_OVERHEAT")

    critical_fault = (lamp1_fail or lamp2_fail or lamp3_fail or plasma_fail or mag_overheat)

    if critical_fault:
        win.alarm_active = True

        # 1 - Detener el motor y el control de la Throttle Valve ──────
        if hasattr(win, "throttle"):
            win.throttle.stop_auto_control()  # Detiene la regulación y congela el moto

        # 2 - Apagado inmediato en hardware
        hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        hw.digital_set("LAMP3_ON_CMD", INACTIVE)
        hw.digital_set("RF_ON_CMD", INACTIVE)

        # 3 - Reset de banderas de software
        win.state_lamps13_pulsing = False
        win.lamp2_on = False
        win.rf_on = False

        # 4 - Activar indicador de alarma físico
        hw.digital_set("ALARM_INDICATION", ACTIVE)

        # 5 - Reset visual de botones en UI
        win.ui.MenuPrincipal_btn_centralLamp.setText("Lamp 2 On")
        win.ui.MenuPrincipal_btn_centralLamp.setStyleSheet("")

        win.ui.MenuPrincipal_btn_plasma.setText("Plasma On")
        win.ui.MenuPrincipal_btn_plasma.setStyleSheet("")

        win.ui.MenuPrincipal_btn_outerLamps.setEnabled(True)
        win.ui.MenuPrincipal_btn_outerLamps.setStyleSheet("")

        # 6 - Mensaje de alarma
        messages = []
        if lamp1_fail:
            messages.append("• Falla en Lámpara 1 (Pérdida de corriente)")
        if lamp2_fail:
            messages.append("• Falla en Lámpara 2 (Pérdida de corriente)")
        if lamp3_fail:
            messages.append("• Falla en Lámpara 3 (Pérdida de corriente)")
        if plasma_fail:
            messages.append("• Falla en Plasma (No logró encender o se cortó la RF)")
        if mag_overheat:
            messages.append("• Sobrecalentamiento de Magnetrón (93°C)")

        msg_text = ("Se ha interrumpido la operación por seguridad debido a:\n\n" + "\n".join(messages)
        )

        import logic.maintenance_process as mp

        mp.update_vent_button_state(win)

        # Ventana de diálogo modal
        QtWidgets.QMessageBox.warning(win, "¡ALERTA DE SEGURIDAD!", msg_text, QtWidgets.QMessageBox.Ok)

        win.alarm_active = False

    elif mag_warning:
        if not getattr(win, "warning_mag_shown", False):
            win.warning_mag_shown = True
            hw.digital_set("ALARM_INDICATION", ACTIVE)

            QtWidgets.QMessageBox.warning(
                win,
                "Advertencia de Temperatura",
                "El Magnetrón ha alcanzado los 85°C (MAGNETRON_WARNING).\n"
                "El proceso continúa, pero vigile la temperatura.",
                QtWidgets.QMessageBox.Ok,
            )
    else:
        hw.digital_set("ALARM_INDICATION", INACTIVE)
        win.warning_mag_shown = False