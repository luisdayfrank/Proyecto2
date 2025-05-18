import pandas as pd
import os

def cargar_historial(archivo):
    """Carga el historial general si existe, si no devuelve DataFrame vacío."""
    if os.path.exists(archivo):
        return pd.read_excel(archivo)
    else:
        return pd.DataFrame()

def guardar_historial(df, archivo):
    """Guarda el historial en un archivo Excel."""
    print(f"Guardando archivo: {archivo} con columnas: {df.columns}")
    df.to_excel(archivo, index=False)

def calcular_gano(row):
    try:
        res = str(row['resultado'])
        if ':' in res:
            sets_ganados, sets_perdidos = res.split(':')
            return int(sets_ganados) > int(sets_perdidos)
    except Exception:
        pass
    return None

def asegurar_columna_gano(df):
    """Asegura que el DataFrame tenga la columna 'gano' calculada si es posible."""
    if 'gano' not in df.columns:
        if 'resultado' in df.columns:
            df['gano'] = df.apply(calcular_gano, axis=1)
        else:
            df['gano'] = None
    return df

def actualizar_historial_sin_duplicados(archivo_general, nuevos_historiales):
    """
    Actualiza el historial Excel con nuevos partidos, evitando duplicados.
    - archivo_general: ruta del historial general (Excel)
    - nuevos_historiales: dict {jugador: [partido_dicts]} generado por parse_excel_historial
    """
    # Cargar historial existente (si no existe, DataFrame vacío)
    df_general = cargar_historial(archivo_general)

    # Unir todos los partidos nuevos en un solo DataFrame
    all_nuevos = []
    for jugador, partidos in nuevos_historiales.items():
        for partido in partidos:
            partido['jugador'] = jugador
            all_nuevos.append(partido)
    df_nuevos = pd.DataFrame(all_nuevos)

    # Asegura columna 'gano' en ambos DataFrames
    df_nuevos = asegurar_columna_gano(df_nuevos)
    df_general = asegurar_columna_gano(df_general)

    # Concatenar y eliminar duplicados
    if df_general.empty:
        df_final = df_nuevos
    else:
        df_final = pd.concat([df_general, df_nuevos], ignore_index=True)

    # Clave única para identificar un partido: personaliza si hace falta
    clave = ['jugador', 'fecha', 'torneo', 'hora', 'rival', 'ronda']
    df_final = df_final.drop_duplicates(subset=clave, keep='first')

    # Asegura columna 'gano' después de todo el proceso (por si drop_duplicates la elimina)
    df_final = asegurar_columna_gano(df_final)

    guardar_historial(df_final, archivo_general)

    nuevos_agregados = len(df_final) - (len(df_general) if not df_general.empty else 0)
    duplicados = len(df_nuevos) - nuevos_agregados
    print(f"Total filas guardadas: {len(df_final)} | Nuevos: {nuevos_agregados} | Duplicados: {max(duplicados, 0)}")
    print(f"Columnas finales en el excel: {df_final.columns}")
    print(df_final.head())
    return nuevos_agregados, max(duplicados, 0)
