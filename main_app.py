import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QMenu, QAction,
    QProgressDialog, QPlainTextEdit, QDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QPropertyAnimation, QEasingCurve, QProcess, QPoint
from PyQt5.QtGui import QIcon, QFont
from cargar_datos_widget import CargarDatosWidget
from visualizacion_jugadores_widget import VisualizacionJugadoresWidget
from comparar_jugadores_widget import CompararJugadoresWidget
# ---- Ejemplo de widgets "dummy" para Dashboard e Historial ----
# Sustituye por tus widgets reales más adelante
class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel("Aquí irá el dashboard general")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

class HistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel("Aquí irá la visualización de historial de jugadores")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

# ---- Fin widgets dummy ----

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador de Jugadores")
        self.setGeometry(100, 100, 1150, 650)
        self.process = None
        self.progress_dialog = None

        # Estilos visuales (puedes personalizar más en style.qss si lo deseas)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f6fa; }
            QWidget#sidebar { background-color: #2c3e50; }
            QPushButton#MenuButton {
                background-color: transparent;
                color: #ecf0f1;
                text-align: left;
                padding: 12px 20px;
                border: none; font-size: 14px; border-radius: 4px;
                margin: 4px 8px; border-left: 5px solid transparent;
            }
            QPushButton#MenuButton:hover {
                background-color: rgba(255,255,255,0.1);
                border-left: 5px solid #3498db; padding-left: 15px;
            }
            QPushButton#MenuButton:checked {
                background-color: #3498db;
                border-left: 5px solid #ecf0f1;
                font-weight: 500; color: white;
            }
            QPushButton#SettingsButton {
                background-color: #816ed8; border: 2px solid #d4d1ff;
                color: white; border-radius: 8px; margin: 10px;
                min-width: 45px; max-width: 45px; min-height: 45px; max-height: 45px;
                qproperty-iconSize: 24px 24px;
            }
            QPushButton#SettingsButton:hover {
                background-color: #917ee0; border: 2px solid white;
            }
            QWidget#MainContent { background-color: #fff; border-top-left-radius: 10px; border-bottom-left-radius: 10px; }
            QLabel#headerTitle { font-size: 20px; color: #2d3436; font-weight: 600; padding-left: 10px; }
            QLabel#headerTime { font-size: 14px; color: #636e72; }
            QStackedWidget { background-color: transparent; }
            QProgressDialog { font-size: 11pt; }
            QPlainTextEdit#ProgressOutput { font-family: Consolas, Courier New, monospace; background-color: #222; color: #eee; border-radius: 4px; }
        """)

        # Layout principal (sidebar + contenido principal)
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        self.setup_sidebar()
        self.setup_main_content()

        # Timer para actualizar la hora
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

        # Seleccionar la primera vista por defecto
        if self.menu_buttons:
            self.menu_buttons[0].click()

    def setup_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 15, 5, 5)
        sidebar_layout.setSpacing(5)

        # Logo/título
        lbl_logo = QLabel("ANALIZADOR")
        lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet("color: #ecf0f1; font-size: 16pt; font-weight: bold; margin-bottom: 15px;")
        sidebar_layout.addWidget(lbl_logo)

        self.menu_buttons = []
        # --------- ASOCIA widgets reales aquí ----------
        self.button_page_map = [
            ("Dashboard", "view-dashboard", self.show_page, DashboardWidget),
            ("Cargar Datos", "document-open", self.show_page, CargarDatosWidget),
            ("Jugadores", "user-identity", self.show_page, VisualizacionJugadoresWidget),
            ("Versus", "user-identity", self.show_page, CompararJugadoresWidget),
            # Puedes añadir más páginas aquí
        ]
        # --------- FIN widgets ---------

        # Botones de menú
        for i, (text, icon_name, callback, WidgetClass) in enumerate(self.button_page_map):
            btn = QPushButton(f" {text}")
            btn.setObjectName("MenuButton")
            icon = QIcon.fromTheme(icon_name)
            if icon.isNull():
                icon = QIcon.fromTheme("application-x-executable")
            btn.setIcon(icon)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, index=i: self.handle_button_click(index))
            btn.setCursor(Qt.PointingHandCursor)
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addStretch()

        # Botón de configuración/acciones
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("SettingsButton")
        settings_icon = QIcon.fromTheme("preferences-system")
        if settings_icon.isNull():
            settings_icon = QIcon.fromTheme("application-x-executable")
            self.settings_button.setText("...")
        self.settings_button.setIcon(settings_icon)
        self.settings_button.setToolTip("Acciones")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.show_settings_menu)
        sidebar_layout.addWidget(self.settings_button, 0, Qt.AlignHCenter)

        self.main_layout.addWidget(sidebar)

    def handle_button_click(self, index):
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        callback = self.button_page_map[index][2]
        if callback:
            callback(index)

    def setup_main_content(self):
        content_widget = QWidget()
        content_widget.setObjectName("MainContent")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 20, 25, 20)
        content_layout.setSpacing(15)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0,0,0,0)
        self.title_label = QLabel("Dashboard")
        self.title_label.setObjectName("headerTitle")
        self.time_label = QLabel()
        self.time_label.setObjectName("headerTime")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)
        content_layout.addWidget(header)

        # StackedWidget para cambiar de página
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget, 1)

        # Instanciar las páginas reales (o placeholders)
        self.pages = []
        for text, icon_name, callback, WidgetClass in self.button_page_map:
            try:
                page_widget = WidgetClass()
                self.pages.append(page_widget)
                self.stacked_widget.addWidget(page_widget)
            except Exception as e:
                placeholder = QLabel(f"Error al cargar '{text}': {e}")
                placeholder.setAlignment(Qt.AlignCenter)
                self.pages.append(placeholder)
                self.stacked_widget.addWidget(placeholder)

        self.main_layout.addWidget(content_widget, 1)

    def update_time(self):
        current_time = QDateTime.currentDateTime()
        self.time_label.setText(current_time.toString("dd/MM/yyyy | hh:mm:ss"))

    def animate_header(self, new_title):
        self.title_label.setText(new_title)
        self.title_label.setGraphicsEffect(None)
        opacity_effect = QWidget().graphicsEffect()
        animation = QPropertyAnimation(self.title_label, b"windowOpacity")
        animation.setDuration(500)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

    def show_page(self, index):
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            new_title = self.button_page_map[index][0]
            self.title_label.setText(new_title)
        else:
            print(f"Error: Índice de página fuera de rango: {index}")

    def show_settings_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #34495e; color: white; border: 1px solid #2c3e50; border-radius: 4px; }
            QMenu::item { padding: 8px 25px 8px 20px; }
            QMenu::item:selected { background-color: #3498db; }
            QMenu::separator { height: 1px; background: #2c3e50; margin-left: 10px; margin-right: 10px; }
        """)
        # Acciones del menú (puedes personalizarlas)
        cargar_action = QAction(QIcon.fromTheme("document-save-as"), "Cargar Datos", self)
        cargar_action.triggered.connect(self.show_placeholder_msg)
        metricas_action = QAction(QIcon.fromTheme("view-statistics"), "Métricas", self)
        metricas_action.triggered.connect(self.show_placeholder_msg)
        menu.addAction(cargar_action)
        menu.addAction(metricas_action)
        button_pos = self.settings_button.mapToGlobal(self.settings_button.rect().topLeft())
        menu_pos = button_pos - QPoint(0, menu.sizeHint().height())
        menu.exec_(menu_pos)

    def show_placeholder_msg(self):
        QMessageBox.information(self, "Función no implementada", "Esta función aún no está implementada.")

# --- Bloque principal de ejecución ---
if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
