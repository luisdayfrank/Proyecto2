import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGroupBox, QScrollArea, QComboBox, QSizePolicy,
    QCompleter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
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

        self.df = cargar_historial("data/historial_general.xlsx")
        self.jugadores = sorted(self.df["jugador"].unique()) if not self.df.empty else []

        # --- Filtro de tiempo ---
        self.filtro_tiempo = QComboBox()
        self.filtro_tiempo.addItems([
            "Todos",
            "Últimos 6 meses",
            "Últimos 3 meses",
            "Mes actual"
        ])
        self.filtro_tiempo.currentIndexChanged.connect(self.refrescar)
        self.layout().addWidget(self.filtro_tiempo)

        # --- Buscador de jugadores con autocompletado ---
        panel_selectores = QHBoxLayout()

        # Buscador 1
        self.buscador_1 = QLineEdit()
        self.buscador_1.setPlaceholderText("Jugador 1")
        self.completer_1 = QCompleter(self.jugadores)
        self.completer_1.setCaseSensitivity(False)
        self.buscador_1.setCompleter(self.completer_1)
        self.buscador_1.textChanged.connect(lambda: self.refrescar())
        panel_selectores.addWidget(self.buscador_1, 1)

        # Espacio central
        vs_label = QLabel("<b>VS</b>")
        vs_label.setAlignment(Qt.AlignCenter)
        panel_selectores.addWidget(vs_label, 0)

        # Buscador 2
        self.buscador_2 = QLineEdit()
        self.buscador_2.setPlaceholderText("Jugador 2")
        self.completer_2 = QCompleter(self.jugadores)
        self.completer_2.setCaseSensitivity(False)
        self.buscador_2.setCompleter(self.completer_2)
        self.buscador_2.textChanged.connect(lambda: self.refrescar())
        panel_selectores.addWidget(self.buscador_2, 1)

        self.layout().addLayout(panel_selectores)

        # --- Área de comparación (con scroll SOLO VERTICAL) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Desactiva el scroll horizontal
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.comparacion_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.comparacion_layout)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout().addWidget(self.scroll_area)

        self.refrescar()

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

        jugador1 = self.buscador_1.text().strip()
        jugador2 = self.buscador_2.text().strip()
        if not (jugador1 and jugador2 and jugador1 in self.jugadores and jugador2 in self.jugadores):
            return

        df1 = self.df[self.df["jugador"] == jugador1]
        df2 = self.df[self.df["jugador"] == jugador2]
        df1_f = self.get_df_filtrado_tiempo(df1)
        df2_f = self.get_df_filtrado_tiempo(df2)

        # === RESUMEN GLOBAL EN FICHA, DISEÑO LIMPIO, CENTRADO Y AJUSTADO ===
        resumen1 = resumen_global(df1_f).get(jugador1, {})
        resumen2 = resumen_global(df2_f).get(jugador2, {})
        resumen_keys = list(resumen1.keys()) if resumen1 else list(resumen2.keys())

        group_resumen = QGroupBox("Resumen Global")
        group_resumen.setLayout(QVBoxLayout())

        # Encabezado centrado
        header = QHBoxLayout()
        lbl_est = QLabel("<b>Estadística</b>")
        lbl_est.setAlignment(Qt.AlignCenter)
        lbl_est.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lbl_j1 = QLabel(f"<b>{jugador1}</b>")
        lbl_j1.setAlignment(Qt.AlignCenter)
        lbl_j1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lbl_j2 = QLabel(f"<b>{jugador2}</b>")
        lbl_j2.setAlignment(Qt.AlignCenter)
        lbl_j2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header.addWidget(lbl_est, 2)
        header.addWidget(lbl_j1, 1)
        header.addWidget(lbl_j2, 1)
        group_resumen.layout().addLayout(header)

        # Fila por estadística, todo centrado y bien alineado
        for key in resumen_keys:
            fila = QHBoxLayout()
            lbl_key = QLabel(self._elide_text(key.replace("_", " ").capitalize(), max_chars=42))
            lbl_key.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl_key.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl1 = QLabel(self._elide_text(str(resumen1.get(key, "")), max_chars=42))
            lbl1.setAlignment(Qt.AlignCenter)
            lbl1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl2 = QLabel(self._elide_text(str(resumen2.get(key, "")), max_chars=42))
            lbl2.setAlignment(Qt.AlignCenter)
            lbl2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            fila.addWidget(lbl_key, 2)
            fila.addWidget(lbl1, 1)
            fila.addWidget(lbl2, 1)
            group_resumen.layout().addLayout(fila)

        self.comparacion_layout.addWidget(group_resumen)

        # === KILLER INSTINCT (Ficha estilo original) ===
        ki1 = killer_instinct_stats(df1_f).get(jugador1, {})
        ki2 = killer_instinct_stats(df2_f).get(jugador2, {})
        group_ki = QGroupBox("Killer Instinct")
        group_ki.setLayout(QVBoxLayout())
        header_ki = QHBoxLayout()
        header_ki.addWidget(QLabel("<b>Estadística</b>"), 2)
        header_ki.addWidget(QLabel(f"<b>{jugador1}</b>"), 1)
        header_ki.addWidget(QLabel(f"<b>{jugador2}</b>"), 1)
        group_ki.layout().addLayout(header_ki)
        for key in ki1.keys():
            fila = QHBoxLayout()
            fila.addWidget(QLabel(self._elide_text(key.replace("_", " ").capitalize(), max_chars=32)), 2)
            fila.addWidget(QLabel(self._elide_text(str(ki1.get(key, "")), max_chars=20)), 1)
            fila.addWidget(QLabel(self._elide_text(str(ki2.get(key, "")), max_chars=20)), 1)
            group_ki.layout().addLayout(fila)
        self.comparacion_layout.addWidget(group_ki)

        # === RACHAS (Ficha estilo original) ===
        streak1 = streaks_stats(df1_f).get(jugador1, {})
        streak2 = streaks_stats(df2_f).get(jugador2, {})
        group_rachas = QGroupBox("Rachas")
        group_rachas.setLayout(QVBoxLayout())
        header_rachas = QHBoxLayout()
        header_rachas.addWidget(QLabel("<b>Estadística</b>"), 2)
        header_rachas.addWidget(QLabel(f"<b>{jugador1}</b>"), 1)
        header_rachas.addWidget(QLabel(f"<b>{jugador2}</b>"), 1)
        group_rachas.layout().addLayout(header_rachas)
        for key in streak1.keys():
            fila = QHBoxLayout()
            fila.addWidget(QLabel(self._elide_text(key.replace("_", " ").capitalize(), max_chars=32)), 2)
            fila.addWidget(QLabel(self._elide_text(str(streak1.get(key, "")), max_chars=20)), 1)
            fila.addWidget(QLabel(self._elide_text(str(streak2.get(key, "")), max_chars=20)), 1)
            group_rachas.layout().addLayout(fila)
        self.comparacion_layout.addWidget(group_rachas)

        # === EVOLUCIÓN RATING (Gráficos alineados) ===
        evo1 = evolution_stats(df1_f)
        evo2 = evolution_stats(df2_f)
        if not evo1.empty or not evo2.empty:
            group_evo = QGroupBox("Evolución Rating")
            group_evo.setLayout(QHBoxLayout())
            canvas1 = self.plot_evo_canvas(evo1, jugador1)
            canvas2 = self.plot_evo_canvas(evo2, jugador2)
            group_evo.layout().addWidget(canvas1)
            group_evo.layout().addWidget(QLabel("VS"))
            group_evo.layout().addWidget(canvas2)
            self.comparacion_layout.addWidget(group_evo)

        # === MOMENTUM (Gráficos alineados) ===
        ult1 = df1_f.tail(20)
        ult2 = df2_f.tail(20)
        group_momentum = QGroupBox("Momentum (últimos 20 partidos)")
        group_momentum.setLayout(QHBoxLayout())
        canvas1 = self.plot_momentum_canvas(ult1)
        canvas2 = self.plot_momentum_canvas(ult2)
        group_momentum.layout().addWidget(canvas1)
        group_momentum.layout().addWidget(QLabel("VS"))
        group_momentum.layout().addWidget(canvas2)
        self.comparacion_layout.addWidget(group_momentum)

        # === PRINCIPALES RIVALES (Tabla alineada, estilo ficha) ===
        opp1 = opponents_stats(df1_f, top_n=5).get(jugador1, {})
        opp2 = opponents_stats(df2_f, top_n=5).get(jugador2, {})
        group_opp = QGroupBox("Principales Rivales")
        group_opp.setLayout(QHBoxLayout())
        group_opp.layout().addWidget(self.rivales_table(opp1))
        group_opp.layout().addWidget(QLabel("VS"))
        group_opp.layout().addWidget(self.rivales_table(opp2))
        self.comparacion_layout.addWidget(group_opp)

    def _elide_text(self, text, max_chars=30):
        """Reduce el texto si es muy largo para evitar desbordes y scroll horizontal."""
        if len(text) > max_chars:
            return text[:max_chars-2] + "…"
        return text

    def plot_evo_canvas(self, evo, jugador):
        fig, ax = plt.subplots(figsize=(3.2, 2), dpi=90)
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
        fig, ax = plt.subplots(figsize=(3.2, 1.2), dpi=90)
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