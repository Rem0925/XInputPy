# XInputPy - Teclado Espiral Xbox 🎮⌨️

![XInputPy](https://img.shields.io/badge/Python-3.12-blue?logo=python) ![PyQt6](https://img.shields.io/badge/PyQt6-UI-green?logo=qt) ![XInput](https://img.shields.io/badge/XInput-Controller-lightgrey?logo=xbox)

XInputPy es una innovadora aplicación de escritorio para Windows/Linux escrita en **Python** que te permite controlar completamente el mouse y escribir texto en tu computadora usando únicamente un **controlador de Xbox**. 

Lo que hace único a este proyecto es su **Teclado Virtual en Espiral Overlay**, una interfaz flotante y transparente diseñada para escribir rápidamente con los joysticks (Thumbsticks), complementada con vibración háptica (Force Feedback) y atajos configurables.

## ✨ Características Principales

- **Teclado en Espiral (Overlay UI):** Interfaz gráfica transparente, renderizada sobre cualquier ventana, construida con `PyQt6`. Navega entre caracteres fluidamente girando el Joystick analógico.
- **Control Total del Mouse:** Controla el puntero, los clics (Izquierdo/Derecho) y la rueda de desplazamiento (Scroll) usando los gatillos y los analógicos del mando.
- **Atajos Personalizables:** Navega hacia atrás, adelante, dale Play/Pausa a tus canciones, activa el modo turbo o simula presionar la tecla `Shift` / `Enter` / `Espacio` usando los botones del control.
- **Configuración en Vivo (JSON):** Configura zonas muertas, sensibilidad y mapeo de botones desde la interfaz gráfica. Los cambios se guardan en un archivo `config.json` que se recarga automáticamente mediante *Hot-Reload* sin reiniciar la app.
- **Vibración Háptica:** Feedback inmersivo; el control vibra al escribir, cambiar de caracteres o ejecutar acciones.
- **Modo Ahorro de Energía:** Optimización inteligente de CPU. Si no detecta entradas del mando en 5 segundos, reduce sus cuadros por segundo (FPS) y vuelve a 60FPS al instante al mover el mando.
- **System Tray:** La app se oculta en la barra de tareas para no estorbar, dándote acceso rápido al menú de configuración en segundo plano.

## 🛠️ Tecnologías y Librerías Utilizadas

- **Python 3** (Lógica principal)
- **PyQt6** (Renderizado del Overlay, Transparencia, System Tray y Ventana de Configuración)
- **XInput-Python** (Lectura en tiempo real de los inputs y vibración del mando de Xbox)
- **PyAutoGUI** (Simulación del cursor y teclado nativo a nivel de sistema operativo)
- **PyInstaller** (Utilizado para compilar la app en un archivo `.exe` o binario independiente)

## 🚀 Cómo Ejecutarlo (Desarrollo)

1. Clona este repositorio:
   ```bash
   git clone https://github.com/Rem0925/XInputPy.git
   ```
2. Instala las dependencias:
   ```bash
   pip install PyQt6 XInput-Python pyautogui
   ```
3. Ejecuta el archivo principal:
   ```bash
   python main.py
   ```

## 🎮 Controles por Defecto

*Puedes cambiar esto a través del menú de Configuración que aparece en la barra de tareas.*

**Modo Escritorio (Mouse):**
- **Stick Izquierdo:** Mover Mouse
- **Stick Derecho (Y):** Rueda de desplazamiento (Scroll)
- **Botón A:** Clic Izquierdo
- **Botón X:** Clic Derecho
- **L3 (Click Stick Izq):** Alternar entre Modo Mouse y Modo Teclado

**Modo Teclado (Overlay Espiral):**
- **Stick Derecho (Y):** Navegar por el espiral de letras
- **Botón B:** Escribir letra seleccionada
- **Botón X:** Borrar (Backspace)
- **Botón Y:** Espacio
- **LT (Gatillo Izquierdo):** Activar mayúsculas (Shift)
- **Start:** Enter

---
**Desarrollado por Eduardo.**
