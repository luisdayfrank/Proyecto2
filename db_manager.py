import numpy as np
import pandas as pd
import os

def cargar_historial(archivo):
    if os.path.exists(archivo):
        return pd.read_excel(archivo)
    else:
        return pd.DataFrame()

def guardar_historial(df, archivo):
    df.to_excel(archivo, index=False)

def arreglar_historial(archivo="data/historial_general.xlsx"):
    def calcular_gano(row):
        try:
            res = str(row['resultado'])
            if ':' in res:
                sets_ganados, sets_perdidos = res.split(':')
                return 1 if int(sets_ganados) > int(sets_perdidos) else 0
        except Exception:
            pass
        return None

    df = pd.read_excel(archivo)
    if 'resultado' not in df.columns:
        print("No hay columna 'resultado'.")
        return

    if 'gano' not in df.columns:
        df['gano'] = df.apply(calcular_gano, axis=1)
        df['gano'] = df['gano'].astype('Int64')  # Int64 soporta nulos
        df.to_excel(archivo, index=False)
        print("Columna 'gano' añadida y calculada para todos los partidos. (1 = ganó, 0 = perdió, <NA> = error o sin resultado)")
    else:
        mask_necesita = df['gano'].isnull()
        if mask_necesita.any():
            df.loc[mask_necesita, 'gano'] = df.loc[mask_necesita].apply(calcular_gano, axis=1)
            df['gano'] = df['gano'].astype('Int64')
            df.to_excel(archivo, index=False)
            print(f"Columna 'gano' recalculada/actualizada para {mask_necesita.sum()} filas nuevas. (1 = ganó, 0 = perdió, <NA> = error o sin resultado)")
        else:
            print("Todas las filas ya tienen calculado 'gano'. No se hicieron cambios.")

def actualizar_historial_sin_duplicados(archivo_general, nuevos_historiales):
    df_general = cargar_historial(archivo_general)
    all_nuevos = []
    for jugador, partidos in nuevos_historiales.items():
        for partido in partidos:
            partido['jugador'] = jugador
            all_nuevos.append(partido)
    df_nuevos = pd.DataFrame(all_nuevos)

    if df_general.empty:
        guardar_historial(df_nuevos, archivo_general)
        arreglar_historial(archivo_general)
        return len(df_nuevos), 0

    df_total = pd.concat([df_general, df_nuevos], ignore_index=True)
    clave = ['jugador', 'fecha', 'torneo', 'hora', 'rival', 'ronda']
    df_sin_duplicados = df_total.drop_duplicates(subset=clave, keep='first')
    nuevos_agregados = len(df_sin_duplicados) - len(df_general)
    duplicados = len(df_nuevos) - nuevos_agregados

    guardar_historial(df_sin_duplicados, archivo_general)
    arreglar_historial(archivo_general)
    return nuevos_agregados, duplicados