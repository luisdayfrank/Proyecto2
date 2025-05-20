import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QGroupBox, QScrollArea, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from db_manager import cargar_historial
from stat_core import resumen_global
from stat_ki import killer_instinct_stats
from stat_streaks import streaks_stats
from stat_evolution import evolution_stats
from stat_opponents import opponents_stats

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class CompararJugadoresWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        titulo = QLabel("<b>Comparativa de Jugadores</b>")
        titulo.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(titulo)

        # Carga de datos
        self.df = cargar_historial("data/historial_general.xlsx")
        self.jugadores = sorted(self.df["jugador"].unique()) if not self.df.empty else []

        # --- Filtros de tiempo (aplica a ambos jugadores) ---
        self.filtro_tiempo = QComboBox()
        self.filtro_tiempo.addItems([
            "Todos",
            "Últimos 6 meses",
            "Últimos 3 meses",
            "Mes actual"
        ])
        self.filtro_tiempo.currentIndexChanged.connect(self.refrescar)
        self.layout().addWidget(self.filtro_tiempo)

        # --- Selección de jugadores (lado a lado) ---
        panel_selectores = QHBoxLayout()

        # Panel izquierdo (Jugador 1)
        self.buscador_1 = QLineEdit()
        self.buscador_1.setPlaceholderText("Buscar jugador 1...")
        self.buscador_1.textChanged.connect(lambda: self.filtrar_jugadores(1))
        self.lista_jugadores_1 = QListWidget()
        self.lista_jugadores_1.addItems(self.jugadores)
        self.lista_jugadores_1.currentTextChanged.connect(lambda _: self.refrescar())
        panel_izq = QVBoxLayout()
        panel_izq.addWidget(self.buscador_1)
        panel_izq.addWidget(self.lista_jugadores_1)
        panel_selectores.addLayout(panel_izq)

        # Panel derecho (Jugador 2)
        self.buscador_2 = QLineEdit()
        self.buscador_2.setPlaceholderText("Buscar jugador 2...")
        self.buscador_2.textChanged.connect(lambda: self.filtrar_jugadores(2))
        self.lista_jugadores_2 = QListWidget()
        self.lista_jugadores_2.addItems(self.jugadores)
        self.lista_jugadores_2.currentTextChanged.connect(lambda _: self.refrescar())
        panel_der = QVBoxLayout()
        panel_der.addWidget(self.buscador_2)
        panel_der.addWidget(self.lista_jugadores_2)
        panel_selectores.addLayout(panel_der)

        self.layout().addLayout(panel_selectores)

        # --- Área de comparación (con scroll) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.comparacion_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout().addWidget(self.scroll_area)

        # --- Inicializa lista filtrada ---
        self.jugadores_filtrados_1 = self.jugadores.copy()
        self.jugadores_filtrados_2 = self.jugadores.copy()

        self.refrescar()

    def filtrar_jugadores(self, cual):
        if cual == 1:
            texto = self.buscador_1.text().lower()
            self.jugadores_filtrados_1 = [j for j in self.jugadores if texto in j.lower()]
            self.lista_jugadores_1.blockSignals(True)
            self.lista_jugadores_1.clear()
            self.lista_jugadores_1.addItems(self.jugadores_filtrados_1)
            self.lista_jugadores_1.blockSignals(False)
        else:
            texto = self.buscador_2.text().lower()
            self.jugadores_filtrados_2 = [j for j in self.jugadores if texto in j.lower()]
            self.lista_jugadores_2.blockSignals(True)
            self.lista_jugadores_2.clear()
            self.lista_jugadores_2.addItems(self.jugadores_filtrados_2)
            self.lista_jugadores_2.blockSignals(False)

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

    def refrescar(self):
        # Limpia la vista anterior
        for i in reversed(range(self.comparacion_layout.count())):
            item = self.comparacion_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # Obtiene los seleccionados
        jugador1 = self.lista_jugadores_1.currentItem().text() if self.lista_jugadores_1.currentItem() else None
        jugador2 = self.lista_jugadores_2.currentItem().text() if self.lista_jugadores_2.currentItem() else None

        # Títulos de columnas
        tit_layout = QHBoxLayout()
        tit_layout.addWidget(QLabel("<b>Estadística</b>"))
        tit_layout.addWidget(QLabel(f"<b>{jugador1 or ''}</b>"))
        tit_layout.addWidget(QLabel(f"<b>{jugador2 or ''}</b>"))
        tit_widget = QWidget()
        tit_widget.setLayout(tit_layout)
        self.comparacion_layout.addWidget(tit_widget)

        # Si ambos jugadores seleccionados y existen datos, compara módulo por módulo
        if jugador1 and jugador2 and jugador1 in self.jugadores and jugador2 in self.jugadores:
            df1 = self.df[self.df["jugador"] == jugador1]
            df2 = self.df[self.df["jugador"] == jugador2]
            df1_f = self.get_df_filtrado_tiempo(df1)
            df2_f = self.get_df_filtrado_tiempo(df2)

            # --- Resumen global
            resumen1 = resumen_global(df1_f).get(jugador1, {})
            resumen2 = resumen_global(df2_f).get(jugador2, {})
            for key in sorted(set(resumen1.keys()) | set(resumen2.keys())):
                row = QHBoxLayout()
                row.addWidget(QLabel(key.replace("_"," ").capitalize()))
                row.addWidget(QLabel(str(resumen1.get(key, ""))))
                row.addWidget(QLabel(str(resumen2.get(key, ""))))
                w = QWidget(); w.setLayout(row)
                self.comparacion_layout.addWidget(w)

            # --- Killer Instinct
            ki1 = killer_instinct_stats(df1_f).get(jugador1, {})
            ki2 = killer_instinct_stats(df2_f).get(jugador2, {})
            self.comparacion_layout.addWidget(QLabel("<b>Killer Instinct</b>"))
            for key in sorted(set(ki1.keys()) | set(ki2.keys())):
                row = QHBoxLayout()
                row.addWidget(QLabel(key.replace("_"," ").capitalize()))
                row.addWidget(QLabel(str(ki1.get(key, ""))))
                row.addWidget(QLabel(str(ki2.get(key, ""))))
                w = QWidget(); w.setLayout(row)
                self.comparacion_layout.addWidget(w)

            # --- Rachas
            streak1 = streaks_stats(df1_f).get(jugador1, {})
            streak2 = streaks_stats(df2_f).get(jugador2, {})
            self.comparacion_layout.addWidget(QLabel("<b>Rachas</b>"))
            for key in sorted(set(streak1.keys()) | set(streak2.keys())):
                row = QHBoxLayout()
                row.addWidget(QLabel(key.replace("_", " ").capitalize()))
                row.addWidget(QLabel(str(streak1.get(key, ""))))
                row.addWidget(QLabel(str(streak2.get(key, ""))))
                w = QWidget(); w.setLayout(row)
                self.comparacion_layout.addWidget(w)

            # --- Evolución rating (gráficos)
            evo1 = evolution_stats(df1_f)
            evo2 = evolution_stats(df2_f)
            if not evo1.empty or not evo2.empty:
                self.comparacion_layout.addWidget(QLabel("<b>Evolución Rating</b>"))
                plot_widget = QWidget()
                plot_layout = QHBoxLayout()
                # Gráfico 1
                canvas1 = self.plot_evo_canvas(evo1, jugador1)
                plot_layout.addWidget(canvas1)
                # Spacer central
                plot_layout.addWidget(QLabel("vs"))
                # Gráfico 2
                canvas2 = self.plot_evo_canvas(evo2, jugador2)
                plot_layout.addWidget(canvas2)
                plot_widget.setLayout(plot_layout)
                self.comparacion_layout.addWidget(plot_widget)

            # --- Momentum (gráficos)
            ult1 = df1_f.tail(20)
            ult2 = df2_f.tail(20)
            self.comparacion_layout.addWidget(QLabel("<b>Momentum (últimos 20 partidos)</b>"))
            plot_widget = QWidget()
            plot_layout = QHBoxLayout()
            canvas1 = self.plot_momentum_canvas(ult1)
            plot_layout.addWidget(canvas1)
            plot_layout.addWidget(QLabel("vs"))
            canvas2 = self.plot_momentum_canvas(ult2)
            plot_layout.addWidget(canvas2)
            plot_widget.setLayout(plot_layout)
            self.comparacion_layout.addWidget(plot_widget)

            # --- Rivales principales
            opp1 = opponents_stats(df1_f, top_n=5).get(jugador1, {})
            opp2 = opponents_stats(df2_f, top_n=5).get(jugador2, {})
            self.comparacion_layout.addWidget(QLabel("<b>Principales Rivales</b>"))
            table_widget = QWidget()
            table_layout = QHBoxLayout()
            table_layout.addWidget(self.rivales_table(opp1))
            table_layout.addWidget(QLabel("vs"))
            table_layout.addWidget(self.rivales_table(opp2))
            table_widget.setLayout(table_layout)
            self.comparacion_layout.addWidget(table_widget)

    def plot_evo_canvas(self, evo, jugador):
        fig, ax = plt.subplots(figsize=(3.5,2), dpi=90)
        if not evo.empty and jugador in evo.columns:
            evo = evo.tail(12)
            meses = [mes.strftime('%Y-%m') for mes in evo.index]
            ratings = [evo[jugador][mes] if pd.notnull(evo[jugador][mes]) else None for mes in evo.index]
            if any(r is not None for r in ratings):
                ax.plot(meses, ratings, marker='o', color='#1f77b4')
                ax.set_title('Rating')
                ax.set_xlabel('Mes')
                ax.grid(True, linestyle=':')
                ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(bottom=0)
        fig.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return canvas

    def plot_momentum_canvas(self, ultimos):
        fig, ax = plt.subplots(figsize=(3.5,1.2), dpi=90)
        if not ultimos.empty:
            resultados = list(ultimos['gano'])
            colores = ['#4CAF50' if res == 1 else '#E53935' if res == 0 else '#9E9E9E' for res in resultados]
            ax.bar(range(1, len(resultados)+1), [1]*len(resultados), color=colores, edgecolor='black')
            ax.set_ylim(0, 1.3)
            ax.set_xlim(0.5, len(resultados)+0.5)
            ax.set_yticks([])
            ax.set_xticks(range(1, len(resultados)+1))
            ax.set_title('Momentum')
            ax.tick_params(axis='x', labelrotation=0)
        else:
            ax.set_title("Sin datos")
        fig.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return canvas

    def rivales_table(self, opp):
        rivales = opp.get('top_rivales', {})
        winrates = opp.get('winrate_por_rival', {})
        html = "<table border='1' cellpadding='2'><tr><th>Rival</th><th>Enfrentamientos</th><th>Winrate</th></tr>"
        for rival, enfrent in rivales.items():
            wr = winrates.get(rival, None)
            wr_str = f"{wr*100:.1f}%" if wr is not None else "-"
            html += f"<tr><td>{rival}</td><td>{enfrent}</td><td>{wr_str}</td></tr>"
        html += "</table>"
        lbl = QLabel(html)
        lbl.setWordWrap(True)
        return lbl