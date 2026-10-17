"""Selección y clasificación de señales mostradas en Mantenimiento."""

# =============================================================================
# Señales visibles en modo mantenimiento
# =============================================================================

from config.digital_signals import DIGITALSIGNALS

# Mostrar y monitorear todas las señales declaradas en la configuración
# técnica, conservando su orden.
MAINTAINER_SIGNALS = tuple(DIGITALSIGNALS)

MAINTAINER_INPUT_SIGNALS = tuple(
    name for name, config in DIGITALSIGNALS.items()
    if config["dir"] == "IN"
)

MAINTAINER_OUTPUT_SIGNALS = tuple(
    name for name, config in DIGITALSIGNALS.items()
    if config["dir"] == "OUT"
)

# Estas salidas se operan mediante sus secuencias o controladores dedicados.
# Sus tarjetas muestran el estado confirmado, pero no escriben el pin en
# forma directa para evitar saltear interlocks o generar pulsos incorrectos.
SEQUENCE_CONTROLLED_OUTPUT_SIGNALS = frozenset({
    "FILAMENT_ENABLE",
    "SOFT_START_CONTROL",
    "MAIN_VACUUM_CONTROL",
    "VENT_VALVE_CONTROL",
    "ALARM_INDICATION",
    "MFC1_OPEN",
    "MFC2_OPEN",
    "DOOR_OPEN_CMD",
    "DOOR_CLOSE_CMD",
    "RF_ON_CMD",
    "LAMP1_ON_CMD",
    "LAMP2_ON_CMD",
    "LAMP3_ON_CMD",
    "STEPPER_STEP",
    "STEPPER_DIR",
    "STEPPER_HALF_STEP",
    "STEPPER_OUTPUT_ENABLE",
})

MANUALLY_TOGGLABLE_OUTPUT_SIGNALS = tuple(
    name for name in MAINTAINER_OUTPUT_SIGNALS
    if name not in SEQUENCE_CONTROLLED_OUTPUT_SIGNALS
)
