from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from config.users import (
    MAINTAINER_USERNAME,
    MAINTAINER_PASSWORD,
)
from config.strings import (
    LOGIN_WINDOW_TITLE,
    LOGIN_TITLE,
    USERNAME_LABEL,
    USERNAME_PLACEHOLDER,
    PASSWORD_LABEL,
    PASSWORD_PLACEHOLDER,
    LOGIN_BUTTON_TEXT,
    CANCEL_BUTTON_TEXT,
    INVALID_CREDENTIALS_MESSAGE,
)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

        self._configure_dialog()

    def create_widgets(self):
        # Título del diálogo
        self.title_label = QLabel(LOGIN_TITLE)
        self.title_label.setObjectName("LoginTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Campo de usuario
        self.username_label = QLabel(USERNAME_LABEL)
        self.username_input = QLineEdit()
        self.username_input.setObjectName("LoginInput")
        self.username_input.setPlaceholderText(USERNAME_PLACEHOLDER)

        # Campo de contraseña
        self.password_label = QLabel(PASSWORD_LABEL)
        self.password_input = QLineEdit()
        self.password_input.setObjectName("LoginInput")
        self.password_input.setPlaceholderText(PASSWORD_PLACEHOLDER)
        self.password_input.setEchoMode(QLineEdit.Password)

        # Mensaje de error
        self.error_label = QLabel()
        self.error_label.setObjectName("LoginErrorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()

        # Botones
        self.login_button = QPushButton(LOGIN_BUTTON_TEXT)
        self.login_button.setObjectName("LoginButton")

        self.cancel_button = QPushButton(CANCEL_BUTTON_TEXT)
        self.cancel_button.setObjectName("CancelButton")

    def setup_layout(self):
        # Layout de los botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)

        # Layout principal del diálogo
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(14)

        main_layout.addWidget(self.title_label)
        main_layout.addSpacing(16)

        main_layout.addWidget(self.username_label)
        main_layout.addWidget(self.username_input)

        main_layout.addWidget(self.password_label)
        main_layout.addWidget(self.password_input)

        main_layout.addWidget(self.error_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_signals(self):
        self.login_button.clicked.connect(
            self._validate_credentials
        )
        self.cancel_button.clicked.connect(self.reject)

        # Permite enviar el formulario presionando Enter
        self.username_input.returnPressed.connect(
            self.password_input.setFocus
        )
        self.password_input.returnPressed.connect(
            self._validate_credentials
        )

        # Oculta el error cuando el usuario vuelve a escribir
        self.username_input.textChanged.connect(
            self._hide_error_message
        )
        self.password_input.textChanged.connect(
            self._hide_error_message
        )

    def _configure_dialog(self):
        self.setWindowTitle(LOGIN_WINDOW_TITLE)
        self.setModal(True)
        self.setFixedWidth(440)

        # Coloca inicialmente el cursor en el campo de usuario
        self.username_input.setFocus()

    def _validate_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if (
            username == MAINTAINER_USERNAME
            and password == MAINTAINER_PASSWORD
        ):
            self.accept()
            return

        self._handle_invalid_credentials()

    def _handle_invalid_credentials(self):
        self._show_error(INVALID_CREDENTIALS_MESSAGE)

        # Mantiene el usuario y limpia solamente la contraseña
        self.password_input.clear()
        self.password_input.setFocus()

    def _hide_error_message(self):
        self.error_label.hide()

    def _show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()