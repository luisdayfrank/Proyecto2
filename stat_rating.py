import numpy as np
from stat_core import resumen_global
from stat_ki import killer_instinct_stats
from stat_streaks import streaks_stats
from stat_evolution import evolution_stats
from stat_opponents import opponents_stats

def calificacion_jugador(df_jugador):
    """
    Calificación global (1-10) considerando: rating, dificultad rivales, winrate, volumen,
    volatilidad, momentum, killer instinct y experiencia.
    """
    jugador = df_jugador["jugador"].iloc[0]
    resumen = resumen_global(df_jugador)[jugador]
    ki = killer_instinct_stats(df_jugador)[jugador]
    streaks = streaks_stats(df_jugador)[jugador]

    # 1. Rating promedio (rango: 600-800, normalmente)
    rating_prom = resumen.get("rating_promedio", 650)
    # Escala: 600=3, 700=7, 750+=10
    rating_score = np.clip((rating_prom - 600) / 15, 3, 10)
    
    # 2. Winrate vs top, medio, bajo (ajustado por rating propio)
    win_top = resumen.get("winrate_vs_top", 0)
    win_med = resumen.get("winrate_vs_medio", 0)
    win_bajo = resumen.get("winrate_vs_bajo", 0)
    # Los winrate vs top valen más si tu rating promedio es bajo
    if rating_prom >= 720:
        peso_wintop = 1.5
        peso_winmed = 1.2
        peso_winbajo = 1.0
    elif rating_prom >= 680:
        peso_wintop = 2.0
        peso_winmed = 1.3
        peso_winbajo = 1.0
    else:
        peso_wintop = 2.5
        peso_winmed = 1.5
        peso_winbajo = 1.0
    win_score = (
        (win_top / 10) * peso_wintop +
        (win_med / 10) * peso_winmed +
        (win_bajo / 10) * peso_winbajo
    ) / (peso_wintop + peso_winmed + peso_winbajo) * 10
    win_score = np.clip(win_score, 0, 10)

    # 3. Volumen de partidos (más = mejor, pero con límites)
    total_partidos = resumen.get("total_partidos", 0)
    # 1500+ partidos = 10, 100 = 5, menos de 50 = 2
    if total_partidos >= 1500:
        exp_score = 10
    elif total_partidos >= 500:
        exp_score = 8
    elif total_partidos >= 200:
        exp_score = 6
    elif total_partidos >= 100:
        exp_score = 5
    elif total_partidos >= 50:
        exp_score = 3
    else:
        exp_score = 2

    # 4. Volatilidad (menor es mejor, escala invertida)
    vol = resumen.get("volatilidad_delta", 8)
    # 4=10, 6=7, 8=5, 10=2, 12=0
    if vol <= 4:
        vol_score = 10
    elif vol <= 6:
        vol_score = 7
    elif vol <= 8:
        vol_score = 5
    elif vol <= 10:
        vol_score = 2
    else:
        vol_score = 0

    # 5. Momentum (subida, neutro, baja)
    momentum = resumen.get("momentum", "").lower()
    if "subida" in momentum:
        mom_score = 8
    elif "baja" in momentum:
        mom_score = 4
    else:
        mom_score = 6

    # 6. Killer Instinct (media winrate 5sets, finales, match point)
    ki_vals = []
    for key in ['winrate_5sets', 'winrate_finales', 'match_point_conversion_pct']:
        val = ki.get(key)
        if val is not None:
            ki_vals.append(val / 10)
    ki_score = np.clip(np.mean(ki_vals) if ki_vals else 5, 0, 10)
    # Penalizar si partidos 5sets y finales jugadas <10 (muestra pequeña)
    if ki.get('partidos_5sets', 0) < 10 or ki.get('finales_jugadas', 0) < 10:
        ki_score *= 0.8

    # 7. Experiencia (torneos jugados)
    total_torneos = resumen.get("total_torneos", 0)
    if total_torneos >= 350:
        torneos_score = 10
    elif total_torneos >= 100:
        torneos_score = 7
    elif total_torneos >= 50:
        torneos_score = 5
    elif total_torneos >= 20:
        torneos_score = 3
    else:
        torneos_score = 2

    # 8. Racha máxima (victorias)
    max_victorias = streaks.get("max_victorias", 0)
    if max_victorias >= 15:
        racha_score = 10
    elif max_victorias >= 10:
        racha_score = 8
    elif max_victorias >= 5:
        racha_score = 5
    else:
        racha_score = 2

    # Ponderación contextual
    PESOS = {
        'rating': 0.20,
        'winrate': 0.22,
        'volumen': 0.14,
        'volatilidad': 0.10,
        'momentum': 0.08,
        'killer_instinct': 0.12,
        'experiencia': 0.08,
        'racha_max': 0.06
    }
    score = (
        PESOS['rating'] * rating_score +
        PESOS['winrate'] * win_score +
        PESOS['volumen'] * exp_score +
        PESOS['volatilidad'] * vol_score +
        PESOS['momentum'] * mom_score +
        PESOS['killer_instinct'] * ki_score +
        PESOS['experiencia'] * torneos_score +
        PESOS['racha_max'] * racha_score
    )
    calificacion = round(score, 2)

    detalles = {
        "rating_score": rating_score,
        "win_score": win_score,
        "exp_score": exp_score,
        "volatilidad_score": vol_score,
        "momentum_score": mom_score,
        "killer_instinct_score": ki_score,
        "torneos_score": torneos_score,
        "racha_max_score": racha_score
    }

    return calificacion, detalles