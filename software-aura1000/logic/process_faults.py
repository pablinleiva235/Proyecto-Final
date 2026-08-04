# logic/process_faults.py

from PyQt5 import QtWidgets
from config.digital_signals import ACTIVE, INACTIVE


def check_process_faults(win, hw):
    """Monitorea las entradas digitales de fallas de Lámparas, Plasma y Magnetrón.

    Si detecta fallas críticas, apaga la potencia, activa ALARM_INDICATION
    y despliega una ventana de advertencia (warning popup).
    """
    # Si ya hay una alarma activa mostrándose, evitamos reentrada en cada ciclo de 100ms
    if getattr(win, "alarm_active", False):
        return

    # 1. Leer todas las entradas digitales de falla
    lamp1_fail = hw.digital_read("LAMP1_FAIL")
    lamp2_fail = hw.digital_read("LAMP2_FAIL")
    lamp3_fail = hw.digital_read("LAMP3_FAIL")
    plasma_fail = hw.digital_read("PLASMA_FAIL")

    mag_warning = hw.digital_read("MAGNETRON_WARNING")
    mag_overheat = hw.digital_read("MAGNETRON_OVERHEAT")

    critical_fault = (lamp1_fail or lamp2_fail or lamp3_fail or plasma_fail or mag_overheat)

    if critical_fault:
        # Bloqueo de seguridad para no abrir múltiples pop-ups superpuestos
        win.alarm_active = True

        # A. Apagado inmediato de potencia en hardware
        hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        hw.digital_set("LAMP3_ON_CMD", INACTIVE)
        hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        hw.digital_set("RF_ON_CMD", INACTIVE)

        # B. Activar indicador físico de alarma
        hw.digital_set("ALARM_INDICATION", ACTIVE)

        # C. Resetear banderas de UI
        win.state_lamps13_pulsing = False

        # D. Construir el mensaje formateado para la alerta
        messages = []
        if lamp1_fail:
            messages.append("• Falla en Lámpara 1 (Filamento / Corriente)")
        if lamp2_fail:
            messages.append("• Falla en Lámpara 2 (Filamento / Corriente)")
        if lamp3_fail:
            messages.append("• Falla en Lámpara 3 (Filamento / Corriente)")
        if plasma_fail:
            messages.append("• Falla en Plasma (Pérdida de RF)")
        if mag_overheat:
            messages.append("• Sobrecalentamiento extremo de Magnetrón (93°C)")

        msg_text = ("Se ha interrumpido la operación por seguridad debido a:\n\n" + "\n".join(messages))

        import logic.maintenance_process as mp

        mp.update_vent_button_state(win)

        # E. Mostrar ventana emergente con ícono de Exclamación (Warning)
        QtWidgets.QMessageBox.warning(win, "¡ALERTA DE SEGURIDAD!", msg_text, QtWidgets.QMessageBox.Ok)

        # Liberar la bandera al cerrar el diálogo
        win.alarm_active = False

    elif mag_warning:
        # Advertencia preventiva de 85°C (no apaga el proceso)
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
        # Si no hay ninguna falla ni advertencia activa, apaga el indicador
        hw.digital_set("ALARM_INDICATION", INACTIVE)
        win.warning_mag_shown = False