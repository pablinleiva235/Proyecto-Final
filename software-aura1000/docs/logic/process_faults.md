# `process_faults.py`

El módulo `process_faults.py` tiene el metodo llamado en el timer general cada 100ms para leer las señales de falla de lamparas, magnetron y plasma, dando aviso al usuario si ocurrio alguna, encendiendo el indicador de alarma y apagando estos modulos de potencia

---

## <span style="color: #4CAF50;">Monitoreo de Seguridad e Interbloqueos de Falla</span>

??? note "Gestor y Evaluación de Fallas de Proceso: `check_process_faults(win, hw)`"
    Rutina periódica de monitoreo e interbloqueo de seguridad que evalúa en tiempo real las señales de retroalimentación de las lámparas infrarrojas, la fuente de radiofrecuencia (RF) de plasma y la protección térmica del magnetrón:

    * **Lámparas Infrarrojas (1, 2 y 3):** Evaluación inmediata ante pérdida de corriente o falla física (`LAMP1_FAIL`, `LAMP2_FAIL`, `LAMP3_FAIL`).
    * **Generador de Plasma / RF:** Aplica un tiempo de gracia de **2.0 segundos** (`PLASMA_IGNITION_DELAY`) desde la habilitación del comando para contemplar la ventana de ionización del gas antes de evaluar el pin de falla (`PLASMA_FAIL`), evitando así disparos en falso por retardo en el encendido.
    * **Protección Térmica del Magnetrón:** Monitorea de forma continua los sensores de sobretemperatura (`MAGNETRON_WARNING` a 85 °C y `MAGNETRON_OVERHEAT` a 93 °C).

    Ante la presencia de una **falla crítica** (falla en cualquier lámpara, caída de plasma fuera del ventana de gracia o sobrecalentamiento del magnetrón), detiene la throttle si estaba ajustando, apaga de forma inmediata las órdenes de encendido en el hardware, enciende el indicador físico de alarma (`ALARM_INDICATION`), resetea los estados visuales en la interfaz gráfica y despliega una ventana modal notificando al operario las causas específicas de la interrupción.

    ```python
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
    ```