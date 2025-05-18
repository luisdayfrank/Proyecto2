"""
Entrada principal de la aplicación.
Organiza la interfaz y los flujos principales.
"""
import tkinter as tk
from tkinter import filedialog, messagebox

# Importar módulos internos (cuando estén implementados)
# import file_parser, db_manager, stat_core, compare, etc.

class AnalisisTenisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis de Tenis - Comparador de jugadores")
        self.create_main_menu()

    def create_main_menu(self):
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack()
        tk.Label(frame, text="Seleccione una opción:", font=("Arial", 18)).pack(pady=10)
        tk.Button(frame, text="Añadir jugador", width=25, command=self.add_player).pack(pady=5)
        tk.Button(frame, text="Ver jugador", width=25, command=self.view_player).pack(pady=5)
        tk.Button(frame, text="Actualizar datos", width=25, command=self.update_player).pack(pady=5)
        tk.Button(frame, text="Comparar jugadores", width=25, command=self.compare_players).pack(pady=5)
        tk.Button(frame, text="Salir", width=25, command=self.root.quit).pack(pady=15)

    def add_player(self):
        messagebox.showinfo("Función", "Aquí se añadirá un jugador (lógica pendiente de implementar)")

    def view_player(self):
        messagebox.showinfo("Función", "Aquí se visualizará un jugador (lógica pendiente de implementar)")

    def update_player(self):
        messagebox.showinfo("Función", "Aquí se actualizarán datos de un jugador (lógica pendiente de implementar)")

    def compare_players(self):
        messagebox.showinfo("Función", "Aquí se compararán dos jugadores (lógica pendiente de implementar)")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalisisTenisApp(root)
    root.mainloop()