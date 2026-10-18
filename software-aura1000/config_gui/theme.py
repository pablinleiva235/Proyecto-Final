"""
Configuración visual global de la aplicación.

Este archivo centraliza todos los colores y estilos utilizados por la GUI.
El objetivo es evitar valores hardcodeados y facilitar futuros cambios de
apariencia o la incorporación de distintos temas visuales.
"""

# =============================================================================
# Paleta de colores
# =============================================================================

# Paletas compartidas por todos los componentes de la interfaz.
THEMES = {
    "dark": {
        "background": "#121358",
        "surface": "#232F72",
        "surface_secondary": "#2F578A",
        "primary": "#36ADA3",
        "text": "#FAFAFA",
        "text_secondary": "#D8E5F0",
        "border": "#7196B8",
        "on": "#4ADE80",
        "running": "#38BDF8",
        "warning": "#FACC15",
        "fault": "#FB7185",
        "off": "#94A3B8",
    },
    "light": {
        "background": "#F2EFE7",
        "surface": "#C8DFDB",
        "surface_secondary": "#66A3BF",
        "primary": "#3368A0",
        "text": "#121358",
        "text_secondary": "#315779",
        "border": "#67848E",
        "on": "#166534",
        "running": "#075985",
        "warning": "#92400E",
        "fault": "#B91C1C",
        "off": "#64748B",
    },
}

_DEFAULT_COLORS = THEMES["dark"]
BACKGROUND_COLOR = _DEFAULT_COLORS["background"]
SURFACE_COLOR = _DEFAULT_COLORS["surface"]
SURFACE_SECONDARY_COLOR = _DEFAULT_COLORS["surface_secondary"]
SURFACE_HOVER_COLOR = SURFACE_SECONDARY_COLOR
SURFACE_DISABLED_COLOR = _DEFAULT_COLORS["off"]
TEXTBOX_BACKGROUND_COLOR = SURFACE_COLOR
PRIMARY_COLOR = _DEFAULT_COLORS["primary"]
BORDER_COLOR = _DEFAULT_COLORS["border"]
DANGER_COLOR = _DEFAULT_COLORS["fault"]
TOP_BAR_COLOR = _DEFAULT_COLORS["background"]
TEXT_COLOR = _DEFAULT_COLORS["text"]
TEXT_MUTED_COLOR = _DEFAULT_COLORS["text_secondary"]

# =============================================================================
# Configuración de Textos
# =============================================================================
FONT_FAMILY = "Segoe UI"
BUTTON_FONT_SIZE = 18
TITLE_FONT_SIZE = 64 
SUBTITLE_FONT_SIZE = 24
TEXT_FONT_SIZE = 16

# =============================================================================
# Configuración de Botones
# =============================================================================
BORDER_W = 2
BORDER_RADIUS = 12

# ============================================================
# SignalWidget
# ============================================================
SIGNAL_ACTIVE_COLOR = _DEFAULT_COLORS["on"]
SIGNAL_INACTIVE_COLOR = _DEFAULT_COLORS["off"]
SIGNAL_PROCESSING_COLOR = _DEFAULT_COLORS["running"]
SIGNAL_WARNING_COLOR = _DEFAULT_COLORS["warning"]
SIGNAL_FAULT_COLOR = _DEFAULT_COLORS["fault"]
# Tinta para el glifo dentro de los círculos de estado, elegida para conservar
# contraste con los colores de estado de cada paleta.
_STATUS_ICON_FOREGROUND = {
    "dark": THEMES["dark"]["background"],
    "light": "#FFFFFF",
}

SIGNAL_WIDGET_BORDER_RADIUS = 10
SIGNAL_LED_SIZE = 18
SIGNAL_LED_BORDER_RADIUS = SIGNAL_LED_SIZE // 2

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
    font-family: {FONT_FAMILY};
    font-size: {SUBTITLE_FONT_SIZE}px;
}}

/* -------------------------------------------------------------------------- */
/* Títulos                                                                    */
/* -------------------------------------------------------------------------- */

QLabel#TitleLabel {{
    font-size: {TITLE_FONT_SIZE}px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}

QLabel#SubtitleLabel {{
    font-size: {SUBTITLE_FONT_SIZE}px;
    color: {TEXT_MUTED_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Barra superior                                                             */
/* -------------------------------------------------------------------------- */

QWidget#TopBar {{
    background-color: {TOP_BAR_COLOR};
    border-bottom: {BORDER_W}px solid {PRIMARY_COLOR};
}}

QLabel#TopBarTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: {SUBTITLE_FONT_SIZE}px;
    font-weight: bold;
}}

QLabel#TopBarDate {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: 500;
}}

QLabel#TopBarTime {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: bold;
    min-width: 80px;
}}

QFrame#OperationCard {{
    background-color: {SURFACE_COLOR};
    border: 2px solid {BORDER_COLOR};
    border-radius: 12px;
}}

QFrame#OperationCard QLabel {{
    background-color: transparent;
    font-size: 14px;
}}

QFrame#OperationStatusCard {{
    background-color: {SURFACE_COLOR};
    border: 2px solid {BORDER_COLOR};
    border-radius: 10px;
}}

QLabel#OperationStatusTitle {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 13px;
    font-weight: 600;
}}

QFrame#OperationStatusCard QLabel#DemoStatusGood {{
    font-size: 14px;
}}

QLabel#NormalOperationTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 32px;
    font-weight: bold;
}}

QLabel#OperationCardTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 17px;
    font-weight: bold;
}}

QLabel#SimulationBadge {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {SIGNAL_PROCESSING_COLOR};
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 16px;
    font-weight: bold;
}}

QLabel#SimulationDescription {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 14px;
}}

QLabel#DemoValue {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 26px;
    font-weight: bold;
}}

QLabel#DemoValueSmall {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#SetpointLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#SetpointUnit {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 13px;
}}

QLabel#SetpointFeedback {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 12px;
}}

QLabel#SetpointFeedback[valid="true"] {{
    color: {SIGNAL_ACTIVE_COLOR};
}}

QLabel#SetpointFeedback[valid="false"] {{
    color: {DANGER_COLOR};
}}

QLineEdit[objectName^="SetpointInput_"] {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px;
    font-size: 16px;
}}

QLineEdit[objectName^="SetpointInput_"]:focus {{
    border-color: {PRIMARY_COLOR};
}}

QLabel#DigitalStatusLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 13px;
}}

QLabel#DigitalStatusValue {{
    background-color: {SURFACE_COLOR};
    color: {SIGNAL_ACTIVE_COLOR};
    border: 1px solid {SIGNAL_ACTIVE_COLOR};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    font-weight: bold;
}}

QLabel#DemoStatus {{
    background-color: transparent;
    color: {SIGNAL_PROCESSING_COLOR};
    font-size: 14px;
    font-weight: bold;
}}

QLabel#DemoStatusGood {{
    background-color: transparent;
    color: {SIGNAL_ACTIVE_COLOR};
    font-size: 16px;
    font-weight: bold;
}}

QPushButton#DemoActionButton {{
    padding: 6px 12px;
    font-size: 14px;
}}

QPushButton#RecipeActionButton {{
    padding: 10px 20px;
    font-size: 16px;
    min-height: 42px;
}}

QPushButton#SetpointStepButton {{
    padding: 4px;
    font-size: 18px;
    font-weight: bold;
}}

QPushButton#BackButton {{
    padding: 10px 22px;
    font-size: 16px;
}}

/* -------------------------------------------------------------------------- */
/* Botón de configuración                                                     */
/* -------------------------------------------------------------------------- */

QPushButton#SettingsButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {PRIMARY_COLOR};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#SettingsButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
    color: {TEXT_COLOR};
    border-color: {BORDER_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Startup Screen                                                             */
/* -------------------------------------------------------------------------- */

QLabel#StartupTitleLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 42px;
    font-weight: bold;
}}

QLabel#StartupMessageLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 26px;
}}

QLabel#StartupErrorLabel {{
    background-color: transparent;
    color: {DANGER_COLOR};
    font-size: 20px;
    font-weight: bold;
}}

QProgressBar#StartupProgressBar {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {PRIMARY_COLOR};
    border-radius: 8px;
    text-align: center;
    min-height: 28px;
}}

QProgressBar#StartupProgressBar::chunk {{
    background-color: {PRIMARY_COLOR};
    border-radius: 6px;
}}

/* -------------------------------------------------------------------------- */
/* Botones                                                                    */
/* -------------------------------------------------------------------------- */

QPushButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {PRIMARY_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 18px;   
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
    color: {TEXT_COLOR};
    border-color: {BORDER_COLOR};
}}

QPushButton:pressed {{
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QPushButton:checked, QPushButton:checked:hover {{
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QPushButton:disabled {{
    background-color: {SURFACE_COLOR};
    border: {BORDER_W}px solid {BORDER_COLOR};
    color: {TEXT_MUTED_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Botón Exit                                                                 */
/* -------------------------------------------------------------------------- */

QPushButton#ExitButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {DANGER_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 8px 20px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#ExitButton:hover {{
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    border-color: {DANGER_COLOR};
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
    font-size: {SUBTITLE_FONT_SIZE}px;
    font-weight: bold;
}}

QLineEdit#LoginInput {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {BORDER_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 10px 24px;
    font-size: {TEXT_FONT_SIZE}px;
}}

QLineEdit#LoginInput:focus {{
    border: {BORDER_W}px solid {PRIMARY_COLOR};
}}

QLabel#LoginErrorLabel {{
    background-color: transparent;
    color: {DANGER_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: bold;
}}

QPushButton#LoginButton {{
    padding: 10px 24px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#CancelButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {TEXT_MUTED_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 10px 24px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#CancelButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
    color: {TEXT_COLOR};
}}

/* ========================================================================== */
/* MaintainerScreen - Tabs                                                    */
/* ========================================================================== */

QTabWidget#MaintainerTabs::pane {{
    background-color: {BACKGROUND_COLOR};
    border: 2px solid {BORDER_COLOR};
    border-radius: 8px;
    top: -1px;
}}

QTabWidget#MaintainerTabs QTabBar::tab {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};

    border: 2px solid {BORDER_COLOR};
    border-bottom: none;

    padding: 12px 28px;
    margin-right: 4px;

    min-width: 180px;

    font-size: 18px;
    font-weight: bold;
}}

QTabWidget#MaintainerTabs QTabBar::tab:selected {{
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};

    border-color: {PRIMARY_COLOR};
}}

QTabWidget#MaintainerTabs QTabBar::tab:!selected {{
    margin-top: 4px;
}}

QTabWidget#MaintainerTabs QTabBar::tab:hover {{
    background-color: {SURFACE_HOVER_COLOR};
    color: {TEXT_COLOR};
}}

QPushButton#MFCControlButton {{
    padding: 6px 12px;
    font-size: 15px;
}}

/* -------------------------------------------------------------------------- */
/*   SignalWidget                                                             */
/* -------------------------------------------------------------------------- */

QFrame#signalWidget {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 18px;
}}

QFrame#signalWidget[interactive="true"]:hover {{
    background-color: {SURFACE_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QFrame#signalWidget[visualState="processing"] {{
    border-color: {SIGNAL_PROCESSING_COLOR};
}}

QFrame#signalWidget[error="true"] {{
    border-color: {SIGNAL_FAULT_COLOR};
}}

QFrame#signalWidget[semanticState="warning"] {{
    border-color: {SIGNAL_WARNING_COLOR};
}}

QFrame#signalWidget[semanticState="fault"] {{
    border-color: {SIGNAL_FAULT_COLOR};
}}

QLabel#signalNameLabel {{
    color: {TEXT_COLOR};
    background-color: transparent;
    border: none;
    font-size: 17px;
    font-weight: 600;
}}

QLabel#signalStatusLabel {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};
    border-radius: 12px;
    padding: 5px 10px;
    border: none;
    font-size: 12px;
    font-weight: 600;
}}

QLabel#signalLedIndicator {{
    min-width: {SIGNAL_LED_SIZE}px;
    max-width: {SIGNAL_LED_SIZE}px;
    min-height: {SIGNAL_LED_SIZE}px;
    max-height: {SIGNAL_LED_SIZE}px;
    border-radius: {SIGNAL_LED_BORDER_RADIUS}px;
}}


/* ACTIVE */

QLabel#signalLedIndicator[visualState="active"] {{
    background-color: {SIGNAL_ACTIVE_COLOR};
    border: {BORDER_W}px solid {SIGNAL_ACTIVE_COLOR};
}}

QLabel#signalStatusLabel[visualState="active"] {{
    color: {SIGNAL_ACTIVE_COLOR};
    background-color: {SURFACE_COLOR};
}}


/* INACTIVE */

QLabel#signalLedIndicator[visualState="inactive"] {{
    background-color: {SIGNAL_INACTIVE_COLOR};
    border: {BORDER_W}px solid {SIGNAL_INACTIVE_COLOR};
}}

QLabel#signalStatusLabel[visualState="inactive"] {{
    color: {TEXT_MUTED_COLOR};
    background-color: {SURFACE_COLOR};
}}


/* PROCESSING */

QLabel#signalLedIndicator[visualState="processing"] {{
    background-color: {SIGNAL_PROCESSING_COLOR};
    border: {BORDER_W}px solid {SIGNAL_PROCESSING_COLOR};
}}

QLabel#signalStatusLabel[visualState="processing"] {{
    color: {SIGNAL_PROCESSING_COLOR};
    background-color: {SURFACE_COLOR};
}}

QLabel#signalStatusLabel[semanticState="warning"] {{
    color: {SIGNAL_WARNING_COLOR};
    background-color: {SURFACE_COLOR};
}}

QLabel#signalStatusLabel[semanticState="fault"] {{
    color: {SIGNAL_FAULT_COLOR};
    background-color: {SURFACE_COLOR};
}}

QWidget#StatusIndicator {{
    border-radius: 21px;
    border: 1px solid {BORDER_COLOR};
    background-color: {SIGNAL_INACTIVE_COLOR};
    color: __STATUS_ICON_FOREGROUND__;
}}

QWidget#StatusIndicator[state="on"] {{
    background-color: {SIGNAL_ACTIVE_COLOR};
    color: __STATUS_ICON_FOREGROUND__;
}}

QWidget#StatusIndicator[state="running"] {{
    background-color: {SIGNAL_PROCESSING_COLOR};
    color: __STATUS_ICON_FOREGROUND__;
}}

QWidget#StatusIndicator[state="warning"] {{
    background-color: {SIGNAL_WARNING_COLOR};
    color: __STATUS_ICON_FOREGROUND__;
}}

QWidget#StatusIndicator[state="fault"] {{
    background-color: {SIGNAL_FAULT_COLOR};
    color: __STATUS_ICON_FOREGROUND__;
}}

QLabel#signalKindIcon {{
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 18px;
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    font-size: 11px;
    font-weight: bold;
}}

QLabel#signalFooterLabel, QLabel#MaintenanceCardFooter {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 12px;
}}

QFrame#MaintenanceCard, QFrame#MFCControlCard {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 18px;
}}

QGroupBox#MaintainerCardGroup {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 18px;
    margin-top: 20px;
    padding: 18px 12px 12px 12px;
    color: {TEXT_COLOR};
    font-size: 16px;
    font-weight: bold;
}}

QGroupBox#MaintainerCardGroup::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: {TEXT_COLOR};
}}

QLabel#MaintenanceCardTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 17px;
    font-weight: bold;
}}

QLabel#MaintenanceCardIcon {{
    min-width: 42px;
    max-width: 42px;
    min-height: 42px;
    max-height: 42px;
    border-radius: 21px;
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    font-size: 13px;
    font-weight: bold;
}}

QLabel#MaintenanceCardValue {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 27px;
    font-weight: bold;
}}

QLabel#MaintenanceCardValue[error="true"] {{
    color: {SIGNAL_FAULT_COLOR};
}}

QLabel#MaintenanceCardUnit {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 13px;
}}

QLabel#MaintenancePill, QLabel#MaintenancePill[state="inactive"] {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};
    border: none;
    border-radius: 12px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: bold;
}}

QLabel#MaintenancePill[state="active"] {{
    background-color: {SURFACE_COLOR};
    color: {SIGNAL_ACTIVE_COLOR};
}}

QLabel#MaintenancePill[state="error"] {{
    background-color: {SURFACE_COLOR};
    color: {SIGNAL_FAULT_COLOR};
}}

QLabel#MaintenancePill[state="warning"] {{
    background-color: {SURFACE_COLOR};
    color: {SIGNAL_WARNING_COLOR};
}}

QLabel#MaintenancePill[state="info"] {{
    background-color: {SURFACE_COLOR};
    color: {SIGNAL_PROCESSING_COLOR};
}}

QProgressBar#MFCFlowProgress {{
    min-height: 8px;
    max-height: 8px;
    border: none;
    border-radius: 4px;
    background-color: {SURFACE_SECONDARY_COLOR};
}}

QProgressBar#MFCFlowProgress::chunk {{
    border-radius: 4px;
    background-color: {PRIMARY_COLOR};
}}

QLabel#MaintainerOperationStatus {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
}}

QLabel#MaintainerOperationStatus[error="true"] {{
    color: {DANGER_COLOR};
}}

QLabel#MaintainerOperationStatus[error="false"] {{
    color: {SIGNAL_ACTIVE_COLOR};
}}

QPushButton#MFCControlButton {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {PRIMARY_COLOR};
    border-radius: 9px;
    color: {TEXT_COLOR};
    padding: 7px 12px;
    font-size: 14px;
}}

QPushButton#MFCControlButton:hover, QPushButton#MFCControlButton:pressed,
QPushButton#MFCControlButton:checked {{
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QPushButton#MFCControlButton:disabled {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};
    border-color: {BORDER_COLOR};
}}

QPushButton#MaintainerSequenceButton {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
    color: {TEXT_COLOR};
    padding: 14px 16px;
    font-size: 16px;
    font-weight: 600;
}}

QPushButton#MaintainerSequenceButton:hover {{
    background-color: {SURFACE_SECONDARY_COLOR};
    border-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};
}}

QPushButton#MaintainerSequenceButton:disabled {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};
    border-color: {BORDER_COLOR};
}}

QPushButton#MaintainerSequenceButton:pressed {{
    background-color: {SURFACE_SECONDARY_COLOR};
    color: {TEXT_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QPushButton#MaintenanceActionButton {{
    padding: 8px 12px;
    font-size: 14px;
}}

QPushButton#DemoActionButton:disabled, QPushButton#RecipeActionButton:disabled,
QPushButton#SetpointStepButton:disabled, QPushButton#BackButton:disabled,
QPushButton#LoginButton:disabled, QPushButton#MaintenanceActionButton:disabled,
QPushButton#SettingsCloseButton:disabled {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};
    border-color: {BORDER_COLOR};
}}

QDoubleSpinBox#MaintenanceSetpointInput {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 14px;
}}

QDialog#SettingsDialog {{
    background-color: {SURFACE_COLOR};
}}

QComboBox#SettingsCombo {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {SURFACE_HOVER_COLOR};
    border-radius: 8px;
    padding: 7px 10px;
    min-width: 140px;
}}

QPushButton#SettingsCloseButton {{
    padding: 8px 16px;
    font-size: 15px;
}}


"""


# La hoja de estilos se construye usando los valores de la paleta oscura.
# Al cambiar de tema, cada color exacto se sustituye por el mismo rol semántico
# de la paleta seleccionada.
_COLOR_ROLES = {
    color.upper(): role
    for role, color in THEMES["dark"].items()
}


def build_app_style(theme="dark"):
    """Devuelve la hoja global usando una única paleta semántica."""
    if theme not in THEMES:
        raise ValueError("El tema debe ser 'light' o 'dark'.")
    import re

    palette = THEMES[theme]
    stylesheet = re.sub(
        r"#[0-9A-Fa-f]{6}",
        lambda match: palette[_COLOR_ROLES[match.group(0).upper()]],
        APP_STYLE,
    )
    return stylesheet.replace(
        "__STATUS_ICON_FOREGROUND__",
        _STATUS_ICON_FOREGROUND[theme],
    )
