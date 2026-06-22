import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QDoubleSpinBox, QSpinBox, 
                             QPushButton, QTabWidget, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt

# --- NUEVA RUTA PARA OCULTAR EL ARCHIVO EN APPDATA ---
appdata_dir = os.path.join(os.getenv('APPDATA'), 'TecladoEspiralXbox')
if not os.path.exists(appdata_dir):
    os.makedirs(appdata_dir)
ARCHIVO_CONFIG = os.path.join(appdata_dir, "config.json")
# -----------------------------------------------------

# Estilo moderno y oscuro para la interfaz (QSS)
ESTILO_OSCURO = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #333;
    border-radius: 4px;
    background: #252526;
}
QTabBar::tab {
    background: #2d2d30;
    color: #999;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #3e3e42;
    color: #fff;
    font-weight: bold;
    border-bottom: 2px solid #007acc;
}
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #333337;
    border: 1px solid #3f3f46;
    border-radius: 3px;
    padding: 5px;
    color: #fff;
    min-height: 25px;
}
QComboBox:drop-down {
    border: 0px;
}
QPushButton {
    background-color: #007acc;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px;
    font-weight: bold;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #0098ff;
}
QPushButton#btnCancelar {
    background-color: #d32f2f;
}
QPushButton#btnCancelar:hover {
    background-color: #f44336;
}
QLabel {
    font-weight: 500;
}
"""

BOTONES_DISPONIBLES = [
    "A", "B", "X", "Y", 
    "LB", "RB", "LT", "RT", 
    "L3", "R3", "START", "BACK", 
    "UP", "DOWN", "LEFT", "RIGHT"
]

class InterfazConfiguracion(QWidget):
    def __init__(self):
        super().__init__()
        self.config = self.cargar_configuracion()
        self.initUI()

    def cargar_configuracion(self):
        try:
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar config.json.\nAsegúrate de ejecutar el teclado primero.\nDetalles: {e}")
            sys.exit()

    def guardar_configuracion(self):
        # 1. Guardar pestaña General
        self.config["zona_muerta"] = self.spin_zm.value()
        self.config["velocidad_raton"] = self.spin_vraton.value()
        self.config["velocidad_scroll"] = self.spin_vscroll.value()
        self.config["multiplicador_turbo"] = self.spin_turbo.value()
        self.config["sensibilidad_espiral"] = self.spin_sespiral.value()
        
        self.config["caracteres"] = self.txt_chars.text()
        self.config["caracteres_shift"] = self.txt_chars_shift.text()

        # 2. Guardar pestaña Escritorio
        for clave, combo in self.combos_escritorio.items():
            self.config["atajos_escritorio"][clave] = combo.currentText()

        # 3. Guardar pestaña Teclado
        for clave, combo in self.combos_teclado.items():
            self.config["atajos_teclado"][clave] = combo.currentText()

        # Escribir a JSON
        try:
            with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            QMessageBox.information(self, "Éxito", "¡Configuración guardada!\nLos cambios se han aplicado al instante en tu teclado espiral.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    def initUI(self):
        self.setWindowTitle('⚙️ Configuración del Mando & Teclado')
        self.resize(600, 500)
        self.setStyleSheet(ESTILO_OSCURO)

        layout_principal = QVBoxLayout()
        tabs = QTabWidget()
        
        # --- PESTAÑA 1: General ---
        tab_general = QWidget()
        layout_general = QFormLayout()
        
        self.spin_zm = QDoubleSpinBox(); self.spin_zm.setRange(0.01, 0.99); self.spin_zm.setSingleStep(0.05); self.spin_zm.setValue(self.config["zona_muerta"])
        self.spin_vraton = QSpinBox(); self.spin_vraton.setRange(1, 50); self.spin_vraton.setValue(self.config["velocidad_raton"])
        self.spin_vscroll = QSpinBox(); self.spin_vscroll.setRange(1, 100); self.spin_vscroll.setValue(self.config["velocidad_scroll"])
        self.spin_turbo = QSpinBox(); self.spin_turbo.setRange(1, 10); self.spin_turbo.setValue(self.config["multiplicador_turbo"])
        self.spin_sespiral = QDoubleSpinBox(); self.spin_sespiral.setRange(0.01, 1.0); self.spin_sespiral.setSingleStep(0.01); self.spin_sespiral.setValue(self.config["sensibilidad_espiral"])
        
        self.txt_chars = QLineEdit(self.config["caracteres"])
        self.txt_chars_shift = QLineEdit(self.config["caracteres_shift"])

        layout_general.addRow("Zona Muerta del Stick:", self.spin_zm)
        layout_general.addRow("Velocidad Base del Ratón:", self.spin_vraton)
        layout_general.addRow("Velocidad Base de Scroll:", self.spin_vscroll)
        layout_general.addRow("Multiplicador Botón Turbo:", self.spin_turbo)
        layout_general.addRow("Sensibilidad Rueda Espiral:", self.spin_sespiral)
        layout_general.addRow("Letras (Normal):", self.txt_chars)
        layout_general.addRow("Letras (Con Shift):", self.txt_chars_shift)
        
        tab_general.setLayout(layout_general)

        # --- PESTAÑA 2: Modo Escritorio ---
        tab_escritorio = QWidget()
        layout_escritorio = QFormLayout()
        self.combos_escritorio = {}
        
        # Traducción amigable para la UI
        nombres_amigables_esc = {
            "click_izq": "Click Izquierdo", "click_der": "Click Derecho", "volver": "Tecla Volver (Esc)",
            "play_pausa": "Play / Pausa", "atras_nav": "Atrás (Navegador)", "enter": "Tecla Enter",
            "prev_track": "Pista Anterior", "next_track": "Pista Siguiente", "modo_turbo": "Activar Modo Turbo (Mantener)",
            "abrir_teclado": "Abrir Teclado Espiral", "abrir_config": "Abrir esta Configuración"
        }

        for clave, nombre_bonito in nombres_amigables_esc.items():
            combo = QComboBox()
            combo.addItems(BOTONES_DISPONIBLES)
            combo.setCurrentText(self.config["atajos_escritorio"][clave])
            layout_escritorio.addRow(nombre_bonito + ":", combo)
            self.combos_escritorio[clave] = combo

        tab_escritorio.setLayout(layout_escritorio)

        # --- PESTAÑA 3: Modo Teclado ---
        tab_teclado = QWidget()
        layout_teclado = QFormLayout()
        self.combos_teclado = {}
        
        nombres_amigables_tec = {
            "escribir_letra": "Escribir Letra Seleccionada", "borrar": "Borrar (Backspace)",
            "espacio": "Barra Espaciadora", "enter": "Tecla Enter", "click_izq": "Click Izquierdo",
            "shift": "Modificador Mayúsculas (Shift)", "alt_gr": "Modificador Alt Gr",
            "cerrar_teclado": "Cerrar Teclado", "modo_turbo": "Navegación Turbo"
        }

        for clave, nombre_bonito in nombres_amigables_tec.items():
            combo = QComboBox()
            combo.addItems(BOTONES_DISPONIBLES)
            combo.setCurrentText(self.config["atajos_teclado"][clave])
            layout_teclado.addRow(nombre_bonito + ":", combo)
            self.combos_teclado[clave] = combo

        tab_teclado.setLayout(layout_teclado)

        # --- Añadir pestañas al Widget principal ---
        tabs.addTab(tab_general, "General & Velocidad")
        tabs.addTab(tab_escritorio, "Mapeo: Escritorio")
        tabs.addTab(tab_teclado, "Mapeo: Teclado")
        
        layout_principal.addWidget(tabs)

        # --- Botones inferiores ---
        caja_botones = QHBoxLayout()
        caja_botones.addStretch(1) # Empuja los botones a la derecha
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.clicked.connect(self.close)
        
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.clicked.connect(self.guardar_configuracion)
        
        caja_botones.addWidget(btn_cancelar)
        caja_botones.addWidget(btn_guardar)
        
        layout_principal.addLayout(caja_botones)
        self.setLayout(layout_principal)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = InterfazConfiguracion()
    ex.show()
    sys.exit(app.exec())