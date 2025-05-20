from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QListWidget
from PyQt5.QtCore import Qt
from file_parser import parse_excel_historial
from db_manager import guardar_historial
from db_manager import actualizar_historial_sin_duplicados

class CargarDatosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.info_label = QLabel("Carga un archivo Excel con una hoja por jugador para procesar los historiales.")
        self.layout().addWidget(self.info_label)

        self.btn_cargar = QPushButton("Seleccionar archivo Excel")
        self.btn_cargar.clicked.connect(self.cargar_archivo)
        self.layout().addWidget(self.btn_cargar)

        self.result_label = QLabel("")
        self.layout().addWidget(self.result_label)

        self.lista_jugadores = QListWidget()
        self.layout().addWidget(self.lista_jugadores)

    def cargar_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)")
        if not path:
            return

        try:
            historiales = parse_excel_historial(path)
            if not historiales:
                self.result_label.setText("No se encontraron hojas/jugadores en el archivo.")
                return

            self.result_label.setText(f"Archivo procesado: {path.split('/')[-1]} — {len(historiales)} jugadores encontrados.")
            self.lista_jugadores.clear()
            for jugador, partidos in historiales.items():
                self.lista_jugadores.addItem(f"{jugador}: {len(partidos)} partidos")

            QMessageBox.information(self, "Carga exitosa", f"Se procesaron {len(historiales)} jugadores.\nPuedes ver el resumen abajo.")

        except Exception as e:
            self.result_label.setText("Error al procesar el archivo.")
            QMessageBox.critical(self, "Error", f"Ocurrió un error procesando el archivo:\n{e}")

        archivo_general = "data/historial_general.xlsx"
        nuevos_agregados, duplicados = actualizar_historial_sin_duplicados(archivo_general, historiales)

        if nuevos_agregados > 0:
            QMessageBox.information(self, "Carga exitosa", f"{nuevos_agregados} partidos nuevos agregados.")
        if duplicados > 0:
            QMessageBox.warning(self, "Duplicados detectados", f"{duplicados} partidos ya estaban en el historial y no se agregaron.")

        all_partidos = []
        for jugador, partidos in historiales.items():
            for partido in partidos:
                partido['jugador'] = jugador
                all_partidos.append(partido)

        import pandas as pd
        df = pd.DataFrame(all_partidos)

        # Guarda el DataFrame como tu "base de datos"
#        guardar_historial(df, "data/historial_general.xlsx")
