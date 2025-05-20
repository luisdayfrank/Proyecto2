import pandas as pd
import numpy as np

# --- Funciones Auxiliares para Parsear Sets y Puntos ---
def parsear_resultado_partido(resultado_str):
    """
    Parsea el string de resultado (ej. "3:1") para obtener los sets ganados
    por el jugador y los sets perdidos.
    Retorna (sets_jugador, sets_rival) o (None, None) si el formato es incorrecto.
    """
    try:
        partes = resultado_str.split(':')
        sets_jugador = int(partes[0])
        sets_rival = int(partes[1])
        return sets_jugador, sets_rival
    except:
        return None, None

def calcular_puntos_partido(row):
    """
    Calcula los puntos ganados y perdidos por el jugador en un partido
    a partir de la columna 'sets' y 'resultado'.
    """
    sets_str = row['sets']
    resultado_str = row['resultado']
    
    puntos_jugador_total = 0
    puntos_rival_total = 0
    sets_jugador_ganados_detalle = 0
    sets_rival_ganados_detalle = 0
    
    # Puntos por set para el jugador
    puntos_por_set_jugador = []
    # Puntos por set para el rival
    puntos_por_set_rival = []

    if pd.isna(sets_str) or pd.isna(resultado_str):
        return pd.Series([0, 0, 0, 0, [], []], index=['puntos_jugador_partido', 'puntos_rival_partido', 'sets_jugador_partido_calc', 'sets_rival_partido_calc', 'puntos_set_jugador', 'puntos_set_rival'])

    scores_sets = sets_str.split(' ')
    
    for score_set_str in scores_sets:
        if not score_set_str: continue # Saltar si hay espacios extra
        try:
            p_jug, p_riv = map(int, score_set_str.split('-'))
            puntos_jugador_total += p_jug
            puntos_rival_total += p_riv
            puntos_por_set_jugador.append(p_jug)
            puntos_por_set_rival.append(p_riv)
            
            if p_jug > p_riv:
                sets_jugador_ganados_detalle += 1
            elif p_riv > p_jug:
                sets_rival_ganados_detalle += 1
            # Considerar empates en puntos como no válidos para un set, o ajustar lógica si necesario
        except ValueError:
            # Manejar casos donde el score del set no es parseable, ej. si está vacío o mal formateado
            pass
            
    return pd.Series([puntos_jugador_total, puntos_rival_total, sets_jugador_ganados_detalle, sets_rival_ganados_detalle, puntos_por_set_jugador, puntos_por_set_rival], 
                     index=['puntos_jugador_partido', 'puntos_rival_partido', 'sets_jugador_partido_calc', 'sets_rival_partido_calc', 'puntos_set_jugador', 'puntos_set_rival'])


def resumen_global(df_original):
    resumen = {}
    
    # --- Preprocesamiento del DataFrame ---
    # Es crucial que 'delta' y 'delta_total' sean numéricos.
    # Si vienen con comas, conviértelos antes o aquí.
    # Esta copia asegura que el DataFrame original no se modifique si se pasa desde fuera.
    df = df_original.copy()
    
    # Asegurar que las columnas de rating y delta son numéricas, reemplazando comas si es necesario
    for col_num in ['rating_jugador', 'rating_rival', 'delta', 'delta_total']:
        if df[col_num].dtype == 'object':
            df[col_num] = df[col_num].astype(str).str.replace(',', '.', regex=False).astype(float)
        elif pd.api.types.is_numeric_dtype(df[col_num]):
            pass # Ya es numérico
        else: # Intento de conversión forzada si no es objeto ni numérico conocido
            try:
                df[col_num] = pd.to_numeric(df[col_num].str.replace(',', '.', regex=False))
            except Exception as e:
                print(f"Advertencia: No se pudo convertir la columna {col_num} a numérica: {e}")
                # Podrías optar por llenar con NaN o dejar como está si la conversión falla
                # df[col_num] = pd.to_numeric(df[col_num], errors='coerce')


    # Aplicar el cálculo de puntos y sets detallados
    # Esto añade nuevas columnas al DataFrame 'jug_df' que se usará más adelante
    # Nota: df.apply con axis=1 puede ser lento en DataFrames muy grandes.
    # Si el rendimiento es crítico, se podrían buscar vectorizaciones.
    temp_stats = df.apply(calcular_puntos_partido, axis=1)
    df = pd.concat([df, temp_stats], axis=1)
    
    # Parsear la columna 'resultado' para obtener sets_jugador y sets_rival de forma más directa
    parsed_results = df['resultado'].apply(parsear_resultado_partido)
    df['sets_jugador_resultado'] = parsed_results.apply(lambda x: x[0] if x else None)
    df['sets_rival_resultado'] = parsed_results.apply(lambda x: x[1] if x else None)


    jugadores = df['jugador'].unique()
    for jugador in jugadores:
        jug_df = df[df['jugador'] == jugador].copy() # Usar la copia ya procesada
        resumen_jugador = {}

        # --- I. Métricas Estadísticas Básicas ---

        # 1. Métricas Generales del Jugador (Kantor L):
        resumen_jugador['total_partidos_jugados'] = len(jug_df)
        resumen_jugador['total_victorias'] = int(jug_df['gano'].sum())
        resumen_jugador['total_derrotas'] = resumen_jugador['total_partidos_jugados'] - resumen_jugador['total_victorias']
        
        if resumen_jugador['total_partidos_jugados'] > 0:
            resumen_jugador['porcentaje_victorias_general'] = round((resumen_jugador['total_victorias'] / resumen_jugador['total_partidos_jugados']) * 100, 2)
        else:
            resumen_jugador['porcentaje_victorias_general'] = None

        resumen_jugador['rating_jugador_promedio_torneo_inicio'] = round(jug_df['rating_jugador'].mean(), 2) # Tu 'rating_promedio' original
        resumen_jugador['rango_rating_jugador'] = (int(jug_df['rating_jugador'].min()), int(jug_df['rating_jugador'].max())) # Tu 'rango_rating'

        resumen_jugador['cambio_rating_neto_total_partido'] = round(jug_df['delta'].sum(), 2)
        
        if resumen_jugador['total_partidos_jugados'] > 0:
            resumen_jugador['cambio_rating_promedio_por_partido'] = round(jug_df['delta'].mean(), 2)
        else:
            resumen_jugador['cambio_rating_promedio_por_partido'] = None
            
        if resumen_jugador['total_victorias'] > 0:
            resumen_jugador['cambio_rating_promedio_por_victoria'] = round(jug_df[jug_df['gano'] == 1]['delta'].mean(), 2)
        else:
            resumen_jugador['cambio_rating_promedio_por_victoria'] = None
            
        if resumen_jugador['total_derrotas'] > 0:
            resumen_jugador['cambio_rating_promedio_por_derrota'] = round(jug_df[jug_df['gano'] == 0]['delta'].mean(), 2)
        else:
            resumen_jugador['cambio_rating_promedio_por_derrota'] = None
        
        # Cambio de rating neto total por torneo (sumando el delta_total del último partido de cada torneo)
        # Esto requiere identificar el último partido por torneo para el jugador
        if not jug_df.empty:
            # Asegurar que 'hora' es comparable, podría necesitar conversión si es string
            # Si 'hora' es string HH:MM, se puede ordenar directamente. Si es datetime, también.
             # Ordenar para asegurar que tomamos el último partido del torneo
            jug_df_sorted_for_delta = jug_df.sort_values(by=['fecha', 'hora_torneo', 'hora'])
            last_match_per_tournament_delta = jug_df_sorted_for_delta.drop_duplicates(subset=['torneo', 'fecha'], keep='last')
            resumen_jugador['cambio_rating_neto_total_torneo'] = round(last_match_per_tournament_delta['delta_total'].sum(),2)
        else:
            resumen_jugador['cambio_rating_neto_total_torneo'] = 0


        # 2. Métricas por Partido (ya están en jug_df['puntos_jugador_partido'], etc. de calcular_puntos_partido)
        #    y jug_df['sets_jugador_resultado'], jug_df['sets_rival_resultado']
        
        # Diferencial de Puntos Promedio por Partido
        jug_df['diferencial_puntos_partido'] = jug_df['puntos_jugador_partido'] - jug_df['puntos_rival_partido']
        if resumen_jugador['total_partidos_jugados'] > 0:
            resumen_jugador['diferencial_puntos_promedio_partido'] = round(jug_df['diferencial_puntos_partido'].mean(), 2)
        else:
            resumen_jugador['diferencial_puntos_promedio_partido'] = None

        # 3. Métricas Agregadas de Sets y Puntos (Totales y Promedios):
        total_sets_jugador_ganados = jug_df['sets_jugador_resultado'].sum()
        total_sets_rival_ganados = jug_df['sets_rival_resultado'].sum() #_resultado es más fiable que _calc si el parseo es bueno
        
        resumen_jugador['total_sets_ganados_jugador'] = int(total_sets_jugador_ganados)
        resumen_jugador['total_sets_perdidos_jugador'] = int(total_sets_rival_ganados) # Sets perdidos por el jugador son ganados por el rival
        
        total_sets_disputados = total_sets_jugador_ganados + total_sets_rival_ganados
        if total_sets_disputados > 0:
            resumen_jugador['porcentaje_sets_ganados'] = round((total_sets_jugador_ganados / total_sets_disputados) * 100, 2)
        else:
            resumen_jugador['porcentaje_sets_ganados'] = None

        resumen_jugador['total_puntos_ganados_jugador'] = int(jug_df['puntos_jugador_partido'].sum())
        resumen_jugador['total_puntos_perdidos_jugador'] = int(jug_df['puntos_rival_partido'].sum())
        
        total_puntos_disputados = resumen_jugador['total_puntos_ganados_jugador'] + resumen_jugador['total_puntos_perdidos_jugador']
        if total_puntos_disputados > 0:
            resumen_jugador['porcentaje_puntos_ganados'] = round((resumen_jugador['total_puntos_ganados_jugador'] / total_puntos_disputados) * 100, 2)
        else:
            resumen_jugador['porcentaje_puntos_ganados'] = None
        
        # Promedios de puntos en sets ganados/perdidos
        puntos_en_sets_ganados_jugador_lista = []
        puntos_cedidos_en_sets_ganados_jugador_lista = []
        puntos_en_sets_perdidos_jugador_lista = []
        puntos_cedidos_en_sets_perdidos_jugador_lista = []

        for _, row in jug_df.iterrows():
            for i in range(len(row['puntos_set_jugador'])):
                p_jug = row['puntos_set_jugador'][i]
                p_riv = row['puntos_set_rival'][i]
                if p_jug > p_riv: # Set ganado por el jugador
                    puntos_en_sets_ganados_jugador_lista.append(p_jug)
                    puntos_cedidos_en_sets_ganados_jugador_lista.append(p_riv)
                elif p_riv > p_jug: # Set perdido por el jugador
                    puntos_en_sets_perdidos_jugador_lista.append(p_jug)
                    puntos_cedidos_en_sets_perdidos_jugador_lista.append(p_riv)
        
        resumen_jugador['promedio_puntos_en_sets_ganados_jugador'] = round(np.mean(puntos_en_sets_ganados_jugador_lista), 2) if puntos_en_sets_ganados_jugador_lista else None
        resumen_jugador['promedio_puntos_cedidos_en_sets_ganados_jugador'] = round(np.mean(puntos_cedidos_en_sets_ganados_jugador_lista), 2) if puntos_cedidos_en_sets_ganados_jugador_lista else None
        resumen_jugador['promedio_puntos_en_sets_perdidos_jugador'] = round(np.mean(puntos_en_sets_perdidos_jugador_lista), 2) if puntos_en_sets_perdidos_jugador_lista else None
        resumen_jugador['promedio_puntos_cedidos_en_sets_perdidos_jugador'] = round(np.mean(puntos_cedidos_en_sets_perdidos_jugador_lista), 2) if puntos_cedidos_en_sets_perdidos_jugador_lista else None

        # 4. Métricas de Rendimiento vs. Rating del Rival:
        if resumen_jugador['total_partidos_jugados'] > 0:
            resumen_jugador['rating_promedio_rivales'] = round(jug_df['rating_rival'].mean(), 2)
            jug_df['diferencia_rating_jugador_rival'] = jug_df['rating_jugador'] - jug_df['rating_rival']
            resumen_jugador['diferencia_rating_promedio_jugador_vs_rival'] = round(jug_df['diferencia_rating_jugador_rival'].mean(), 2)
        else:
            resumen_jugador['rating_promedio_rivales'] = None
            resumen_jugador['diferencia_rating_promedio_jugador_vs_rival'] = None

        vs_mayor_rating_df = jug_df[jug_df['rating_jugador'] < jug_df['rating_rival']]
        vs_menor_rating_df = jug_df[jug_df['rating_jugador'] > jug_df['rating_rival']]
        
        resumen_jugador['victorias_vs_mayor_rating'] = int(vs_mayor_rating_df['gano'].sum())
        resumen_jugador['derrotas_vs_mayor_rating'] = len(vs_mayor_rating_df) - resumen_jugador['victorias_vs_mayor_rating']
        resumen_jugador['victorias_vs_menor_rating'] = int(vs_menor_rating_df['gano'].sum())
        resumen_jugador['derrotas_vs_menor_rating'] = len(vs_menor_rating_df) - resumen_jugador['victorias_vs_menor_rating']

        if not vs_mayor_rating_df.empty:
            resumen_jugador['porcentaje_victorias_vs_mayor_rating'] = round(vs_mayor_rating_df['gano'].mean() * 100, 2)
        else:
            resumen_jugador['porcentaje_victorias_vs_mayor_rating'] = None
            
        if not vs_menor_rating_df.empty:
            # Ojo: aquí es porcentaje de DERROTAS vs menor rating
            resumen_jugador['porcentaje_derrotas_vs_menor_rating'] = round((1 - vs_menor_rating_df['gano'].mean()) * 100, 2) if len(vs_menor_rating_df) > 0 else None
        else:
            resumen_jugador['porcentaje_derrotas_vs_menor_rating'] = None

        # 5. Análisis de Resultados Específicos de Partido:
        resumen_jugador['frecuencia_marcadores'] = {}
        marcadores_posibles_victoria = ["3:0", "3:1", "3:2"]
        marcadores_posibles_derrota = ["0:3", "1:3", "2:3"]

        for marcador in marcadores_posibles_victoria:
            resumen_jugador['frecuencia_marcadores'][f'victorias_{marcador.replace(":", "_")}'] = int(jug_df[(jug_df['resultado'] == marcador) & (jug_df['gano'] == 1)].shape[0])
        for marcador in marcadores_posibles_derrota:
            resumen_jugador['frecuencia_marcadores'][f'derrotas_{marcador.replace(":", "_")}'] = int(jug_df[(jug_df['resultado'] == marcador) & (jug_df['gano'] == 0)].shape[0])
        
        # Porcentajes (opcional, si lo necesitas)
        # ej. resumen_jugador['porcentaje_victorias_3_0'] = (resumen_jugador['frecuencia_marcadores']['victorias_3_0'] / resumen_jugador['total_victorias']) * 100 if resumen_jugador['total_victorias'] > 0 else None


        # 6. Métricas por Tipo de Ronda:
        resumen_jugador['rendimiento_por_ronda'] = {}
        tipos_ronda = jug_df['ronda'].str.lower().unique() # Usar str.lower() para consistencia
        
        for tipo in tipos_ronda:
            if pd.isna(tipo): continue
            ronda_df = jug_df[jug_df['ronda'].str.lower() == tipo]
            if not ronda_df.empty:
                victorias_ronda = int(ronda_df['gano'].sum())
                partidos_ronda = len(ronda_df)
                resumen_jugador['rendimiento_por_ronda'][tipo] = {
                    'partidos_jugados': partidos_ronda,
                    'victorias': victorias_ronda,
                    'derrotas': partidos_ronda - victorias_ronda,
                    'win_rate': round((victorias_ronda / partidos_ronda) * 100, 2) if partidos_ronda > 0 else None,
                    'delta_promedio': round(ronda_df['delta'].mean(), 2) if partidos_ronda > 0 else None
                }

        # 7. Métricas por Torneo:
        resumen_jugador['total_torneos_jugados'] = jug_df[['torneo', 'fecha']].drop_duplicates().shape[0] # Tu 'total_torneos'
        
        if resumen_jugador['total_torneos_jugados'] > 0:
            # Asumimos que la columna 'posicion' indica la posición final en el torneo
            # Si 'posicion' puede ser no numérica o tener strings, hay que limpiarla
            jug_df['posicion_numerica'] = pd.to_numeric(jug_df['posicion'], errors='coerce')
            # Tomamos la posición del último partido del jugador en cada torneo
            # Esto es una simplificación; la posición real debería ser única por torneo/jugador
            posiciones_torneo = jug_df.sort_values(by=['fecha', 'hora_torneo', 'hora']).drop_duplicates(subset=['torneo', 'fecha'], keep='last')
            
            resumen_jugador['posicion_promedio_torneos'] = round(posiciones_torneo['posicion_numerica'].mean(),2) if not posiciones_torneo.empty else None
            resumen_jugador['torneos_ganados'] = int(posiciones_torneo[posiciones_torneo['posicion_numerica'] == 1].shape[0]) if not posiciones_torneo.empty else 0
            
            if resumen_jugador['total_torneos_jugados'] > 0 :
                 resumen_jugador['porcentaje_torneos_ganados'] = round((resumen_jugador['torneos_ganados'] / resumen_jugador['total_torneos_jugados']) * 100, 2) if resumen_jugador['total_torneos_jugados'] > 0 else None
            else:
                 resumen_jugador['porcentaje_torneos_ganados'] = None
            
            resumen_jugador['delta_total_promedio_por_torneo'] = round(posiciones_torneo['delta_total'].mean(), 2) if not posiciones_torneo.empty else None
        else:
            resumen_jugador['posicion_promedio_torneos'] = None
            resumen_jugador['torneos_ganados'] = 0
            resumen_jugador['porcentaje_torneos_ganados'] = None
            resumen_jugador['delta_total_promedio_por_torneo'] = None


        # --- Métricas que ya tenías (adaptadas o mantenidas) ---
        resumen_jugador['winrate_total_original'] = round(jug_df['gano'].mean() * 100, 2) if not jug_df.empty else None # Tu 'winrate_total'
        resumen_jugador['volatilidad_delta'] = round(jug_df['delta'].std(), 2) if not jug_df.empty else None

        # Momentum (tendencia en los últimos N partidos, aquí N=10)
        # Ordenar por fecha y hora del partido para asegurar la secuencia correcta
        # Asumo que 'hora' es la hora del partido. Si 'hora_torneo' es más relevante para secuencia, ajustar.
        ultimos = jug_df.sort_values(['fecha', 'hora']).tail(10) 
        if len(ultimos) >= 2: # Necesitas al menos 2 puntos para una tendencia
            # Usar 'rating_jugador' al final del partido. Si tienes 'rating_despues_partido', sería mejor.
            # Aquí usamos el rating_jugador que parece ser el rating *antes* del torneo o una snapshot.
            # Para un momentum real de rating, necesitarías el rating después de cada partido.
            # Como alternativa, podemos ver el 'delta' acumulado en los últimos partidos.
            momentum_delta_acumulado = ultimos['delta'].sum()
            
            if momentum_delta_acumulado > 5: # Umbral arbitrario
                tendencia = "Subida reciente de rating"
            elif momentum_delta_acumulado < -5: # Umbral arbitrario
                tendencia = "Baja reciente de rating"
            else:
                tendencia = "Rating estable recientemente"
            resumen_jugador['momentum_rating_ultimos_10_partidos'] = tendencia
            resumen_jugador['momentum_delta_acumulado_ultimos_10'] = round(momentum_delta_acumulado,2)
        else:
            resumen_jugador['momentum_rating_ultimos_10_partidos'] = "No hay suficientes datos (menos de 10 o 2 partidos)"
            resumen_jugador['momentum_delta_acumulado_ultimos_10'] = None


        # Definir categorías rivales según rating promedio jugador (tu lógica original)
        rp = resumen_jugador['rating_jugador_promedio_torneo_inicio'] # Usar el rating promedio que calculamos
        def rival_cat(rat_rival):
            if pd.isna(rat_rival) or pd.isna(rp): return "Desconocido"
            if rat_rival >= rp + 50:
                return "Top"
            elif rat_rival >= rp - 50: # Originalmente era rp - 50. Si es rat >= rp - 50 es "Medio", si no "Bajo".
                return "Medio"
            else:
                return "Bajo"
        jug_df['cat_rival'] = jug_df['rating_rival'].apply(rival_cat)

        resumen_jugador['winrate_vs_categoria_rival'] = {}
        for cat in ['Top', 'Medio', 'Bajo', 'Desconocido']:
            mask = jug_df['cat_rival'] == cat
            cat_df = jug_df[mask]
            if not cat_df.empty:
                resumen_jugador['winrate_vs_categoria_rival'][f'winrate_vs_{cat}'] = round(cat_df['gano'].mean() * 100, 2)
            else:
                resumen_jugador['winrate_vs_categoria_rival'][f'winrate_vs_{cat}'] = None
        
        # Winrate en finales y terceros puestos (tu lógica original, ligeramente ajustada para consistencia)
        # Usar .str.contains es bueno, pero ser específico con .str.lower() == "final" o "3rd" puede ser más robusto si no hay variaciones
        finales_df = jug_df[jug_df['ronda'].str.lower().str.strip() == "final"]
        terceros_df = jug_df[jug_df['ronda'].str.lower().str.strip() == "3rd"]

        resumen_jugador['finales_jugadas'] = len(finales_df)
        if not finales_df.empty:
            resumen_jugador['finales_ganadas'] = int(finales_df['gano'].sum())
            resumen_jugador['finales_ganadas_pct'] = round(finales_df['gano'].mean() * 100, 2)
        else:
            resumen_jugador['finales_ganadas'] = 0
            resumen_jugador['finales_ganadas_pct'] = None

        resumen_jugador['terceros_puestos_jugados'] = len(terceros_df)
        if not terceros_df.empty:
            resumen_jugador['terceros_puestos_ganados'] = int(terceros_df['gano'].sum())
            resumen_jugador['terceros_puestos_ganados_pct'] = round(terceros_df['gano'].mean() * 100, 2)
        else:
            resumen_jugador['terceros_puestos_ganados'] = 0
            resumen_jugador['terceros_puestos_ganados_pct'] = None

        resumen[jugador] = resumen_jugador

    return resumen
