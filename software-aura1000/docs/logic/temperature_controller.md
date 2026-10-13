# `temperature_controller.py`

El módulo `temperature_controller.py` tiene la clase `TempController` con metodos integrados en el Menu Principal de la UI en la seccion de lamparas para poder ajustar un setpoint de temperatura al ejecutar un proceso manual, posterior al ajuste de presion y previo al encendido de plasma. La idea es generar una rampa de subida hasta el setpoint con las 3 lamparas, y luego dejar solamente encendida la lampara central controlando la misma mediante histeresis para lograr mantener la temperatura lo mas estable posible durante el proceso

---