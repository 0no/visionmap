#!/usr/bin/env python3
"""
VisionMap Creator - Aplicativo para criação de mapas visuais
Ponto de entrada principal da aplicação
"""

import tkinter as tk
from src.ui.main_window import VisionMapApp

def main():
    """Função principal que inicializa a aplicação."""
    root = tk.Tk()
    app = VisionMapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()