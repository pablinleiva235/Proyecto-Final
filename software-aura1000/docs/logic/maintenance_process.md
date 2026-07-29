# `maintenance_process.py`

El módulo `maintenance_process.py` agrupa metodos para poder ir probando mediante la interfaz, de manera secuencial, los distintos modulos que utiliza el proceso. La idea es que quede en el modo mantenimiento para poder hacer un proceso de forma no automatica y probar que los modulos esten funcionando correctamente

---

## <span style="color: #4CAF50;">Funciones de proceso en modo Mantenimiento</span>

??? note "Inicializacion: `init(win)`"
    Se ejecuta de forma síncrona al inicializar la vista de mantenimiento. Limpia preventivamente cualquier acoplamiento o señal previa en los pulsadores mediante bloques `try-except` para evitar ejecuciones duplicadas (doble disparo) en el entorno gráfico, asociando luego cada evento `clicked` a su rutina lógica correspondiente mediante funciones `lambda`.

    ```python
    def init(win):
        """Inicializa las conexiones de los botones del Menú Principal (Mantenimiento)."""
        buttons = [
            win.ui.MenuPrincipal_btn_enable_driver,
            win.ui.MenuPrincipal_btn_open_door,
            win.ui.MenuPrincipal_btn_soft_vacuum,
            win.ui.MenuPrincipal_btn_main_vacuum,
            win.ui.MenuPrincipal_btn_vent_chamber
        ]
        for btn in buttons:
            try:
                btn.clicked.disconnect()
            except TypeError:
                pass

        win.ui.MenuPrincipal_btn_enable_driver.clicked.connect(lambda: toggle_drivers(win))
        win.ui.MenuPrincipal_btn_open_door.clicked.connect(lambda: toggle_door(win))
        win.ui.MenuPrincipal_btn_soft_vacuum.clicked.connect(lambda: toggle_soft_vacuum(win))
        win.ui.MenuPrincipal_btn_main_vacuum.clicked.connect(lambda: toggle_main_vacuum(win))
        win.ui.MenuPrincipal_btn_vent_chamber.clicked.connect(lambda: vent_chamber(win))
    ```

??? note "Habilitacion de drivers: `toggle_drivers(win)`"
    Habilita los Drivers SN75436 de la AURA 1000 DIO para poder manejar las señales que requieren mayor tension.

    ```python
    def toggle_drivers(win):
        """Controla la habilitación y deshabilitación de los drivers de la placa DIO."""
        btn = win.ui.MenuPrincipal_btn_enable_driver
        
        if btn.text() == "Habilitar Drivers":
            win.hw.digital_set("DRIVER_ENABLE", ACTIVE)
            btn.setText("Deshabilitar Drivers")
            btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            win.hw.digital_set("DRIVER_ENABLE", INACTIVE)
            btn.setText("Habilitar Drivers")
            btn.setStyleSheet("")
    ```

??? note "Apertura/Cierre de puerta: `toggle_door(win)`"
    Administra la apertura y cierre del pistón neumático de la puerta de cámara de proceso. Si abre, deshabilita los botones para hacer vacio y ventear

    ```python
    def toggle_door(win):
        """ Controla la apertura y el cierre seguro de la puerta de la cámara. """
        btn = win.ui.MenuPrincipal_btn_open_door
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum
        btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
        
        if btn.text() == "Abrir Puerta":
            win.hw.digital_set("DOOR_CLOSE_CMD", INACTIVE)
            win.hw.digital_set("DOOR_OPEN_CMD", ACTIVE)
            btn_soft.setEnabled(False)
            btn_main.setEnabled(False)
            btn_vent.setEnabled(False)
            btn.setText("Cerrar Puerta")
            btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            win.hw.digital_set("DOOR_OPEN_CMD", INACTIVE)
            win.hw.digital_set("DOOR_CLOSE_CMD", ACTIVE)
            btn_soft.setEnabled(True)
            btn_main.setEnabled(True)
            btn_vent.setEnabled(True)
            btn.setText("Abrir Puerta")
            btn.setStyleSheet("")
    ```

??? note "Encendido/Apagado de valvula de Soft Vacuum: `toggle_soft_vacuum(win)`"
    Modula la válvula neumática encargada del vacío lento o inicial (`SOFT_START_CONTROL`). Al encenderse, bloquea de forma mandatoria la interfaz del operario para impedir la apertura física de la puerta bajo vacío. 

    ```python
    def toggle_soft_vacuum(win):
        """
        Controla la habilitación y deshabilitación de la válvula neumática de soft vacuum.
        """
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum
        btn_door = win.ui.MenuPrincipal_btn_open_door
        
        if btn_soft.text() == "Soft Vacuum On":
            win.hw.digital_set("SOFT_START_CONTROL", ACTIVE)
            btn_soft.setText("Soft Vacuum Off")
            btn_soft.setStyleSheet("background-color: #f44336; color: white;")
            btn_door.setEnabled(False)
        else:
            win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
            btn_soft.setText("Soft Vacuum On")
            btn_soft.setStyleSheet("")
            
            # Habilita la puerta solo si Main Vacuum tampoco está activo
            if btn_main.text() == "Main Vacuum On":
                btn_door.setEnabled(True)
    ```

??? note "Encendido/Apagado de valvula de Soft Vacuum: `toggle_main_vacuum(win)`"
    Comanda la válvula de alto flujo de vacío (`MAIN_VACUUM_CONTROL`). Solo se puede accionar si esta habilitada la valvula de Soft Vacuum. Una vez encendida la valvula de Main Vacuum, se apaga la de Soft Vacuum

    ```python
    def toggle_main_vacuum(win):
        """
        Controla la activación de Main Vacuum.
        Al encenderlo, apaga automáticamente Soft Vacuum según el manual del equipo.
        """
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_door = win.ui.MenuPrincipal_btn_open_door
        
        # 1. Validación de prerrequisito
        if btn_soft.text() == "Soft Vacuum On" and btn_main.text() == "Main Vacuum On":
            QtWidgets.QMessageBox.warning(
                win, 
                "Secuencia Inválida", 
                "No se puede activar Main Vacuum si Soft Vacuum no está encendido primero.",
                QtWidgets.QMessageBox.Ok
            )
            return

        # 2. Encendido / Apagado de Main Vacuum
        if btn_main.text() == "Main Vacuum On":
            win.hw.digital_set("MAIN_VACUUM_CONTROL", ACTIVE)
            btn_main.setText("Main Vacuum Off")
            btn_main.setStyleSheet("background-color: #f44336; color: white;")
            btn_door.setEnabled(False)
            
            # <-- APAGADO AUTOMÁTICO DE SOFT VACUUM
            if btn_soft.text() == "Soft Vacuum Off":
                win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
                btn_soft.setText("Soft Vacuum On")
                btn_soft.setStyleSheet("")
                print("[INFO] Soft Vacuum cerrado automáticamente al pasar a Main Vacuum.")
            
            # Habilitación de MFCs al alcanzar vacío principal
            set_mfc_controls_enabled(win, True)
        else:
            win.hw.digital_set("MAIN_VACUUM_CONTROL", INACTIVE)
            btn_main.setText("Main Vacuum On")
            btn_main.setStyleSheet("")
            
            # Corte de vacío principal: deshabilitamos MFCs
            set_mfc_controls_enabled(win, False)
    ```

??? note "Venteo de camara: `vent_chamber(win)`"
    Maneja la apertura física de la línea de nitrógeno/aire hacia el interior de la cámara (`VENT_VALVE_CONTROL`). Evalúa rigurosamente que no existan líneas de vacío succionando en simultáneo. Si pasa los filtros, inicia el venteo y congela temporalmente todos los mandos periféricos del panel. Cuenta con una rutina de escape que permite la cancelación manual inmediata por parte del operario.

    ```python
    def vent_chamber(win):
        """ Controla el inicio y la cancelación manual del proceso de venteo. """
        btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum

        if btn_vent.text() == "Vent Chamber":
            # Verifica que NINGUNA de las dos válvulas de vacío esté abierta
            if btn_soft.text() == "Soft Vacuum Off" or btn_main.text() == "Main Vacuum Off": 
                QtWidgets.QMessageBox.warning(
                    win,
                    "Secuencia Inválida",
                    "No se puede ventear la cámara si alguna válvula de vacío (Soft o Main) está abierta.\n"
                    "Cierre las válvulas de vacío primero.",
                    QtWidgets.QMessageBox.Ok
                )
                return

            # Inicio de venteo
            win.hw.digital_set("VENT_VALVE_CONTROL", ACTIVE)
            btn_vent.setText("Venteando...")
            btn_vent.setStyleSheet("background-color: #2ec4b6; color: black; font-weight: bold;")
            
            # Bloqueos de seguridad durante el venteo
            btn_soft.setEnabled(False)
            btn_main.setEnabled(False)
            win.ui.MenuPrincipal_btn_open_door.setEnabled(False)
            set_mfc_controls_enabled(win, False)
            
        else:
            # Cancelación manual
            win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
            btn_vent.setText("Vent Chamber")
            btn_vent.setStyleSheet("")
            
            btn_soft.setEnabled(True)
            btn_main.setEnabled(True)
            win.ui.MenuPrincipal_btn_open_door.setEnabled(True)
    ```

??? note "Finalizacion del venteo: `finish_vent_sequence(win)`"
    Subrutina de callback asíncrona disparada automáticamente por el gestor de tiempos una vez transcurrido el retardo de estabilización post-detección de presión atmosférica (ATM). Valida que la secuencia no haya sido abortada previamente, desenergiza la electroválvula de venteo y devuelve los controles periféricos y mecánicos a su estado de libre operación segura.

    ```python
    def finish_vent_sequence(win):
        """Cierra la válvula de venteo de forma segura y habilita la apertura de puerta al finalizar."""
        btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
        
        if btn_vent.text() != "Presión ATM alcanzada...":
            return

        win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
        btn_vent.setText("Vent Chamber")
        btn_vent.setStyleSheet("")
        
        win.ui.MenuPrincipal_btn_soft_vacuum.setEnabled(True)
        win.ui.MenuPrincipal_btn_main_vacuum.setEnabled(True)
        win.ui.MenuPrincipal_btn_open_door.setEnabled(True)
    ```

??? note "Apertura/Cierre de válvula shutoff de MFC1 (O2): `toggle_mfc1_valve(win)`"
    Controla la señal digital de corte para la línea de Oxígeno (`MFC1_OPEN`). Al cerrar la válvula de corte, resetea por seguridad la tensión del setpoint analógico a 0.0 V para evitar acumulación de presión en la línea.

    ```python
    def toggle_mfc1_valve(win):
        """ Habilita / Deshabilita la válvula de corte de O2 (MFC1) """
        btn = win.ui.MenuPrincipal_btn_mfc1_open
        if btn.text() == "Abrir Valvula MFC1: O2":
            win.hw.digital_set("MFC1_OPEN", ACTIVE)
            btn.setText("Cerrar Valvula MFC1: O2")
            btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            win.hw.digital_set("MFC1_OPEN", INACTIVE)
            win.hw.analog_write("MFC1_SETPOINT", 0.0)
            btn.setText("Abrir Valvula MFC1: O2")
            btn.setStyleSheet("")
    ```

??? note "Apertura/Cierre de válvula shutoff de MFC2 (N2): `toggle_mfc2_valve(win)`"
    Controla la señal digital de corte para la línea de Nitrógeno (`MFC2_OPEN`). Ante una acción de cierre de la válvula, fuerza de manera preventiva el setpoint analógico a 0.0 V.

    ```python
    def toggle_mfc2_valve(win):
        """ Habilita / Deshabilita la válvula de corte de N2 (MFC2) """
        btn = win.ui.MenuPrincipal_btn_mfc2_open
        if btn.text() == "Abrir Valvula MFC2: N2":
            win.hw.digital_set("MFC2_OPEN", ACTIVE)
            btn.setText("Cerrar Valvula MFC2: N2")
            btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            win.hw.digital_set("MFC2_OPEN", INACTIVE)
            win.hw.analog_write("MFC2_SETPOINT", 0.0)
            btn.setText("Abrir Valvula MFC2: N2")
            btn.setStyleSheet("")
    ```

??? note "Ajuste de setpoint de MFC1 (O2): `set_mfc1_flow(win)`"
    Lee el campo de texto (`QLineEdit`) con el setpoint seteado, reemplazando comas por puntos, y valida numéricamente que el setpoint ingresada en SLM esté dentro del rango seguro. Escala proporcionalmente el caudal a su correspondiente tensión analógica de salida de la DAQ (`MFC1_SETPOINT`) y notifica cualquier inconsistencia o fuera de rango mediante un `QMessageBox`.

    ```python
    def set_mfc1_flow(win):
        """ Lee el QLineEdit, valida el valor e ingresa la tensión a la DAQ para O2 """
        text_val = win.ui.MenuPrincipal_mfc1_setpoint.text().replace(',', '.')
        btn_set = win.ui.MenuPrincipal_btn_mfc1_set
        try:
            slm_target = float(text_val)
            if 0.0 <= slm_target <= MFC1_MAX_SLM:
                voltage = (slm_target / MFC1_MAX_SLM) * MFC1_MAX_VOLT
                win.hw.analog_write("MFC1_SETPOINT", voltage)
                print(f"[MFC1 O2] Setpoint cargado: {slm_target:.2f} SLM ({voltage:.2f} V)")
                btn_set.setStyleSheet("background-color: #4CAF50; color: white;")
            else:
                btn_set.setStyleSheet("background-color: #f44336; color: white;")
                QtWidgets.QMessageBox.warning(
                    win, "Rango Inválido",
                    f"El caudal de O2 debe estar entre 0.0 y {MFC1_MAX_SLM} SLM."
                )
        except ValueError:
            btn_set.setStyleSheet("background-color: #f44336; color: white;")
            QtWidgets.QMessageBox.warning(
                win, "Entrada Inválida",
                "Por favor ingrese un número válido para el setpoint de O2."
            )
    ```

??? note "Ajuste de setpoint MFC2 (N2): `set_mfc2_flow(win)`"
    Lee el campo de texto (`QLineEdit`) con el setpoint seteado, reemplazando comas por puntos, y valida numéricamente que el setpoint ingresada en SLM esté dentro del rango seguro. Escala proporcionalmente el caudal a su correspondiente tensión analógica de salida de la DAQ (`MFC2_SETPOINT`) y notifica cualquier inconsistencia o fuera de rango mediante un `QMessageBox`.

    ```python
    def set_mfc2_flow(win):
        """ Lee el QLineEdit, valida el valor e ingresa la tensión a la DAQ para N2 """
        text_val = win.ui.MenuPrincipal_mfc2_setpoint.text().replace(',', '.')
        btn_set = win.ui.MenuPrincipal_btn_mfc2_set
        try:
            slm_target = float(text_val)
            if 0.0 <= slm_target <= MFC2_MAX_SLM:
                voltage = (slm_target / MFC2_MAX_SLM) * MFC2_MAX_VOLT
                win.hw.analog_write("MFC2_SETPOINT", voltage)
                print(f"[MFC2 N2] Setpoint cargado: {slm_target:.2f} SLM ({voltage:.2f} V)")
                btn_set.setStyleSheet("background-color: #4CAF50; color: white;")
            else:
                btn_set.setStyleSheet("background-color: #f44336; color: white;")
                QtWidgets.QMessageBox.warning(
                    win, "Rango Inválido",
                    f"El caudal de N2 debe estar entre 0.0 y {MFC2_MAX_SLM} SLM."
                )
        except ValueError:
            btn_set.setStyleSheet("background-color: #f44336; color: white;")
            QtWidgets.QMessageBox.warning(
                win, "Entrada Inválida",
                "Por favor ingrese un número válido para el setpoint de N2."
            )
    ```

??? note "Encendido de lamparas 1 y 3: `trigger_lamps_1_3(win)`"
    Envía un pulso de una duracion dada por el parametro pasado a qt_sleep a las lámparas 1 y 3 y las apaga. Si el pulso dura mas de 28s, la placa de los monoestables previa a las lamparas por donde pasan estas señales hace que las lamparas se apaguen cortando el pulso

    ```python
    def trigger_lamps_1_3(win):
        try:
            # 1. Pulso de activación (ACTIVE)
            win.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
            win.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
            
            # 2. Mantener el pulso unos milisegundos para asegurar el trigger
            qt_sleep(20000)

            # 3. Retorno al estado de reposo (INACTIVE)
            win.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
            win.hw.digital_set("LAMP3_ON_CMD", INACTIVE)

            print("[INFO] Pulso enviado a Lámparas 1 y 3 (Monoestable disparado).")

        except Exception as e:
            print(f"[ERROR] Fallo al enviar pulso a Lámparas 1 y 3: {e}")

    ```

??? note "Encendido de lampara 2: `toggle_lamp_2(win)`"
    Controla el encendido y apagado de la Lámpara 2 (Central) mediante un estado ON/OFF.

    ```python   
    def toggle_lamp_2(win):
        btn = win.ui.MenuPrincipal_btn_centralLamp  

        if btn.text() == "Lamp 2 On":
            win.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
            btn.setText("Lamp 2 Off")
            btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
            print("[INFO] Lámpara 2 (Central) Encendida.")
        else:
            win.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
            btn.setText("Lamp 2 On")
            btn.setStyleSheet("")
            print("[INFO] Lámpara 2 (Central) Apagada.")
    ```