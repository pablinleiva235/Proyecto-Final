"""
Configuración visual global de la aplicación.

Este archivo centraliza todos los colores y estilos utilizados por la GUI.
El objetivo es evitar valores hardcodeados y facilitar futuros cambios de
apariencia o la incorporación de distintos temas visuales.
"""

# =============================================================================
# Paleta de colores
# =============================================================================

# Colores principales
BACKGROUND_COLOR = "#1E1E1E"
SURFACE_COLOR = "#2B2B2B"
SURFACE_HOVER_COLOR = "#3A3A3A"

PRIMARY_COLOR = "#0094FF"
DANGER_COLOR = "#D32F2F"

# Barra superior
TOP_BAR_COLOR = "#111111"

# Login
INPUT_BACKGROUND_COLOR = "#252525"

# Texto
TEXT_COLOR = "#EEEEEE"
TEXT_MUTED_COLOR = "#AAAAAA"

# Indicadores LED 
LED_ON_COLOR = "#00C853"
LED_OFF_COLOR = "#D32F2F"

# =============================================================================
# Hoja de estilos global (QSS)
# =============================================================================

APP_STYLE = f"""
/* -------------------------------------------------------------------------- */
/* Ventana principal                                                          */
/* -------------------------------------------------------------------------- */

QMainWindow {{
    background-color: {BACKGROUND_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Widgets generales                                                          */
/* -------------------------------------------------------------------------- */

QWidget {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    font-family: "Segoe UI";
    font-size: 18px;
}}

/* -------------------------------------------------------------------------- */
/* Títulos                                                                    */
/* -------------------------------------------------------------------------- */

QLabel#TitleLabel {{
    font-size: 42px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}

QLabel#SubtitleLabel {{
    font-size: 22px;
    color: {TEXT_MUTED_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Barra superior                                                             */
/* -------------------------------------------------------------------------- */

QWidget#TopBar {{
    background-color: {TOP_BAR_COLOR};
    border-bottom: 2px solid {PRIMARY_COLOR};
}}

QLabel#TopBarTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 22px;
    font-weight: bold;
}}

/* -------------------------------------------------------------------------- */
/* Botones                                                                    */
/* -------------------------------------------------------------------------- */

QPushButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {PRIMARY_COLOR};
    border-radius: 12px;
    padding: 18px;
    font-size: 22px;
}}

QPushButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
}}

QPushButton:pressed {{
    background-color: {PRIMARY_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Botón Exit                                                                 */
/* -------------------------------------------------------------------------- */

QPushButton#ExitButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {DANGER_COLOR};
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 16px;
}}

QPushButton#ExitButton:hover {{
    background-color: {DANGER_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Login Dialog                                                               */
/* -------------------------------------------------------------------------- */

QDialog {{
    background-color: {BACKGROUND_COLOR};
}}

QLabel#LoginTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 28px;
    font-weight: bold;
}}

QLineEdit#LoginInput {{
    background-color: {INPUT_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {SURFACE_HOVER_COLOR};
    border-radius: 8px;
    padding: 10px;
    font-size: 18px;
}}

QLineEdit#LoginInput:focus {{
    border: 2px solid {PRIMARY_COLOR};
}}

QLabel#LoginErrorLabel {{
    background-color: transparent;
    color: {DANGER_COLOR};
    font-size: 16px;
    font-weight: bold;
}}

QPushButton#LoginButton {{
    padding: 10px 24px;
    font-size: 18px;
}}

QPushButton#CancelButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {TEXT_MUTED_COLOR};
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 18px;
}}

QPushButton#CancelButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
}}
"""