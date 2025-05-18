import pandas as pd

def opponents_stats(df, top_n=5):
    """
    Devuelve los principales rivales y winrate vs esos rivales para cada jugador.
    """
    resultados = {}
    for jugador in df['jugador'].unique():
        jug_df = df[df['jugador'] == jugador]
        # Contar los rivales más frecuentes
        top_rivales = jug_df['rival'].value_counts().head(top_n).to_dict()
        winrate_por_rival = {}
        for rival in top_rivales:
            enfrentamientos = jug_df[jug_df['rival'] == rival]
            ganados = enfrentamientos['gano'].sum()
            total = enfrentamientos['gano'].count()
            if total > 0:
                winrate = ganados / total
                winrate_por_rival[rival] = round(winrate, 2)
            else:
                winrate_por_rival[rival] = None
        resultados[jugador] = {
            'top_rivales': top_rivales,
            'winrate_por_rival': winrate_por_rival
        }
    return resultados