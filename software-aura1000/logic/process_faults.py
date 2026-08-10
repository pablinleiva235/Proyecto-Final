# logic/process_faults.py

from PyQt5 import QtWidgets
from config.digital_signals import ACTIVE, INACTIVE


def check_process_faults(win, hw):
    """Monitorea las entradas digitales de fallas de Lámparas, Plasma y Magnetrón.
    Las fallas de Lámparas y Plasma solo se evalúan si sus comandos de salida están ACTIVOS.
    """
    if getattr(win, "alarm_active", False):
        return

    # 1. Leer comandos activos desde las banderas de software de win
    cmd_lamps13 = getattr(win, "state_lamps13_pulsing", False)
    cmd_lamp2 = getattr(win, "lamp2_on", False)
    cmd_rf = getattr(win, "rf_on", False)

    # 2. Evaluar fallas SOLO si el comando correspondiente está activo
    lamp1_fail = cmd_lamps13 and hw.digital_read("LAMP1_FAIL")
    lamp2_fail = cmd_lamp2 and hw.digital_read("LAMP2_FAIL")
    lamp3_fail = cmd_lamps13 and hw.digital_read("LAMP3_FAIL")
    plasma_fail = cmd_rf and hw.digital_read("PLASMA_FAIL")

    # 3. Sensores del Magnetrón (monitoreo continuo)
    mag_warning = hw.digital_read("MAGNETRON_WARNING")
    mag_overheat = hw.digital_read("MAGNETRON_OVERHEAT")

    critical_fault = (lamp1_fail or lamp2_fail or lamp3_fail or plasma_fail or mag_overheat)

    if critical_fault:
        win.alarm_active = True

        # A. Apagado físico de salidas en hardware
        hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        hw.digital_set("LAMP3_ON_CMD", INACTIVE)
        hw.digital_set("RF_ON_CMD", INACTIVE)

        # B. Resetear todas las banderas de estado a False
        win.state_lamps13_pulsing = False
        win.lamp2_on = False
        win.rf_on = False

        # C. Activar indicador de alarma físico
        hw.digital_set("ALARM_INDICATION", ACTIVE)

        # D. Construir mensaje de error
        messages = []
        if lamp1_fail:
            messages.append("• Falla en Lámpara 1 (Pérdida de corriente)")
        if lamp2_fail:
            messages.append("• Falla en Lámpara 2 (Pérdida de corriente)")
        if lamp3_fail:
            messages.append("• Falla en Lámpara 3 (Pérdida de corriente)")
        if plasma_fail:
            messages.append("• Falla en Plasma (Pérdida de acople RF)")
        if mag_overheat:
            messages.append("• Sobrecalentamiento crítico de Magnetrón (93°C)")

        msg_text = ("Se ha interrumpido la operación por seguridad debido a:\n\n"+ "\n".join(messages))

        import logic.maintenance_process as mp

        mp.update_vent_button_state(win)

        # E. Ventana emergente (modal)
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