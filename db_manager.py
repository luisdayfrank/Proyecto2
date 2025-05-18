import pandas as pd

def guardar_historial(df, archivo):
    df.to_excel(archivo, index=False)

def cargar_historial(archivo):
    return pd.read_excel(archivo)