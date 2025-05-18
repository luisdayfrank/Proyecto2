import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from file_parser import parse_excel_historial
from stat_core import resumen_global
# Puedes importar más módulos a medida que avances

class ResultModal(QtWidgets.QDialog):
    def __init__(self, jugador, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Resultados: {jugador}")
        self.setModal(True)
        layout = QtWidgets.QVBoxLayout()
        
        label = QtWidgets.QLabel(f"<b>{jugador}</b><br><br>"
                                 f"Torneos: <b>{stats.get('torneos', '-')}</b><br>"
                                 f"Ligas: <b>{stats.get('ligas', '-')}</b><br>"
                                 f"Partidos: <b>{stats.get('partidos', '-')}</b><br>"
                                 f"Winrate: <b>{stats.get('winrate', '-')}%</b><br>"
                                )
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        ok_btn = QtWidgets.QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        self.setLayout(layout)
        self.setFixedWidth(320)
        self.setFixedHeight(260)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador de Jugadores")
        self.setMinimumSize(480, 320)
        self.setStyleSheet(open("style.qss").read())

        # Central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vbox = QtWidgets.QVBoxLayout(central)

        title = QtWidgets.QLabel("Analizador de Jugadores")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 2rem; margin-bottom: 24px;")
        vbox.addWidget(title)

        self.btn_cargar = QtWidgets.QPushButton("Cargar archivo Excel")
        self.btn_cargar.clicked.connect(self.cargar_excel)
        vbox.addWidget(self.btn_cargar)

        self.status = QtWidgets.QLabel("")
        self.status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self.status)

        vbox.addStretch(1)

    def cargar_excel(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)")
        if not path:
            return
        self.status.setText("Procesando archivo...")
        QtWidgets.QApplication.processEvents()

        # 1. Parsear el archivo Excel a un diccionario de historiales (uno por hoja/jugador)
        historiales = parse_excel_historial(path)  # dict: {jugador: dataframe/dict}
        # 2. Para cada jugador, calcular estadísticas globales y mostrar modal
        for jugador, datos in historiales.items():
            stats = resumen_global(datos)
            # Aquí puedes llamar a otros módulos y actualizar stats según necesites
            # Ejemplo: stats.update(streaks_stats(datos))
            self.mostrar_resultado_jugador(jugador, stats)

        self.status.setText("¡Todos los jugadores han sido procesados!")

    def mostrar_resultado_jugador(self, jugador, stats):
        modal = ResultModal(jugador, stats, self)
        modal.exec()

def main():
    app = QtWidgets.QApplication(sys.argv)
    try:
        with open("style.qss") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print("No se pudo cargar style.qss:", e)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
