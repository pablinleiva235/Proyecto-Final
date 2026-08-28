# `process_faults.py`

El módulo `process_faults.py` tiene el metodo llamado en el timer general cada 100ms para leer las señales de falla de lamparas, magnetron y plasma, dando aviso al usuario si ocurrio alguna, encendiendo el indicador de alarma y apagando estos modulos de potencia

---

## <span style="color: #4CAF50;">Monitoreo de Seguridad e Interbloqueos de Falla</span>

??? note "Gestor y Evaluación de Fallas de Proceso: `check_process_faults(win, hw)`"
    Rutina periódica de monitoreo e interbloqueo de seguridad que evalúa en tiempo real las señales de retroalimentación de las lámparas infrarrojas, la fuente de radiofrecuencia (RF) de plasma y la protección térmica del magnetrón:

    * **Lámparas Infrarrojas (1, 2 y 3):** Evaluación inmediata ante pérdida de corriente o falla física (`LAMP1_FAIL`, `LAMP2_FAIL`, `LAMP3_FAIL`).
    * **Generador de Plasma / RF:** Aplica un tiempo de gracia de **2.0 segundos** (`PLASMA_IGNITION_DELAY`) desde la habilitación del comando para contemplar la ventana de ionización del gas antes de evaluar el pin de falla (`PLASMA_FAIL`), evitando así disparos en falso por retardo en el encendido.
    * **Protección Térmica del Magnetrón:** Monitorea de forma continua los sensores de sobretemperatura (`MAGNETRON_WARNING` a 85 °C y `MAGNETRON_OVERHEAT` a 93 °C).

    Ante la presencia de una **falla crítica** (falla en cualquier lámpara, caída de plasma fuera del ventana de gracia o sobrecalentamiento del magnetrón), apaga de forma inmediata las órdenes de encendido en el hardware, enciende el indicador físico de alarma (`ALARM_INDICATION`), resetea los estados visuales en la interfaz gráfica y despliega una ventana modal notificando al operario las causas específicas de la interrupción.

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

        critical_fault = (
            lamp1_fail or lamp2_fail or lamp3_fail or plasma_fail or mag_overheat
        )

        if critical_fault:
            win.alarm_active = True

            # Apagado inmediato en hardware
            hw.digital_set("LAMP1_ON_CMD", INACTIVE)
            hw.digital_set("LAMP2_ON_CMD", INACTIVE)
            hw.digital_set("LAMP3_ON_CMD", INACTIVE)
            hw.digital_set("RF_ON_CMD", INACTIVE)

            # Reset de banderas de software
            win.state_lamps13_pulsing = False
            win.lamp2_on = False
            win.rf_on = False

            # Activar indicador de alarma físico
            hw.digital_set("ALARM_INDICATION", ACTIVE)

            # Reset visual de botones en UI
            win.ui.MenuPrincipal_btn_centralLamp.setText("Lamp 2 On")
            win.ui.MenuPrincipal_btn_centralLamp
    ```