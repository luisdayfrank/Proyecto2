import pandas as pd

def streaks_stats(df, umbral_larga=5):
    """
    Si umbral_larga es un dict, lo usa por jugador. Si es int, lo usa global.
    """
    streaks = {}
    for jugador in df['jugador'].unique():
        jug_df = df[df['jugador'] == jugador].sort_values(['fecha', 'hora'])
        # Selecciona umbral
        umbral = umbral_larga[jugador] if isinstance(umbral_larga, dict) else umbral_larga

        max_win, max_lose = 0, 0
        cur_win, cur_lose = 0, 0
        largas_win, largas_lose = 0, 0
        en_racha_win, en_racha_lose = False, False

        for gano in jug_df['gano']:
            if gano:
                cur_win += 1
                max_win = max(max_win, cur_win)
                cur_lose = 0
                if cur_win >= umbral and not en_racha_win:
                    largas_win += 1
                    en_racha_win = True
                if cur_win < umbral:
                    en_racha_win = False
                en_racha_lose = False
            elif gano is not None:
                cur_lose += 1
                max_lose = max(max_lose, cur_lose)
                cur_win = 0
                if cur_lose >= umbral and not en_racha_lose:
                    largas_lose += 1
                    en_racha_lose = True
                if cur_lose < umbral:
                    en_racha_lose = False
                en_racha_win = False

        # Racha actual (últimos 20 partidos)
        ultimos = jug_df.tail(20)
        racha = 0
        for res in reversed(list(ultimos['gano'])):
            if res is True:
                if racha >= 0:
                    racha += 1
                else:
                    break
            elif res is False:
                if racha <= 0:
                    racha -= 1
                else:
                    break

        streaks[jugador] = {
            'max_victorias': max_win,
            'max_derrotas': max_lose,
            'racha_actual': racha,
            'largas_victorias': largas_win,
            'largas_derrotas': largas_lose,
            'umbral_larga': umbral
        }
    return streaks
