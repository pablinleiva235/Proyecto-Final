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
    Administra la apertura y cierre del pistón neumático de la puerta de cámara de proceso.

    ```python
    def toggle_door(win):
        """Controla la apertura y el cierre seguro de la puerta de la cámara."""
        btn = win.ui.MenuPrincipal_btn_open_door
        
        if btn.text() == "Abrir Puerta":
            win.hw.digital_set("DOOR_CLOSE_CMD", INACTIVE)
            win.hw.digital_set("DOOR_OPEN_CMD", ACTIVE)
            btn.setText("Cerrar Puerta")
            btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            win.hw.digital_set("DOOR_OPEN_CMD", INACTIVE)
            win.hw.digital_set("DOOR_CLOSE_CMD", ACTIVE)
            btn.setText("Abrir Puerta")
            btn.setStyleSheet("")
    ```

??? note "Encendido/Apagado de valvula de Soft Vacuum: `toggle_soft_vacuum(win)`"
    Modula la válvula neumática encargada del vacío lento o inicial (`SOFT_START_CONTROL`). Al encenderse, bloquea de forma mandatoria la interfaz del operario para impedir la apertura física de la puerta bajo vacío. Al intentar apagarse, interroga el estado de la válvula principal, denegando la acción mediante un `QMessageBox` de advertencia si el vacío principal sigue activo.

    ```python
    def toggle_soft_vacuum(win):
        """Controla la válvula de soft vacuum y bloquea el apagado si hay vacío principal activo."""
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum
        btn_door = win.ui.MenuPrincipal_btn_open_door
        
        if btn_soft.text() == "Soft Vacuum On":
            win.hw.digital_set("SOFT_START_CONTROL", ACTIVE)
            btn_soft.setText("Soft Vacuum Off")
            btn_soft.setStyleSheet("background-color: #f44336; color: white;")
            btn_door.setEnabled(False)  # <-- BLOQUEO DE SEGURIDAD
        else:
            if btn_main.text() == "Main Vacuum Off":
                QtWidgets.QMessageBox.warning(
                    win, 
                    "Secuencia Inválida", 
                    "No se puede apagar Soft Vacuum mientras Main Vacuum esté encendido.\nApague primero el vacío principal.",
                    QtWidgets.QMessageBox.Ok
                )
                return
                
            win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
            btn_soft.setText("Soft Vacuum On")
            btn_soft.setStyleSheet("")
    ```

??? note "Encendido/Apagado de valvula de Soft Vacuum: `toggle_main_vacuum(win)`"
    Comanda la válvula de alto flujo de vacío (`MAIN_VACUUM_CONTROL`). Actúa bajo una restricción jerárquica de hardware simulada por software: si el sistema detecta que la etapa previa de Soft Vacuum está inactiva, interrumpe el flujo de ejecución previniendo turbulencias térmicas o daños mecánicos en la cámara. Al acoplarse, restringe el uso de la compuerta.

    ```python
    def toggle_main_vacuum(win):
        """Controla la válvula de vacío principal, permitiendo la acción SOLO si Soft Vacuum está activo."""
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_door = win.ui.MenuPrincipal_btn_open_door
        
        if btn_soft.text() == "Soft Vacuum On":
            QtWidgets.QMessageBox.warning(
                win, 
                "Secuencia Inválida", 
                "No se puede activar Main Vacuum si Soft Vacuum no está encendido primero.",
                QtWidgets.QMessageBox.Ok
            )
            return

        if btn_main.text() == "Main Vacuum On":
            win.hw.digital_set("MAIN_VACUUM_CONTROL", ACTIVE)
            btn_main.setText("Main Vacuum Off")
            btn_main.setStyleSheet("background-color: #f44336; color: white;")
            btn_door.setEnabled(False)  # <-- BLOQUEO DE SEGURIDAD
        else:
            win.hw.digital_set("MAIN_VACUUM_CONTROL", INACTIVE)
            btn_main.setText("Main Vacuum On")
            btn_main.setStyleSheet("")
    ```

??? note "Venteo de camara: `vent_chamber(win)`"
    Maneja la apertura física de la línea de nitrógeno/aire hacia el interior de la cámara (`VENT_VALVE_CONTROL`). Evalúa rigurosamente que no existan líneas de vacío succionando en simultáneo. Si pasa los filtros, inicia el venteo y congela temporalmente todos los mandos periféricos del panel. Cuenta con una rutina de escape que permite la cancelación manual inmediata por parte del operario.

    ```python
    def vent_chamber(win):
        """Controla el inicio y la cancelación manual del proceso de venteo de la cámara."""
        btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
        btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
        btn_main = win.ui.MenuPrincipal_btn_main_vacuum

        if btn_vent.text() == "Vent Chamber":
            if btn_soft.text() == "Soft Vacuum Off" or btn_main.text() == "Main Vacuum Off": 
                QtWidgets.QMessageBox.warning(win, "Secuencia Inválida", "...", QtWidgets.QMessageBox.Ok)
                return

            win.hw.digital_set("VENT_VALVE_CONTROL", ACTIVE)
            btn_vent.setText("Venteando...")
            btn_vent.setStyleSheet("background-color: #2ec4b6; color: black; font-weight: bold;")
            
            btn_soft.setEnabled(False)
            btn_main.setEnabled(False)
            win.ui.MenuPrincipal_btn_open_door.setEnabled(False)
        else:
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