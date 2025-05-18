import pandas as pd
import re
from datetime import datetime

def parse_excel_historial(file_path):
    xls = pd.ExcelFile(file_path)
    historiales = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        partidos = []
        i = 0
        while i < len(df):
            row = df.iloc[i]
            # 1. Detectar inicio de torneo
            if isinstance(row[0], str) and "Tournament" in row[0]:
                # Extraer fecha, hora y nombre del torneo/liga
                torneo_match = re.match(r'(\d{1,2} [A-Za-z]{3} \d{4}) (\d{1,2}:\d{2})\s*Tournament (.+)', row[0])
                if torneo_match:
                    fecha = torneo_match.group(1)
                    hora_torneo = torneo_match.group(2)
                    torneo = torneo_match.group(3).strip()
                else:
                    fecha = None
                    hora_torneo = None
                    torneo = row[0]

                # 2. Datos del jugador (siguiente fila)
                datos_row = df.iloc[i+1] if i+1 < len(df) else None
                rating = int(datos_row[4]) if datos_row is not None and pd.notnull(datos_row[4]) and str(datos_row[4]).isdigit() else None
                lugar = str(datos_row[5]).split()[0] if datos_row is not None and pd.notnull(datos_row[5]) else None
                delta_total = float(str(datos_row[8]).replace(',', '.')) if datos_row is not None and pd.notnull(datos_row[8]) else None

                # Saltar encabezado de partidos (siguiente fila)
                i += 3

                # 3. Leer partidos hasta que termine el bloque (la col A vuelva a tener "Tournament" o esté vacía)
                while i < len(df):
                    partido_row = df.iloc[i]
                    if isinstance(partido_row[0], str) and "Tournament" in partido_row[0]:
                        break # Nuevo torneo, salir del bucle interno
                    if isinstance(partido_row[0], str) and re.match(r'^\d{1,2}:\d{2}$', partido_row[0]):
                        try:
                            partido = {
                                "fecha": fecha,
                                "hora_torneo": hora_torneo,
                                "torneo": torneo,
                                "rating_jugador": rating,
                                "posicion": lugar,
                                "delta_total": delta_total,
                                "hora": partido_row[0],
                                "ronda": partido_row[1],
                                "rival": partido_row[2],
                                "rating_rival": int(partido_row[4]) if pd.notnull(partido_row[4]) and str(partido_row[4]).isdigit() else None,
                                "resultado": str(partido_row[6]).replace(' ', '').replace(':', ':') if pd.notnull(partido_row[6]) else None,
                                "sets": str(partido_row[7]).replace('\xa0', ' ').strip() if pd.notnull(partido_row[7]) else None,
                                "delta": float(str(partido_row[8]).replace(',', '.')) if pd.notnull(partido_row[8]) else None,
                            }
                            partidos.append(partido)
                        except Exception as e:
                            pass # Salta fila si da error
                    i += 1
                continue
            i += 1
        historiales[sheet_name] = partidos
    return historiales

def historiales_a_dataframe(historiales):
    all_partidos = []
    for jugador, partidos in historiales.items():
        for partido in partidos:
            partido['jugador'] = jugador
            all_partidos.append(partido)
    return pd.DataFrame(all_partidos)

# Prueba rápida
# if __name__ == "__main__":
#     archivo = "data/historiales/Jugadores.xlsx"
#     historiales = parse_excel_historial(archivo)
#     for jugador, partidos in historiales.items():
#         print(f"\nJugador: {jugador} - Total partidos: {len(partidos)}")
#         for p in partidos[:3]:
#             print(p)
#         print("-" * 40)
