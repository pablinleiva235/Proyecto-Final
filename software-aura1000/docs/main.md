# `main.py`

El módulo `main.py` constituye el punto de entrada (*entry point*) principal de la aplicación. Se encarga de coordinar el arranque del entorno gráfico de PyQt5, instanciar la capa de control integrada del hardware y, fundamentalmente, inyectar un manejador de excepciones global (*global exception hook*). Este mecanismo garantiza que ante cualquier falla inesperada del software, el reactor Gasonics Aura 1000 conmute de manera mandatoria a un estado físico seguro antes de finalizar el proceso.

---

## <span style="color: #4CAF50;">Punto de Entrada e Inyección de Seguridad</span>

??? note "Manejador Global de Emergencia: `global_exception_handler(exctype, value, traceback)`"
    Actúa como una rutina de interrupción de última línea de defensa acoplada a `sys.excepthook`. Si un hilo secundario, callback de temporizador o evento de la GUI genera un error no capturado, esta rutina intercepta el flujo, localiza la instancia global del objeto de hardware de forma reflexiva y ejecuta imperativamente el método `shutdown_state()` para desactivar actuadores y bobinas de vacío. Finalmente, despliega un cuadro de diálogo crítico para el operario en el laboratorio antes de matar el proceso.

    ```python
    def global_exception_handler(exctype, value, traceback):
        """
        Captura cualquier excepción no manejada en el software para forzar
        el estado seguro del reactor AURA 1000 antes de cerrar la aplicación.
        """
        print(f"\n[CRITICAL] Error no manejado detectado: {exctype.__name__}: {value}")
        
        try:
            # Buscamos la instancia de hardware a través de la ventana principal
            if 'window' in globals() and hasattr(window, 'hw') and window.hw is not None:
                print("Ejecutando shutdown_state() de emergencia en hardware.py...")
                window.hw.shutdown_state()
            else:
                print("Alerta: No se encontró la instancia de hardware activa para el apagado seguro.")
        except Exception as hw_err:
            print(f"Error crítico al intentar forzar el estado seguro: {hw_err}")

        # Mostrar cartel de alerta al operario en el laboratorio
        try:
            error_msg = (
                f"Ocurrió un error inesperado en el sistema.\n\n"
                f"El hardware se ha llevado a ESTADO SEGURO automáticamente.\n\n"
                f"Detalle del error:\n{value}"
            )
            QtWidgets.QMessageBox.critical(None, "Falla Crítica de Sistema", error_msg)
        except Exception as gui_err:
            print(f"No se pudo mostrar el cuadro de diálogo de Qt: {gui_err}")

        # Llamamos al comportamiento por defecto de Python (imprime el traceback en consola)
        sys.__excepthook__(exctype, value, traceback)
        
        # Forzamos la salida inmediata del script para evitar bucles zombis en la GUI
        sys.exit(1)
    ```

??? note "Bloque Principal de Arranque: `__main__`"
    Maneja la inicialización síncrona del sistema. En primera instancia, desvía el control de excepciones nativo hacia el manejador de emergencia. Luego, crea el lazo de eventos de la aplicación (`QApplication`) e instancia la abstracción del hardware, inicializando exclusivamente los registros digitales necesarios para la lectura inicial del pulsador físico de marcha (*ON*) antes de transferir el control a la ventana principal.

    ```python
    if __name__ == "__main__":
        # Vinculamos el hook de excepciones global antes de arrancar la app
        sys.excepthook = global_exception_handler

        app = QtWidgets.QApplication(sys.argv)
        hw = Hardware()
        
        # Inicializo solo placa digital al inicio ya que debo leer el boton de ON para encender
        window = MainWindow(hw)
        window.show()
        
        sys.exit(app.exec_())
    ```