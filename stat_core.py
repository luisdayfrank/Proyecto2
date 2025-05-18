import pandas as pd
import numpy as np

def resumen_global(df):
    resumen = {}
    jugadores = df['jugador'].unique()
    for jugador in jugadores:
        jug_df = df[df['jugador'] == jugador].copy()
        resumen_jugador = {}

        # Total torneos (torneo único por nombre y fecha)
        resumen_jugador['total_torneos'] = jug_df[['torneo', 'fecha']].drop_duplicates().shape[0]

        # Total partidos
        resumen_jugador['total_partidos'] = len(jug_df)

        # Rating promedio y rango
        resumen_jugador['rating_promedio'] = round(jug_df['rating_jugador'].mean(), 2)
        resumen_jugador['rango_rating'] = (int(jug_df['rating_jugador'].min()), int(jug_df['rating_jugador'].max()))

        # Win Rate total
        resumen_jugador['winrate_total'] = round(jug_df['gano'].mean() * 100, 2)

        # Volatilidad (desviación estándar de delta)
        resumen_jugador['volatilidad_delta'] = round(jug_df['delta'].std(), 2)

        # Momentum (tendencia en los últimos 10 partidos)
        ultimos = jug_df.sort_values(['fecha', 'hora']).tail(10)
        if len(ultimos) >= 2:
            momentum = ultimos['rating_jugador'].iloc[-1] - ultimos['rating_jugador'].iloc[0]
            if momentum > 5:
                tendencia = "Subida reciente"
            elif momentum < -5:
                tendencia = "Baja reciente"
            else:
                tendencia = "Estable"
            resumen_jugador['momentum'] = tendencia
        else:
            resumen_jugador['momentum'] = "No hay suficientes datos"

        # Definir categorías rivales según rating promedio jugador
        rp = resumen_jugador['rating_promedio']
        def rival_cat(rat):
            if rat >= rp + 50:
                return "Top"
            elif rat >= rp - 50:
                return "Medio"
            else:
                return "Bajo"
        jug_df['cat_rival'] = jug_df['rating_rival'].apply(rival_cat)

        # Winrate vs Top/Medio/Bajo
        for cat in['Top', 'Medio', 'Bajo']:
            mask = jug_df['cat_rival'] == cat
            if mask.any():
                resumen_jugador[f'winrate_vs_{cat}'] = round(jug_df.loc[mask, 'gano'].mean() * 100, 2)
            else:
                resumen_jugador[f'winrate_vs_{cat}'] = None

        # Winrate en finales y terceros puestos
        finales = jug_df[jug_df['ronda'].str.lower().str.contains("final", na=False)]
        terceros = jug_df[jug_df['ronda'].str.lower().str.contains("3", na=False)]

        if not finales.empty:
            resumen_jugador['finales_jugadas'] = len(finales)
            resumen_jugador['finales_ganadas'] = int(finales['gano'].sum())
            resumen_jugador['finales_ganadas_pct'] = round(finales['gano'].mean() * 100, 2)
        else:
            resumen_jugador['finales_jugadas'] = 0
            resumen_jugador['finales_ganadas'] = 0
            resumen_jugador['finales_ganadas_pct'] = None

        if not terceros.empty:
            resumen_jugador['terceros_jugados'] = len(terceros)
            resumen_jugador['terceros_ganados'] = int(terceros['gano'].sum())
            resumen_jugador['terceros_ganados_pct'] = round(terceros['gano'].mean() * 100, 2)
        else:
            resumen_jugador['terceros_jugados'] = 0
            resumen_jugador['terceros_ganados'] = 0
            resumen_jugador['terceros_ganados_pct'] = None

        resumen[jugador] = resumen_jugador

    return resumen