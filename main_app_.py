from file_parser import parse_excel_historial, historiales_a_dataframe
from stat_core import resumen_global
from stat_ki import killer_instinct_stats
from stat_streaks import streaks_stats
from stat_opponents import opponents_stats
from stat_evolution import evolution_stats
from compare import comparar_jugadores

def format_float(val):
    try:
        return f"{float(val):.2f}"
    except Exception:
        return str(val)


if __name__ == "__main__":
    archivo = "data/historiales/Jugadores.xlsx"
    historiales = parse_excel_historial(archivo)
    df = historiales_a_dataframe(historiales)
    # Calcula 'gano'
    def calcular_gano(row):
        try:
            res = str(row['resultado'])
            if ':' in res:
                sets_ganados, sets_perdidos = res.split(':')
                return int(sets_ganados) > int(sets_perdidos)
        except Exception:
            pass
        return None
    df['gano'] = df.apply(calcular_gano, axis=1)

    resumen = resumen_global(df)
    ki = killer_instinct_stats(df)
    streaks = streaks_stats(df)
    rivales = opponents_stats(df)
    evolucion = evolution_stats(df)
    comparativa = comparar_jugadores(df, 'Pagac Z', 'Pikous M')

def sugerir_umbral(partidos):
    if partidos < 30:
        return 3
    elif partidos < 100:
        return 4
    elif partidos < 300:
        return 5
    elif partidos < 600:
        return 6
    else:
        return 7

# Primero, calcula partidos por jugador
    partidos_por_jugador = df['jugador'].value_counts().to_dict()
    umbrales_por_jugador = {jug: sugerir_umbral(cnt) for jug, cnt in partidos_por_jugador.items()}

# Pasa el diccionario a streaks_stats
    streaks = streaks_stats(df, umbral_larga=umbrales_por_jugador)

    print("=== Resumen Global Mejorado ===")
    for jugador, datos in resumen.items():
        print(f"\nJugador: {jugador}")
        for k, v in datos.items():
            if isinstance(v, float):
                print(f"{k}: {v:.2f}")
            else:
                print(f"{k}: {v}")

        # Killer Instinct SOLO aquí por jugador
        if jugador in ki:
            print("\nKiller Instinct:")
            for k_ki, v_ki in ki[jugador].items():
                if isinstance(v_ki, float):
                    print(f"{k_ki}: {v_ki:.2f}%")
                else:
                    print(f"{k_ki}: {v_ki}")

print(f"\n=== Rachas (umbral adaptativo) ===")
for jugador, datos in streaks.items():
    racha_actual = datos['racha_actual']
    if racha_actual > 0:
        racha_str = f"{racha_actual} victorias seguidas"
    elif racha_actual < 0:
        racha_str = f"{abs(racha_actual)} derrotas seguidas"
    else:
        racha_str = "Sin racha actual"

    print(
        f"{jugador} (Racha larga: ≥{datos['umbral_larga']}): "
        f"Máx victorias: {datos['max_victorias']} | "
        f"Rachas largas victoria: {datos['largas_victorias']} | "
        f"Máx derrotas: {datos['max_derrotas']} | "
        f"Rachas largas derrota: {datos['largas_derrotas']} | "
        f"Racha actual (últimos 20): {racha_str}"
    )
    print("\n=== Rivales ===")
    for jugador, datos in rivales.items():
        print(f"Jugador: {jugador}")
        print(f"  Top rivales: {datos['top_rivales']}")
        print(f"  Winrate vs rivales: {datos['winrate_por_rival']}\n")

    print("\n=== Evolución ===")
    print(evolucion.round(2))

    print("\n=== Comparativa ===")
    for player in comparativa:
        for metric in comparativa[player]:
            comparativa[player][metric] = format_float(comparativa[player][metric])
    print(comparativa)