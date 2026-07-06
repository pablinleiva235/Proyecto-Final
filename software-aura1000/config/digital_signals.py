from drivers import dio_driver as dio

ACTIVE = True
INACTIVE = False

DIGITALSIGNALS = {

# --------- SEÑALES SECONDPORTA: P1-1 a P1-8 / SALIDAS -------------
    "PURGE_VALVE_CONTROL":        {"port": dio.SECONDPORTA, "bit": 7, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "VENT_VALVE_CONTROL":         {"port": dio.SECONDPORTA, "bit": 6, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "MAIN_VACUUM_CONTROL":        {"port": dio.SECONDPORTA, "bit": 5, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "ALARM_INDICATION":           {"port": dio.SECONDPORTA, "bit": 4, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "MFC4_OPEN":                  {"port": dio.SECONDPORTA, "bit": 3, "dir": "OUT", "active_state": 0, "initial_state": 1},
    "MFC3_OPEN":                  {"port": dio.SECONDPORTA, "bit": 2, "dir": "OUT", "active_state": 0, "initial_state": 1},
    "MFC2_OPEN":                  {"port": dio.SECONDPORTA, "bit": 1, "dir": "OUT", "active_state": 0, "initial_state": 1},
    "MFC1_OPEN":                  {"port": dio.SECONDPORTA, "bit": 0, "dir": "OUT", "active_state": 0, "initial_state": 1},

    # --------- SEÑALES SECONDPORTB: P1-9 a P1-16 / SALIDAS ------------
    "MAIN_PNEUMATIC_ENABLE":      {"port": dio.SECONDPORTB, "bit": 7, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "SOFT_START_CONTROL":         {"port": dio.SECONDPORTB, "bit": 6, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "FILAMENT_ENABLE":            {"port": dio.SECONDPORTB, "bit": 5, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "LOAD_VACUUM_CONTROL":        {"port": dio.SECONDPORTB, "bit": 4, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "UNLOAD_VACUUM_CONTROL":      {"port": dio.SECONDPORTB, "bit": 3, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "LOAD_ASSY_UP_CONTROL":       {"port": dio.SECONDPORTB, "bit": 2, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "UNLOAD_ASSY_UP_CONTROL":     {"port": dio.SECONDPORTB, "bit": 1, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "LOAD_CHUCK_UP_ASSY_CONTROL": {"port": dio.SECONDPORTB, "bit": 0, "dir": "OUT", "active_state": 1, "initial_state": 0},

    # --------- SEÑALES SECONDPORTC: P1-17 a P1-24 NO CONECTADAS -------
    "P1_17":                      {"port": dio.SECONDPORTCH, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_18":                      {"port": dio.SECONDPORTCH, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_19":                      {"port": dio.SECONDPORTCH, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_20":                      {"port": dio.SECONDPORTCH, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_21":                      {"port": dio.SECONDPORTCL, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_22":                      {"port": dio.SECONDPORTCL, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_23":                      {"port": dio.SECONDPORTCL, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_24":                      {"port": dio.SECONDPORTCL, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1},

    # --------- SEÑALES FIRSTPORTA: P1-25 a P1-32 / ENTRADAS ----------
    "LOAD_ASSY_UP_SENSE":         {"port": dio.FIRSTPORTA, "bit": 7, "dir": "IN", "active_state": 0, "initial_state": 1},
    "LOAD_ASSY_DOWN_SENSE":       {"port": dio.FIRSTPORTA, "bit": 6, "dir": "IN", "active_state": 0, "initial_state": 0},
    "UNLOAD_ASSY_UP_SENSE":       {"port": dio.FIRSTPORTA, "bit": 5, "dir": "IN", "active_state": 0, "initial_state": 1},
    "UNLOAD_ASSY_DOWN_SENSE":     {"port": dio.FIRSTPORTA, "bit": 4, "dir": "IN", "active_state": 0, "initial_state": 0},
    "LOAD_VACUUM_SENSE":          {"port": dio.FIRSTPORTA, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1},
    "UNLOAD_VACUUM_SENSE":        {"port": dio.FIRSTPORTA, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1},
    "AUX_START":                  {"port": dio.FIRSTPORTA, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1},
    "AUX_STOP":                   {"port": dio.FIRSTPORTA, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1},

    # --------- SEÑALES FIRSTPORTB: P1-33 a P1-40 / ENTRADAS ----------
    "P1_33":                      {"port": dio.FIRSTPORTB, "bit": 7, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no relevada
    "LAMP3_FAIL":                 {"port": dio.FIRSTPORTB, "bit": 6, "dir": "IN", "active_state": 1, "initial_state": 1},
    "LAMP2_FAIL":                 {"port": dio.FIRSTPORTB, "bit": 5, "dir": "IN", "active_state": 1, "initial_state": 1},
    "LAMP1_FAIL":                 {"port": dio.FIRSTPORTB, "bit": 4, "dir": "IN", "active_state": 1, "initial_state": 1},
    "PLASMA_FAIL":                {"port": dio.FIRSTPORTB, "bit": 3, "dir": "IN", "active_state": 1, "initial_state": 1},
    "P1_38":                      {"port": dio.FIRSTPORTB, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no relevada
    "P1_39":                      {"port": dio.FIRSTPORTB, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada
    "POWER_ON_SWITCH":            {"port": dio.FIRSTPORTB, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1},

    # --------- SEÑALES FIRSTPORTC: P1-41 a P1-47 NO CONECTADAS -------
    "P1_41":                      {"port": dio.FIRSTPORTCH, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_42":                      {"port": dio.FIRSTPORTCH, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1},
    "SYS_POWER":                  {"port": dio.FIRSTPORTCH, "bit": 1, "dir": "IN", "active_state": 1, "initial_state": 1},
    "P1_44":                      {"port": dio.FIRSTPORTCH, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1},
    "P1_45":                      {"port": dio.FIRSTPORTCL, "bit": 3, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "P1_46":                      {"port": dio.FIRSTPORTCL, "bit": 2, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "P1_47":                      {"port": dio.FIRSTPORTCL, "bit": 1, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "POWER_ON":                   {"port": dio.FIRSTPORTCL, "bit": 0, "dir": "OUT", "active_state": 0, "initial_state": 1},

    # --------- SEÑALES FOURTHPORTA: P2-51 a P2-58 / SALIDAS ----------
    "DOOR_OPEN_CMD":              {"port": dio.FOURTHPORTA, "bit": 7, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "DOOR_CLOSE_CMD":             {"port": dio.FOURTHPORTA, "bit": 6, "dir": "OUT", "active_state": 1, "initial_state": 1},
    "LOAD_ARM_OUT_CMD":           {"port": dio.FOURTHPORTA, "bit": 5, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "LOAD_ARM_HOME_CMD":          {"port": dio.FOURTHPORTA, "bit": 4, "dir": "OUT", "active_state": 1, "initial_state": 1},
    "RF_ON_CMD":                  {"port": dio.FOURTHPORTA, "bit": 3, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "P2_56":                      {"port": dio.FOURTHPORTA, "bit": 2, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Señal no conectada
    "P2_57":                      {"port": dio.FOURTHPORTA, "bit": 1, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Señal no conectada
    "P2_58":                      {"port": dio.FOURTHPORTA, "bit": 0, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Señal no conectada

    # --------- SEÑALES FOURTHPORTB: P2-59 a P1-66 / SALIDAS ----------
    "UNLOAD_ARM_OUT_CMD":         {"port": dio.FOURTHPORTB, "bit": 7, "dir": "OUT", "active_state": 1, "initial_state": 0}, 
    "UNLOAD_ARM_HOME_CMD":        {"port": dio.FOURTHPORTB, "bit": 6, "dir": "OUT", "active_state": 1, "initial_state": 1},
    "SEND_CMD":                   {"port": dio.FOURTHPORTB, "bit": 5, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "RECEIVE_CMD":                {"port": dio.FOURTHPORTB, "bit": 4, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "LAMP1_ON_CMD":               {"port": dio.FOURTHPORTB, "bit": 3, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "LAMP2_ON_CMD":               {"port": dio.FOURTHPORTB, "bit": 2, "dir": "OUT", "active_state": 1, "initial_state": 0}, 
    "LAMP3_ON_CMD":               {"port": dio.FOURTHPORTB, "bit": 1, "dir": "OUT", "active_state": 1, "initial_state": 0}, 
    "RECEIVE_RESET":              {"port": dio.FOURTHPORTB, "bit": 0, "dir": "OUT", "active_state": 1, "initial_state": 0},

    # --------- SEÑALES FOURTHPORTC: P2-67 a P2-74 / SALIDAS -------
    "DRIVER_ENABLE":              {"port": dio.FOURTHPORTCH, "bit": 3, "dir": "OUT", "active_state": 1, "initial_state": 0},
    "P2_68":                      {"port": dio.FOURTHPORTCH, "bit": 2, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Señal no conectada
    "P2_69":                      {"port": dio.FOURTHPORTCH, "bit": 1, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Señal no conectada
    "P2_70":                      {"port": dio.FOURTHPORTCH, "bit": 0, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Señal no conectada
    "P2_71":                      {"port": dio.FOURTHPORTCL, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada
    "P2_72":                      {"port": dio.FOURTHPORTCL, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada
    "P2_73":                      {"port": dio.FOURTHPORTCL, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada
    "P2_74":                      {"port": dio.FOURTHPORTCL, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada

    # --------- SEÑALES THIRDPORTA: P2-75 a P2-82 / ENTRADAS ----------
    "SEND_CASS_SENSE":            {"port": dio.THIRDPORTA, "bit": 7, "dir": "IN", "active_state": 0, "initial_state": 0},
    "RECEIVE_CASS_SENSE":         {"port": dio.THIRDPORTA, "bit": 6, "dir": "IN", "active_state": 0, "initial_state": 0},
    "RECEIVE_CASS_READY":         {"port": dio.THIRDPORTA, "bit": 5, "dir": "IN", "active_state": 1, "initial_state": 1},
    "ATM_SWITCH":                 {"port": dio.THIRDPORTA, "bit": 4, "dir": "IN", "active_state": 0, "initial_state": 0},
    "WAFER_SENT_SENSE":           {"port": dio.THIRDPORTA, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1},
    "WAFER_RECEIVED_SENSE":       {"port": dio.THIRDPORTA, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1}, 
    "MAGNETRON_WARNING":          {"port": dio.THIRDPORTA, "bit": 1, "dir": "IN", "active_state": 1, "initial_state": 0}, 
    "MAGNETRON_OVERHEAT":         {"port": dio.THIRDPORTA, "bit": 0, "dir": "IN", "active_state": 1, "initial_state": 0}, 

    # --------- SEÑALES THIRDPORTB: P2-83 a P2-90 / ENTRADAS ----------
    "DOOR_OPEN":                  {"port": dio.THIRDPORTB, "bit": 7, "dir": "IN", "active_state": 0, "initial_state": 1},
    "DOOR_CLOSE":                 {"port": dio.THIRDPORTB, "bit": 6, "dir": "IN", "active_state": 0, "initial_state": 0},
    "LOAD_ARM_OUT":               {"port": dio.THIRDPORTB, "bit": 5, "dir": "IN", "active_state": 0, "initial_state": 1},
    "LOAD_ARM_HOME":              {"port": dio.THIRDPORTB, "bit": 4, "dir": "IN", "active_state": 0, "initial_state": 0},
    "UNLOAD_ARM_OUT":             {"port": dio.THIRDPORTB, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1},
    "UNLOAD_ARM_HOME":            {"port": dio.THIRDPORTB, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 0}, 
    "COVER_DOWN":                 {"port": dio.THIRDPORTB, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1}, 
    "AIR_FLOW":                   {"port": dio.THIRDPORTB, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 1}, 

    # --------- SEÑALES THIRDPORTC: P2-91 a P2-98 / SEÑALES THROTTLE -- 
    "P2_91":                      {"port": dio.THIRDPORTCH, "bit": 3, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada
    "P2_92":                      {"port": dio.THIRDPORTCH, "bit": 2, "dir": "IN", "active_state": 0, "initial_state": 1}, # Señal no conectada
    "THROTTLE_CLOSED":            {"port": dio.THIRDPORTCH, "bit": 1, "dir": "IN", "active_state": 0, "initial_state": 1}, # Entrada
    "THROTTLE_OPEN":              {"port": dio.THIRDPORTCH, "bit": 0, "dir": "IN", "active_state": 0, "initial_state": 0}, # Entrada
    "STEPPER_STEP":               {"port": dio.THIRDPORTCL, "bit": 3, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Salida
    "STEPPER_DIR":                {"port": dio.THIRDPORTCL, "bit": 2, "dir": "OUT", "active_state": 1, "initial_state": 1}, # Salida
    "STEPPER_HALF_STEP":          {"port": dio.THIRDPORTCL, "bit": 1, "dir": "OUT", "active_state": 1, "initial_state": 0}, # Salida
    "STEPPER_OUTPUT_ENABLE":      {"port": dio.THIRDPORTCL, "bit": 0, "dir": "OUT", "active_state": 0, "initial_state": 1}, # Salida
}