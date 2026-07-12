from PyQt5.QtWidgets import QStackedWidget, QWidget


class NavigationController:
    def __init__(self, stack: QStackedWidget):
        self.stack = stack
        self.screens = {}

    def register_screen(self, name: str, screen: QWidget):
        """
        Registra una pantalla con un nombre lógico.

        El nombre permite navegar sin depender de los índices internos
        utilizados por QStackedWidget.
        """
        if name in self.screens:
            raise ValueError(f"La pantalla '{name}' ya está registrada.")

        self.screens[name] = screen
        self.stack.addWidget(screen)

    def show_screen(self, name: str):
        """
        Muestra la pantalla asociada al nombre indicado.
        """
        if name not in self.screens:
            raise KeyError(f"La pantalla '{name}' no está registrada.")

        self.stack.setCurrentWidget(self.screens[name])