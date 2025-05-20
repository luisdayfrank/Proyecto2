import pandas as pd
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QGroupBox, QPushButton, QScrollArea, QComboBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
from db_manager import cargar_historial
from stat_core import resumen_global
from stat_ki import killer_instinct_stats
from stat_streaks import streaks_stats
from stat_evolution import evolution_stats
from stat_opponents import opponents_stats
from stat_rating import calificacion_jugador

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class VisualizacionJugadoresWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.titulo = QLabel("<b>Visualización de Jugadores</b>")
        self.titulo.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.titulo)

        # Filtro de tiempo
        self.filtro_tiempo = QComboBox()
        self.filtro_tiempo.addItems([
            "Todos",
            "Últimos 6 meses",
            "Últimos 3 meses",
            "Mes actual"
        ])
        self.filtro_tiempo.currentIndexChanged.connect(self.refrescar_filtrado_modulos)
        self.layout().addWidget(self.filtro_tiempo)

        # Buscador
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar jugador...")
        self.buscador.textChanged.connect(self.filtrar_jugadores)
        self.layout().addWidget(self.buscador)

        # Listado de jugadores
        self.lista_jugadores = QListWidget()
        self.lista_jugadores.currentRowChanged.connect(self.seleccionar_jugador_por_indice)
        self.layout().addWidget(self.lista_jugadores)

        # Navegación tipo ficha
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀")
        self.btn_prev.clicked.connect(self.prev_jugador)
        nav_layout.addWidget(self.btn_prev)
        self.ficha_nombre = QLabel()
        self.ficha_nombre.setAlignment(Qt.AlignCenter)
        self.ficha_nombre.setStyleSheet("font-size: 16px; font-weight: bold;")
        nav_layout.addWidget(self.ficha_nombre, stretch=1)
        self.btn_next = QPushButton("▶")
        self.btn_next.clicked.connect(self.next_jugador)
        nav_layout.addWidget(self.btn_next)
        self.layout().addLayout(nav_layout)

        # ---- Botón copiar todo ----
        boton_layout = QHBoxLayout()
        boton_layout.setAlignment(Qt.AlignRight)
        self.btn_copiar = QPushButton("Copiar todo")
        self.btn_copiar.clicked.connect(self.copiar_todas_estadisticas)
        boton_layout.addWidget(self.btn_copiar)
        self.layout().addLayout(boton_layout)

        # ---- SCROLL AREA para fichas de estadísticas ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.fichas_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout().addWidget(self.scroll_area)

        # FICHA CALIFICACION (número grande)
        self.ficha_rating = QGroupBox("Calificación Global")
        self.ficha_rating.setLayout(QVBoxLayout())
        self.rating_label = QLabel("—")
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.rating_label.setStyleSheet("font-size: 56px; font-weight: bold; color: #1976D2;")
        self.ficha_rating.layout().addWidget(self.rating_label)
        self.fichas_layout.addWidget(self.ficha_rating)

        # Ficha resumen global
        self.ficha_resumen = QGroupBox("Resumen Global")
        self.ficha_resumen.setLayout(QVBoxLayout())
        self.stats_label = QLabel("Selecciona un jugador para ver su ficha.")
        self.stats_label.setAlignment(Qt.AlignTop)
        self.stats_label.setWordWrap(True)
        self.stats_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ficha_resumen.layout().addWidget(self.stats_label)
        self.fichas_layout.addWidget(self.ficha_resumen)

        # Ficha Killer Instinct
        self.ficha_ki = QGroupBox("Killer Instinct")
        self.ficha_ki.setLayout(QVBoxLayout())
        self.ki_label = QLabel()
        self.ki_label.setAlignment(Qt.AlignTop)
        self.ki_label.setWordWrap(True)
        self.ki_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ficha_ki.layout().addWidget(self.ki_label)
        self.fichas_layout.addWidget(self.ficha_ki)

        # Ficha Rachas
        self.ficha_streaks = QGroupBox("Rachas")
        self.ficha_streaks.setLayout(QVBoxLayout())
        self.streaks_label = QLabel()
        self.streaks_label.setAlignment(Qt.AlignTop)
        self.streaks_label.setWordWrap(True)
        self.streaks_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ficha_streaks.layout().addWidget(self.streaks_label)
        self.fichas_layout.addWidget(self.ficha_streaks)

        # Ficha Evolución (con gráfico)
        self.ficha_evo = QGroupBox("Evolución de Rating (mensual)")
        self.ficha_evo.setLayout(QVBoxLayout())
        self.evo_label = QLabel()
        self.evo_label.setAlignment(Qt.AlignTop)
        self.evo_label.setWordWrap(True)
        self.evo_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ficha_evo.layout().addWidget(self.evo_label)
        self.evo_canvas = None  # Canvas de matplotlib
        self.fichas_layout.addWidget(self.ficha_evo)

        # Ficha Momentum (rachas recientes, con gráfico)
        self.ficha_momentum = QGroupBox("Momentum (últimos 20 partidos)")
        self.ficha_momentum.setLayout(QVBoxLayout())
        self.momentum_label = QLabel()
        self.momentum_label.setAlignment(Qt.AlignTop)
        self.momentum_label.setWordWrap(True)
        self.momentum_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ficha_momentum.layout().addWidget(self.momentum_label)
        self.momentum_canvas = None
        self.fichas_layout.addWidget(self.ficha_momentum)

        # Ficha Rivales
        self.ficha_opponents = QGroupBox("Principales Rivales")
        self.ficha_opponents.setLayout(QVBoxLayout())
        self.opponents_label = QLabel()
        self.opponents_label.setAlignment(Qt.AlignTop)
        self.opponents_label.setWordWrap(True)
        self.opponents_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ficha_opponents.layout().addWidget(self.opponents_label)
        self.fichas_layout.addWidget(self.ficha_opponents)

        # Data
        self.df = None
        self.jugadores = []
        self.jugadores_filtrados = []
        self.indice_actual = -1

        # SCROLL MEMORY
        self.last_scroll = 0

        self.cargar_jugadores()

    def cargar_jugadores(self):
        try:
            self.df = cargar_historial("data/historial_general.xlsx")
            if self.df.empty:
                self.lista_jugadores.clear()
                self.stats_label.setText("No hay datos en la base de datos.")
                self.ficha_nombre.setText("")
                return
            self.jugadores = sorted(self.df["jugador"].unique())
            self.filtrar_jugadores()
            self.stats_label.setText("Selecciona un jugador para ver su ficha.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando base de datos:\n{e}")

    def filtrar_jugadores(self):
        texto = self.buscador.text().lower()
        self.jugadores_filtrados = [j for j in self.jugadores if texto in j.lower()]
        self.lista_jugadores.blockSignals(True)
        self.lista_jugadores.clear()
        self.lista_jugadores.addItems(self.jugadores_filtrados)
        self.lista_jugadores.blockSignals(False)
        if self.jugadores_filtrados:
            self.lista_jugadores.setCurrentRow(0)
            self.indice_actual = 0
            self.mostrar_ficha_jugador(0)
        else:
            self.ficha_nombre.setText("")
            self.stats_label.setText("No hay jugadores que coincidan con la búsqueda.")
            self.ki_label.setText("")
            self.streaks_label.setText("")
            self.evo_label.setText("")
            self.opponents_label.setText("")
            self.momentum_label.setText("")
            self.rating_label.setText("—")

    def seleccionar_jugador_por_indice(self, row):
        # Recordar posición del scroll antes de actualizar
        self.last_scroll = self.scroll_area.verticalScrollBar().value()
        if row >= 0 and row < len(self.jugadores_filtrados):
            self.indice_actual = row
            self.mostrar_ficha_jugador(row)
        # Restaurar posición del scroll después de actualizar
        self.scroll_area.verticalScrollBar().setValue(self.last_scroll)

    def refrescar_filtrado_modulos(self):
        if self.indice_actual >= 0 and self.indice_actual < len(self.jugadores_filtrados):
            self.mostrar_ficha_jugador(self.indice_actual)

    def get_df_filtrado_tiempo(self, df):
        if df is None or df.empty:
            return df
        opcion = self.filtro_tiempo.currentText()
        hoy = pd.Timestamp.today().normalize()
        if opcion == "Todos":
            return df
        df = df.copy()
        df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
        if opcion == "Últimos 6 meses":
            desde = hoy - pd.DateOffset(months=6)
            return df[df['fecha_dt'] >= desde]
        elif opcion == "Últimos 3 meses":
            desde = hoy - pd.DateOffset(months=3)
            return df[df['fecha_dt'] >= desde]
        elif opcion == "Mes actual":
            return df[df['fecha_dt'].dt.month == hoy.month]
        return df

    def mostrar_ficha_jugador(self, indice):
        jugador = self.jugadores_filtrados[indice]
        self.ficha_nombre.setText(jugador)
        if self.df is not None and jugador in self.df["jugador"].unique():
            df_jugador = self.df[self.df["jugador"] == jugador]
            df_jugador_filtrado = self.get_df_filtrado_tiempo(df_jugador)

            # CALIFICACION GLOBAL
            try:
                calificacion, _ = calificacion_jugador(df_jugador_filtrado)
                self.rating_label.setText(f"{calificacion:.2f}")
            except Exception:
                self.rating_label.setText("—")

            # Resumen global
            resumen = resumen_global(df_jugador_filtrado).get(jugador, {})
            ficha = "<hr><ul style='margin-left: 0; padding-left: 1em;'>"
            for key, val in resumen.items():
                ficha += f"<li><b>{key.replace('_',' ').capitalize()}:</b> {val}</li>"
            ficha += "</ul><hr>"
            self.stats_label.setText(ficha)

            # Killer instinct
            ki = killer_instinct_stats(df_jugador_filtrado).get(jugador, {})
            ki_text = "<ul style='margin-left: 0; padding-left: 1em;'>"
            for key, val in ki.items():
                ki_text += f"<li><b>{key.replace('_',' ').capitalize()}:</b> {val}</li>"
            ki_text += "</ul>"
            self.ki_label.setText(ki_text)

            # Rachas
            streaks = streaks_stats(df_jugador_filtrado)
            streaks_j = streaks.get(jugador, {})
            streaks_text = "<ul style='margin-left: 0; padding-left: 1em;'>"
            for key, val in streaks_j.items():
                streaks_text += f"<li><b>{key.replace('_',' ').capitalize()}:</b> {val}</li>"
            streaks_text += "</ul>"
            self.streaks_label.setText(streaks_text)

            # Evolución (gráfico)
            self._clear_evo_canvas()
            evo = evolution_stats(df_jugador_filtrado)
            if not evo.empty:
                evo = evo.tail(12)  # últimos 12 meses
                meses = [mes.strftime('%Y-%m') for mes in evo.index]
                ratings = [evo[jugador][mes] if pd.notnull(evo[jugador][mes]) else None for mes in evo.index]
                if any(r is not None for r in ratings):
                    fig, ax = plt.subplots(figsize=(5,2.5), dpi=90)
                    ax.plot(meses, ratings, marker='o', color='#1f77b4')
                    ax.set_title('Evolución del Rating')
                    ax.set_xlabel('Mes')
                    ax.set_ylabel('Rating')
                    ax.grid(True, linestyle=':')
                    ax.tick_params(axis='x', rotation=45)
                    fig.tight_layout()
                    self.evo_canvas = FigureCanvas(fig)
                    self.ficha_evo.layout().addWidget(self.evo_canvas)
                    self.evo_label.setText("")
                else:
                    self.evo_label.setText("Sin datos de rating.")
            else:
                self.evo_label.setText("Sin datos de rating.")

            # Momentum (gráfico de los últimos 20 partidos: verde=win, rojo=lose)
            self._clear_momentum_canvas()
            ultimos = df_jugador_filtrado.tail(20)
            if not ultimos.empty:
                resultados = list(ultimos['gano'])
                colores = ['#4CAF50' if res == 1 else '#E53935' if res == 0 else '#9E9E9E' for res in resultados]
                fig, ax = plt.subplots(figsize=(5,1.5), dpi=90)
                ax.bar(range(1, len(resultados)+1), [1]*len(resultados), color=colores, edgecolor='black')
                ax.set_ylim(0, 1.3)
                ax.set_xlim(0.5, len(resultados)+0.5)
                ax.set_yticks([])
                ax.set_xticks(range(1, len(resultados)+1))
                ax.set_title('Momentum: últimos 20 partidos (verde=win, rojo=lose)')
                ax.tick_params(axis='x', labelrotation=0)
                fig.tight_layout()
                self.momentum_canvas = FigureCanvas(fig)
                self.ficha_momentum.layout().addWidget(self.momentum_canvas)
                self.momentum_label.setText("")
            else:
                self.momentum_label.setText("Sin datos de momentum.")

            # Rivales
            opp = opponents_stats(df_jugador_filtrado, top_n=5).get(jugador, {})
            rivales = opp.get('top_rivales', {})
            winrates = opp.get('winrate_por_rival', {})
            opp_text = "<table border='1' cellpadding='2'><tr><th>Rival</th><th>Enfrentamientos</th><th>Winrate</th></tr>"
            for rival, enfrent in rivales.items():
                wr = winrates.get(rival, None)
                wr_str = f"{wr*100:.1f}%" if wr is not None else "-"
                opp_text += f"<tr><td>{rival}</td><td>{enfrent}</td><td>{wr_str}</td></tr>"
            opp_text += "</table>"
            self.opponents_label.setText(opp_text)
        else:
            self.stats_label.setText("Selecciona un jugador para ver su ficha.")
            self.ki_label.setText("")
            self.streaks_label.setText("")
            self.evo_label.setText("")
            self.momentum_label.setText("")
            self.opponents_label.setText("")
            self.rating_label.setText("—")
            self._clear_evo_canvas()
            self._clear_momentum_canvas()

    def copiar_todas_estadisticas(self):
        # Recolectar textos de todos los módulos
        partes = []
        jugador = self.ficha_nombre.text()
        if jugador:
            partes.append(f"Jugador: {jugador}\n")

        partes.append(f"Calificación Global: {self.rating_label.text()} / 10\n")

        partes.append("=== Resumen Global ===")
        partes.append(self.stats_label.text().replace('<ul>', '').replace('</ul>', '').replace('<li>', '').replace('</li>', '').replace('<hr>', '').replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('<br/>', '\n'))

        partes.append("=== Killer Instinct ===")
        partes.append(self.ki_label.text().replace('<ul>', '').replace('</ul>', '').replace('<li>', '').replace('</li>', '').replace('<hr>', '').replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('<br/>', '\n'))

        partes.append("=== Rachas ===")
        partes.append(self.streaks_label.text().replace('<ul>', '').replace('</ul>', '').replace('<li>', '').replace('</li>', '').replace('<hr>', '').replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('<br/>', '\n'))

        partes.append("=== Evolución de Rating (últimos 12 meses) ===")
        partes.append(self.evo_label.text().replace('<table', '').replace('</table>', '').replace('<tr>', '').replace('</tr>', '').replace('<th>', '').replace('</th>', '').replace('<td>', '\t').replace('</td>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('<br/>', '\n'))

        partes.append("=== Momentum ===")
        partes.append(self.momentum_label.text().replace('<ul>', '').replace('</ul>', '').replace('<li>', '').replace('</li>', '').replace('<hr>', '').replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('<br/>', '\n'))

        partes.append("=== Principales Rivales ===")
        partes.append(self.opponents_label.text().replace('<table', '').replace('</table>', '').replace('<tr>', '').replace('</tr>', '').replace('<th>', '').replace('</th>', '').replace('<td>', '\t').replace('</td>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('<br/>', '\n'))

        texto = '\n'.join(partes)

        # Copiar al portapapeles
        clipboard = QApplication.clipboard()
        clipboard.setText(texto)
        QMessageBox.information(self, "Copiado", "¡Estadísticas copiadas al portapapeles!")

    def _clear_evo_canvas(self):
        if self.evo_canvas is not None:
            self.ficha_evo.layout().removeWidget(self.evo_canvas)
            self.evo_canvas.setParent(None)
            self.evo_canvas = None

    def _clear_momentum_canvas(self):
        if self.momentum_canvas is not None:
            self.ficha_momentum.layout().removeWidget(self.momentum_canvas)
            self.momentum_canvas.setParent(None)
            self.momentum_canvas = None

    def prev_jugador(self):
        self.last_scroll = self.scroll_area.verticalScrollBar().value()
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.lista_jugadores.setCurrentRow(self.indice_actual)
        self.scroll_area.verticalScrollBar().setValue(self.last_scroll)

    def next_jugador(self):
        self.last_scroll = self.scroll_area.verticalScrollBar().value()
        if self.indice_actual < len(self.jugadores_filtrados) - 1:
            self.indice_actual += 1
            self.lista_jugadores.setCurrentRow(self.indice_actual)
        self.scroll_area.verticalScrollBar().setValue(self.last_scroll)