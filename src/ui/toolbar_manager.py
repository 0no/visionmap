"""
Gerenciador da barra de ferramentas para a interface do VisionMap
"""

import tkinter as tk


class ToolbarManager:
    """Classe que gerencia a barra de ferramentas da aplicação."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.toolbar = None
        self.buttons = {}
        self.create_toolbar()
    
    def create_toolbar(self):
        """Cria a barra de ferramentas."""
        self.toolbar = tk.Frame(self.parent, bg="lightgray", height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Botão de seleção
        self.buttons['select'] = tk.Button(
            self.toolbar, 
            text="Selecionar (A)", 
            command=self.app.set_select_mode
        )
        self.buttons['select'].pack(side=tk.LEFT, padx=5, pady=5)
        self.buttons['select'].config(relief=tk.SUNKEN)  # Inicialmente ativo
        
        # Botão de adicionar caixa
        self.buttons['add_box'] = tk.Button(
            self.toolbar, 
            text="Adicionar Caixa (B)", 
            command=self.app.set_add_box_mode
        )
        self.buttons['add_box'].pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão de adicionar anotação
        self.buttons['add_note'] = tk.Button(
            self.toolbar, 
            text="Adicionar Anotação (C)", 
            command=self.app.set_add_note_mode
        )
        self.buttons['add_note'].pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão de adicionar container
        self.buttons['add_container'] = tk.Button(
            self.toolbar, 
            text="Adicionar Container (D)", 
            command=self.app.set_add_container_mode
        )
        self.buttons['add_container'].pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão de conectar caixas
        self.buttons['connect'] = tk.Button(
            self.toolbar, 
            text="Conectar (E)", 
            command=self.app.set_connect_mode
        )
        self.buttons['connect'].pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão para trocar a cor
        self.buttons['color'] = tk.Button(
            self.toolbar, 
            text="Trocar Cor (F)", 
            command=self.app.change_box_color
        )
        self.buttons['color'].pack(side=tk.LEFT, padx=5, pady=5)
        
        # Separador
        separator = tk.Frame(self.toolbar, width=2, bg="gray")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Botões de seleção múltipla
        self.buttons['select_all'] = tk.Button(
            self.toolbar, 
            text="Sel. Tudo (Ctrl+A)", 
            command=self.app.select_all
        )
        self.buttons['select_all'].pack(side=tk.LEFT, padx=5, pady=5)
        
        self.buttons['clear_selection'] = tk.Button(
            self.toolbar, 
            text="Limpar Sel. (Esc)", 
            command=self.app.clear_selection
        )
        self.buttons['clear_selection'].pack(side=tk.LEFT, padx=5, pady=5)
    
    def reset_all_buttons(self):
        """Reseta todos os botões da barra de ferramentas."""
        for button in self.buttons.values():
            if button != self.buttons['select_all'] and button != self.buttons['clear_selection'] and button != self.buttons['color']:
                button.config(relief=tk.RAISED)
    
    def set_active_mode(self, mode):
        """Define qual botão está ativo baseado no modo."""
        self.reset_all_buttons()
        
        if mode in self.buttons:
            self.buttons[mode].config(relief=tk.SUNKEN)
    
    def get_toolbar_height(self):
        """Retorna a altura da barra de ferramentas."""
        return self.toolbar.winfo_reqheight() if self.toolbar else 0