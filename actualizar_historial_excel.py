import pandas as pd

# 1. Leer el historial general existente
def cargar_historial_general(archivo_general):
    try:
        return pd.read_excel(archivo_general)
    except FileNotFoundError:
        return pd.DataFrame()  # Si no existe, empieza vacío

# 2. Leer los nuevos partidos desde otro Excel (puede tener solo 1 jugador y 1 torneo o varios)
from file_parser_excel_struct import parse_excel_historial

def cargar_nuevos_partidos(archivo_nuevo):
    # Usa tu parser para que el formato sea igual que el general
    return parse_excel_historial(archivo_nuevo)

# 3. Unir y eliminar duplicados
def actualizar_historial(archivo_general, archivo_nuevo, archivo_salida):
    # Cargar base antigua
    df_general = cargar_historial_general(archivo_general)
    # Cargar nuevos partidos
    nuevos = cargar_nuevos_partidos(archivo_nuevo)
    # Unir todos los partidos nuevos en un solo DataFrame
    all_nuevos = []
    for jugador, partidos in nuevos.items():
        for partido in partidos:
            partido['jugador'] = jugador
            all_nuevos.append(partido)
    df_nuevos = pd.DataFrame(all_nuevos)

    # Si el general está vacío, simplemente guarda los nuevos
    if df_general.empty:
        df_nuevos.to_excel(archivo_salida, index=False)
        print(f"Historial creado con {len(df_nuevos)} partidos nuevos.")
        return

    # Concatenar y eliminar duplicados
    df_total = pd.concat([df_general, df_nuevos], ignore_index=True)

    # Define la clave única para un partido
    clave = ['jugador', 'fecha', 'torneo', 'hora', 'rival', 'ronda']

    # Quita duplicados (se queda solo con el primero encontrado)
    df_sin_duplicados = df_total.drop_duplicates(subset=clave, keep='first')

    # Detecta cuántos partidos fueron duplicados y se excluyeron
    nuevos_agregados = len(df_sin_duplicados) - len(df_general)
    duplicados = len(df_nuevos) - nuevos_agregados

    df_sin_duplicados.to_excel(archivo_salida, index=False)
    print(f"{nuevos_agregados} partidos nuevos agregados.")
    if duplicados > 0:
        print(f"{duplicados} partidos eran duplicados y no se agregaron.")
    print(f"Total en historial: {len(df_sin_duplicados)} partidos.")

# ------------ PRUEBA DE USO -----------
if __name__ == "__main__":
    archivo_general = "data/historiales/historial_general.xlsx"
    archivo_nuevos = "data/historiales/nuevos_partidos.xlsx"
    archivo_salida = "data/historiales/historial_actualizado.xlsx"
    actualizar_historial(archivo_general, archivo_nuevos, archivo_salida)