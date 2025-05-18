import pandas as pd
import numpy as np

def killer_instinct_stats(df):
    """
    Devuelve estadísticas killer instinct para cada jugador
    """
    resultado = {}

    for jugador in df['jugador'].unique():
        jug_df = df[df['jugador'] == jugador].copy()
        ki = {}

        # 1. Win Rate en 5to set
        jug_df['sets_jugados'] = jug_df['sets'].apply(lambda x: len(str(x).split()) if pd.notnull(x) else 0)
        cinco_sets = jug_df[jug_df['sets_jugados'] >= 5]
        if not cinco_sets.empty:
            ki['winrate_5sets'] = round(cinco_sets['gano'].mean() * 100, 2)
            ki['partidos_5sets'] = len(cinco_sets)
        else:
            ki['winrate_5sets'] = None
            ki['partidos_5sets'] = 0

        # 2. Win Rate en finales
        finales = jug_df[jug_df['ronda'].str.lower().str.contains("final", na=False)]
        if not finales.empty:
            ki['winrate_finales'] = round(finales['gano'].mean() * 100, 2)
            ki['finales_jugadas'] = len(finales)
        else:
            ki['winrate_finales'] = None
            ki['finales_jugadas'] = 0

        # 3. Victorias viniendo desde atrás (>1 set abajo)
        def fue_remontada(row):
            # Busca score sets, tipo "4-11 13-11 8-11 11-9 11-8"
            sets = str(row['sets']).split()
            # Contar sets ganados/perdidos por orden
            mi_sets, su_sets = 0, 0
            mi, su = [], []
            for s in sets:
                try:
                    a, b = map(int, s.split('-'))
                    mi.append(a)
                    su.append(b)
                except:
                    continue
            # ¿En algún momento fue perdiendo por 2 o más sets en el marcador?
            diff = 0
            perdia = 0
            for i in range(len(mi)):
                diff += (mi[i] > su[i]) - (mi[i] < su[i])
                if diff < -1:
                    perdia = 1
            return perdia and row['gano']
        jug_df['remontada'] = jug_df.apply(fue_remontada, axis=1)
        if jug_df['remontada'].sum() > 0:
            ki['victorias_remontadas'] = jug_df['remontada'].sum()
            ki['remontada_pct'] = round(100 * jug_df['remontada'].mean(), 2)
        else:
            ki['victorias_remontadas'] = 0
            ki['remontada_pct'] = 0

        # 4. Conversión match point (>80%)
        # Definición simple: ¿cuando tuvo la oportunidad de cerrar partido, lo hizo?
        # Aquí: si ganó el último set por diferencia de 2 o más puntos (simulación)
        def cerro_match_point(row):
            try:
                sets = str(row['sets']).split()
                if not sets: return np.nan
                ultimo_set = sets[-1]
                a, b = map(int, ultimo_set.split('-'))
                # Ganó el último set
                if row['gano'] and a > b and (a - b) >= 2:
                    return 1
            except:
                pass
            return 0
        jug_df['convirtio_match_point'] = jug_df.apply(cerro_match_point, axis=1)
        total_casos_mp = jug_df['convirtio_match_point'].notnull().sum()
        if total_casos_mp:
            ki['match_point_conversion_pct'] = round(100 * jug_df['convirtio_match_point'].mean(), 2)
        else:
            ki['match_point_conversion_pct'] = None

        resultado[jugador] = ki

    return resultado