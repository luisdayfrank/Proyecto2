def comparar_jugadores(df, jugador_a, jugador_b):
    """
    Compara métricas básicas entre dos jugadores.
    """
    a = df[df['jugador'] == jugador_a]
    b = df[df['jugador'] == jugador_b]
    return {
        jugador_a: {
            'partidos': len(a),
            'winrate': a['gano'].mean(),
            'delta_promedio': a['delta'].mean()
        },
        jugador_b: {
            'partidos': len(b),
            'winrate': b['gano'].mean(),
            'delta_promedio': b['delta'].mean()
        }
    }