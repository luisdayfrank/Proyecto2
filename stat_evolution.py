import pandas as pd

def evolution_stats(df):
    """
    Evolución mensual/anual del rating de cada jugador.
    """
    df = df.copy()  # <--- Añade esto al inicio de la función
    df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['fecha_dt', 'rating_jugador'])
    df['mes'] = df['fecha_dt'].dt.to_period('M')
    evolution = df.groupby(['jugador', 'mes'])['rating_jugador'].mean().unstack(0)
    return evolution