import sys
import os
import math
import json
import time
import pyautogui
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor, QAction
from PyQt6.QtCore import Qt, QTimer, QRectF, QFileSystemWatcher
import XInput

# IMPORTAR LA INTERFAZ DE CONFIGURACIÓN DIRECTAMENTE
import Config

# --- CONFIGURACIÓN DE PYAUTOGUI (VITAL PARA FLUIDEZ) ---
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# ==============================================================================
# ⚙️ SISTEMA DE CONFIGURACIÓN GLOBAL (Vía config.json oculto en AppData)
# ==============================================================================
appdata_dir = os.path.join(os.getenv('APPDATA'), 'TecladoEspiralXbox')
if not os.path.exists(appdata_dir):
    os.makedirs(appdata_dir)
ARCHIVO_CONFIG = os.path.join(appdata_dir, "config.json")

CONFIGURACION_DEFAULT = {
    "zona_muerta": 0.4,
    "velocidad_raton": 5,
    "velocidad_scroll": 15,
    "multiplicador_turbo": 3,
    "sensibilidad_espiral": 0.12,
    "caracteres":       "abcdefghijklmnopqrstuvwxyz1234567890-/,.",
    "caracteres_shift": "ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_?<>",
    "atajos_escritorio": {
        "click_izq": "A", "click_der": "X", "volver": "B", "play_pausa": "Y",
        "atras_nav": "LB", "enter": "START", "prev_track": "LT", "next_track": "RT",
        "modo_turbo": "RB", "abrir_teclado": "L3", "abrir_config": "BACK"
    },
    "atajos_teclado": {
        "escribir_letra": "B", "borrar": "X", "espacio": "Y", "enter": "START",
        "click_izq": "A", "shift": "LT", "alt_gr": "RT", "cerrar_teclado": "L3",
        "modo_turbo": "RB"
    }
}

# Cargar la configuración desde el archivo, o crearla si no existe
def cargar_config():
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return CONFIGURACION_DEFAULT
    else:
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(CONFIGURACION_DEFAULT, f, indent=4)
        return CONFIGURACION_DEFAULT

CONFIGURACION = cargar_config()
# ==============================================================================

ANCHO_VENTANA = 800
ALTO_VENTANA = 800
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

class TecladoEspiralOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput | 
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        pantalla = QApplication.primaryScreen().geometry()
        self.setGeometry(pantalla)
        
        self.modo_teclado = False
        self.shift_activo = False 
        self.clic_izq_activo = False
        self.clic_der_activo = False
        self.indice_float = 0.0
        self.indice_seleccionado = 0
        self.vibracion_frames = 0
        
        # --- NUEVAS VARIABLES DE OPTIMIZACIÓN ---
        self.ultimo_tiempo_input = time.time()
        self.en_reposo = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.bucle_principal)
        self.timer.start(16) 

        self.estado_botones_previo = {}

        # --- SYSTEM TRAY (Bandeja del sistema) ---
        self.setup_tray_icon()

        # Vigilante de archivos: Recarga la config automáticamente si se modifica el JSON
        self.watcher = QFileSystemWatcher([os.path.abspath(ARCHIVO_CONFIG)])
        self.watcher.fileChanged.connect(self.recargar_configuracion_en_vivo)

    def setup_tray_icon(self):
        """Crea un icono en la barra de tareas de Windows (junto a la hora)"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Usamos un icono estándar de Qt (un pequeño monitor/teclado)
        icono = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icono)
        
        # Crear el menú que aparece al hacer click derecho
        tray_menu = QMenu()
        
        accion_config = tray_menu.addAction("⚙️ Configuración")
        accion_config.triggered.connect(self.abrir_menu_configuracion)
        
        tray_menu.addSeparator()
        
        accion_salir = tray_menu.addAction("❌ Salir del Programa")
        accion_salir.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.setToolTip("Teclado Espiral Xbox")

    def recargar_configuracion_en_vivo(self):
        global CONFIGURACION
        print("🔄 Recargando nueva configuración...")
        CONFIGURACION = cargar_config()

    def obtener_estado_mando(self):
        try:
            if XInput.get_connected()[0]:
                return XInput.get_state(0)
        except:
            pass
        return None

    def vibrar(self, motor_izq, motor_der, frames):
        try:
            XInput.set_vibration(0, motor_izq, motor_der)
            self.vibracion_frames = frames
        except:
            pass

    def abrir_menu_configuracion(self):
        """Abre la interfaz gráfica de configuración."""
        print("⚙️ Abriendo interfaz de configuración...")
        try:
            # En lugar de subprocess, abrimos la ventana de PyQt directamente desde el módulo importado
            if not hasattr(self, 'ventana_config') or not self.ventana_config.isVisible():
                self.ventana_config = Config.InterfazConfiguracion()
                self.ventana_config.show()
            else:
                self.ventana_config.activateWindow() # Traer al frente si ya está abierta
        except Exception as e:
            print(f"Error al abrir la configuración: {e}")

    def bucle_principal(self):
        estado = self.obtener_estado_mando()
        if not estado:
            return

        botones_estado = XInput.get_button_values(estado)
        gatillos_estado = XInput.get_trigger_values(estado) 
        
        botones_actuales = {
            'A': botones_estado.get('A', False),
            'B': botones_estado.get('B', False),
            'X': botones_estado.get('X', False),
            'Y': botones_estado.get('Y', False),
            'L3': botones_estado.get('LEFT_THUMB', False),
            'LB': botones_estado.get('LEFT_SHOULDER', False),
            'RB': botones_estado.get('RIGHT_SHOULDER', False),
            'START': botones_estado.get('START', False),
            'BACK': botones_estado.get('BACK', False), 
            'UP': botones_estado.get('DPAD_UP', False),
            'DOWN': botones_estado.get('DPAD_DOWN', False),
            'LEFT': botones_estado.get('DPAD_LEFT', False),
            'RIGHT': botones_estado.get('DPAD_RIGHT', False),
            'LT': gatillos_estado[0] > 0.5,
            'RT': gatillos_estado[1] > 0.5
        }

        self.shift_activo = botones_actuales[CONFIGURACION["atajos_teclado"]["shift"]]

        def boton_presionado(btn):
            return botones_actuales[btn] and not self.estado_botones_previo.get(btn, False)
            
        def boton_soltado(btn):
            return not botones_actuales[btn] and self.estado_botones_previo.get(btn, False)

        # --- BOTÓN DE CONFIGURACIÓN ---
        if boton_presionado(CONFIGURACION["atajos_escritorio"]["abrir_config"]):
            self.abrir_menu_configuracion()

        # --- LÓGICA DE CAMBIAR MODO ---
        btn_modo = CONFIGURACION["atajos_escritorio"]["abrir_teclado"]
        if boton_presionado(btn_modo):
            self.modo_teclado = not self.modo_teclado
            if self.clic_izq_activo: 
                pyautogui.mouseUp(button='left'); self.clic_izq_activo = False
            if self.clic_der_activo: 
                pyautogui.mouseUp(button='right'); self.clic_der_activo = False
            self.update() 

        sticks = XInput.get_thumb_values(estado)
        eje_x_izq, eje_y_izq = sticks[0]
        eje_x_der, eje_y_der = sticks[1]
        
        eje_y_izq = -eje_y_izq 
        eje_y_der = -eje_y_der

        # --- LÓGICA DE MODO REPOSO (OPTIMIZACIÓN DE CPU) ---
        input_activo = (
            any(botones_actuales.values()) or 
            abs(eje_x_izq) > 0.1 or abs(eje_y_izq) > 0.1 or 
            abs(eje_x_der) > 0.1 or abs(eje_y_der) > 0.1
        )

        if input_activo:
            self.ultimo_tiempo_input = time.time()
            if self.en_reposo:
                self.en_reposo = False
                self.timer.setInterval(16) # Volver a toda velocidad (60 FPS)
                print("⚡ Mando en uso: Volviendo a 60 FPS")
        else:
            # Si pasan 5 segundos sin tocar el mando, bajamos a 10 FPS
            if not self.en_reposo and (time.time() - self.ultimo_tiempo_input > 5.0):
                self.en_reposo = True
                self.timer.setInterval(100) # Bajar a 10 FPS
                print("💤 Mando inactivo: Modo reposo activado (Ahorro de CPU)")

        zm = CONFIGURACION["zona_muerta"]
        turbo = CONFIGURACION["multiplicador_turbo"] if botones_actuales['RB'] else 1

        vel_raton = CONFIGURACION["velocidad_raton"] * turbo
        if abs(eje_x_izq) > zm or abs(eje_y_izq) > zm:
            dx = eje_x_izq if abs(eje_x_izq) > zm else 0
            dy = eje_y_izq if abs(eje_y_izq) > zm else 0
            pyautogui.move(dx * vel_raton, dy * vel_raton)

        if self.modo_teclado:
            atajos = CONFIGURACION["atajos_teclado"]
            self.actualizar_espiral_vertical(eje_y_der, turbo)

            if boton_presionado(atajos["escribir_letra"]):
                cars = CONFIGURACION["caracteres_shift"] if self.shift_activo else CONFIGURACION["caracteres"]
                pyautogui.write(cars[self.indice_seleccionado])
                self.vibrar(30000, 30000, 6) 
            
            if boton_presionado(atajos["click_izq"]): 
                pyautogui.mouseDown(button='left')
                self.clic_izq_activo = True
            if boton_soltado(atajos["click_izq"]): 
                if self.clic_izq_activo:
                    pyautogui.mouseUp(button='left')
                    self.clic_izq_activo = False
            
            if boton_presionado(atajos["borrar"]): pyautogui.press('backspace')
            if boton_presionado(atajos["espacio"]): pyautogui.press('space')
            if boton_presionado(atajos["enter"]): pyautogui.press('enter')

            if boton_presionado(atajos["shift"]): pyautogui.keyDown('shift')
            if boton_soltado(atajos["shift"]): pyautogui.keyUp('shift')
            if boton_presionado(atajos["alt_gr"]): 
                pyautogui.keyDown('ctrl'); pyautogui.keyDown('alt')
            if boton_soltado(atajos["alt_gr"]): 
                pyautogui.keyUp('ctrl'); pyautogui.keyUp('alt')

            if boton_presionado('UP'): pyautogui.press('up')
            if boton_presionado('DOWN'): pyautogui.press('down')
            if boton_presionado('LEFT'): pyautogui.press('left')
            if boton_presionado('RIGHT'): pyautogui.press('right')

        else:
            atajos = CONFIGURACION["atajos_escritorio"]
            
            vel_scroll = CONFIGURACION["velocidad_scroll"] * turbo
            if abs(eje_y_der) > zm:
                pyautogui.scroll(int(-eje_y_der * vel_scroll))

            if boton_presionado(atajos["click_izq"]): 
                pyautogui.mouseDown(button='left'); self.clic_izq_activo = True
            if boton_soltado(atajos["click_izq"]): 
                if self.clic_izq_activo: pyautogui.mouseUp(button='left'); self.clic_izq_activo = False
            
            if boton_presionado(atajos["click_der"]): 
                pyautogui.mouseDown(button='right'); self.clic_der_activo = True
            if boton_soltado(atajos["click_der"]): 
                if self.clic_der_activo: pyautogui.mouseUp(button='right'); self.clic_der_activo = False

            if boton_presionado(atajos["volver"]): pyautogui.press('esc')
            if boton_presionado(atajos["play_pausa"]): pyautogui.press('playpause')
            if boton_presionado(atajos["atras_nav"]): pyautogui.press('browserback')
            if boton_presionado(atajos["enter"]): pyautogui.press('enter')
            if boton_presionado(atajos["prev_track"]): pyautogui.press('prevtrack')
            if boton_presionado(atajos["next_track"]): pyautogui.press('nexttrack')
            
            if boton_presionado('UP'): pyautogui.press('up')
            if boton_presionado('DOWN'): pyautogui.press('down')
            if boton_presionado('LEFT'): pyautogui.press('left')
            if boton_presionado('RIGHT'): pyautogui.press('right')

        self.estado_botones_previo = botones_actuales
        
        if self.vibracion_frames > 0:
            self.vibracion_frames -= 1
            if self.vibracion_frames == 0:
                try: XInput.set_vibration(0, 0, 0)
                except: pass

    def actualizar_espiral_vertical(self, y, turbo=1):
        if abs(y) > CONFIGURACION["zona_muerta"]:
            sensibilidad = CONFIGURACION["sensibilidad_espiral"] * turbo
            indice_previo = self.indice_seleccionado
            
            self.indice_float += (y * abs(y)) * sensibilidad
            
            cars = CONFIGURACION["caracteres"]
            self.indice_float %= len(cars)
            self.indice_seleccionado = int(round(self.indice_float)) % len(cars)
            
            if self.indice_seleccionado != indice_previo:
                self.vibrar(6000, 6000, 2)
            self.update() 
        else:
            self.update()

    def paintEvent(self, event):
        if not self.modo_teclado: return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pos_raton = self.mapFromGlobal(QCursor.pos())
        
        offset_x = 320
        offset_y = 150
        
        target_x = pos_raton.x() + offset_x
        target_y = pos_raton.y() + offset_y
        margen = 350 
        
        # Variable para saber si el teclado está a la derecha o a la izquierda del ratón
        teclado_a_la_derecha = True
        
        if target_x + margen > self.width(): 
            target_x = pos_raton.x() - offset_x
            teclado_a_la_derecha = False # El teclado saltó a la izquierda
            
        if target_y + margen > self.height(): target_y = pos_raton.y() - offset_y
        
        centro_x = max(margen, min(self.width() - margen, target_x))
        centro_y = max(margen, min(self.height() - margen, target_y))
        
        # Verificación de seguridad final para saber de qué lado quedó
        if centro_x < pos_raton.x():
            teclado_a_la_derecha = False
        else:
            teclado_a_la_derecha = True
            
        painter.translate(centro_x, centro_y)

        set_caracteres = CONFIGURACION["caracteres_shift"] if self.shift_activo else CONFIGURACION["caracteres"]

        # --- REVERTIDO A LA ESTÉTICA ANTERIOR (MÁS COMPACTA) ---
        for d in range(-5, 6): 
            idx_elemento = int(round(self.indice_float)) + d
            d_exacto = float(idx_elemento) - self.indice_float
            
            idx_real = idx_elemento % len(set_caracteres)
            char = set_caracteres[idx_real]
            
            theta = d_exacto * 0.45        
            radio = 140 - (d_exacto * 22) 
            
            if radio < 20: continue   
            if radio > 350: continue  
            
            pos_x = radio * math.cos(theta)
            pos_y = radio * math.sin(theta)
            
            # --- MAGIA DEL FLIP HORIZONTAL ---
            # Si el teclado está a la derecha del ratón, invertimos X 
            # Esto hace que la tecla verde apunte hacia el ratón como un espejo
            if teclado_a_la_derecha:
                pos_x = -pos_x
            
            if d == 0: 
                color_fondo = QColor(25, 130, 25) 
                color_texto = QColor(255, 255, 255)
                size = 60 
            else:
                intensidad = max(40, 100 - int(abs(d_exacto) * 10))
                alpha = max(0, 255 - int(abs(d_exacto) * 35))
                color_fondo = QColor(intensidad, intensidad, intensidad, alpha)
                color_texto = QColor(255, 255, 255, alpha)
                size = max(20, 55 - abs(d_exacto) * 6)
                
            painter.setBrush(QBrush(color_fondo))
            painter.setPen(Qt.PenStyle.NoPen)
            rect = QRectF(pos_x - size/2, pos_y - size/2, size, size)
            painter.drawRoundedRect(rect, 8, 8)
            
            painter.setPen(color_texto)
            font = QFont("Arial", int(size * 0.5), QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, char)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = TecladoEspiralOverlay()
    app.setQuitOnLastWindowClosed(False)
    overlay.show()
    sys.exit(app.exec())