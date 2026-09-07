"""
Selección de señales visibles en la pantalla de mantenimiento.

La definición técnica de cada señal continúa perteneciendo a
config/digital_signals.py.

Este archivo únicamente determina qué señales digitales deben mostrarse en
MaintainerScreen y en qué orden deben aparecer.
"""

# =============================================================================
# Señales visibles en modo mantenimiento
# =============================================================================

MAINTAINER_SIGNALS = (
    "POWER_ON",
    "POWER_ON_SWITCH",
    "SYS_POWER",
    "DRIVER_ENABLE",
    "P1_38",
)

MAINTAINER_OUTPUT_SIGNALS = (
    "POWER_ON",
    "DRIVER_ENABLE",
)