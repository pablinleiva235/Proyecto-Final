# `pyqt_gui.py` y `pyqt_gui.ui`

Estos archivos son la salida Python y el diseño de una interfaz anterior de Qt Designer. `pyqt_gui.py` contiene `Ui_MainWindow.setupUi()` con objetos como `stackedWidget` y `MenuPrincipal`.

La `MainWindow` activa no importa `Ui_MainWindow`: crea `WelcomeScreen`, `MaintainerScreen`, `StatisticsScreen` y `NormalOperationScreen` en código Python. Por ello, la pantalla activa no se actualiza al recompilar estos artefactos heredados.

Si se mantiene el diseño anterior, la compilación se realiza desde `software-aura1000/gui/` apuntando a su archivo existente:

```bash
pyuic5 pyqt_gui.ui -o pyqt_gui.py
```

La documentación antigua indicaba `main_window.ui` y la opción `-x`; ese nombre de archivo no existe en el directorio. Antes de modificar/regenerar estos recursos, confirmar que el objetivo sea mantener la UI heredada y no las pantallas activas de Python.
