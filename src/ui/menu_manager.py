"""
Gerenciador de menus para a interface do VisionMap
"""

import tkinter as tk


class MenuManager:
    """Classe que gerencia os menus da aplicação."""
    
    def __init__(self, app):
        self.app = app
        self.create_menu()
    
    def create_menu(self):
        """Cria o menu da aplicação."""
        menubar = tk.Menu(self.app.root)
        
        # Menu Arquivo
        self._create_file_menu(menubar)
        
        # Menu Inserir
        self._create_insert_menu(menubar)
        
        # Menu Editar
        self._create_edit_menu(menubar)
        
        # Menu Canvas
        self._create_canvas_menu(menubar)
        
        # Menu Ajuda
        self._create_help_menu(menubar)
        
        self.app.root.config(menu=menubar)
    
    def _create_file_menu(self, menubar):
        """Cria o menu Arquivo."""
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo", command=self.app.new_visionmap, accelerator="Ctrl+N")
        file_menu.add_command(label="Abrir", command=self.app.open_visionmap, accelerator="Ctrl+O")
        file_menu.add_command(label="Salvar", command=self.app.save_visionmap, accelerator="Ctrl+S")
        file_menu.add_command(label="Salvar Como", command=self.app.save_as_visionmap)
        file_menu.add_separator()
        file_menu.add_command(label="Importar do Mermaid", command=self.app.import_from_mermaid)
        file_menu.add_command(label="Exportar como Imagem", command=self.app.export_image)
        file_menu.add_command(label="Exportar como Mermaid", command=self.app.export_mermaid)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.app.root.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
    
    def _create_insert_menu(self, menubar):
        """Cria o menu Inserir."""
        insert_menu = tk.Menu(menubar, tearoff=0)
        insert_menu.add_command(label="Nova Caixa (B)", command=self.app.set_add_box_mode)
        insert_menu.add_command(label="Nova Anotação (C)", command=self.app.set_add_note_mode)
        insert_menu.add_command(label="Novo Container (D)", command=self.app.set_add_container_mode)
        menubar.add_cascade(label="Inserir", menu=insert_menu)
    
    def _create_edit_menu(self, menubar):
        """Cria o menu Editar."""
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Selecionar (A)", command=self.app.set_select_mode)
        edit_menu.add_command(label="Conectar Elementos (E)", command=self.app.set_connect_mode)
        edit_menu.add_separator()
        edit_menu.add_command(label="Selecionar Tudo", command=self.app.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Limpar Seleção", command=self.app.clear_selection, accelerator="Esc")
        edit_menu.add_separator()
        edit_menu.add_command(label="Editar Item", command=self.app.edit_selected)
        edit_menu.add_command(label="Trocar Cor (F)", command=self.app.change_box_color)
        edit_menu.add_command(label="Excluir Item", command=self.app.delete_selected, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="Trazer para Frente (G)", command=self.app.bring_selected_to_front)
        edit_menu.add_command(label="Enviar para Trás (H)", command=self.app.send_selected_to_back)
        menubar.add_cascade(label="Editar", menu=edit_menu)
    
    def _create_canvas_menu(self, menubar):
        """Cria o menu Canvas."""
        canvas_menu = tk.Menu(menubar, tearoff=0)
        canvas_menu.add_command(label="Aumentar Tamanho do Canvas", command=lambda: self._resize_canvas(1.5))
        canvas_menu.add_command(label="Diminuir Tamanho do Canvas", command=lambda: self._resize_canvas(0.75))
        canvas_menu.add_command(label="Redefinir Tamanho do Canvas", command=lambda: self._resize_canvas(1.0, reset=True))
        canvas_menu.add_separator()
        canvas_menu.add_command(label="Centralizar Visão", command=self._center_canvas_view)
        canvas_menu.add_command(label="Ajustar Canvas ao Conteúdo", command=self._fit_canvas_to_content)
        menubar.add_cascade(label="Canvas", menu=canvas_menu)
    
    def _create_help_menu(self, menubar):
        """Cria o menu Ajuda."""
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Sobre", command=self.app.show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
    
    def _resize_canvas(self, scale_factor, reset=False):
        """Redimensiona o canvas pelo fator de escala fornecido."""
        if reset:
            self.app.canvas_width = 3000
            self.app.canvas_height = 2000
        else:
            self.app.canvas_width = int(self.app.canvas_width * scale_factor)
            self.app.canvas_height = int(self.app.canvas_height * scale_factor)
        
        self.app.canvas.config(scrollregion=(0, 0, self.app.canvas_width, self.app.canvas_height))
        self.app.statusbar.config(text=f"Tamanho do canvas ajustado para {self.app.canvas_width}x{self.app.canvas_height}")
    
    def _center_canvas_view(self):
        """Centraliza a visão do canvas."""
        x1, y1, x2, y2 = self.app.canvas.cget("scrollregion").split()
        width = float(x2) - float(x1)
        height = float(y2) - float(y1)
        
        x_center = width / 2
        y_center = height / 2
        
        self.app.canvas.xview_moveto((x_center - self.app.canvas.winfo_width() / 2) / width)
        self.app.canvas.yview_moveto((y_center - self.app.canvas.winfo_height() / 2) / height)
        
        self.app.statusbar.config(text="Visão centralizada")
    
    def _fit_canvas_to_content(self):
        """Ajusta o tamanho do canvas para acomodar todo o conteúdo atual."""
        from tkinter import messagebox
        
        if not (self.app.boxes or self.app.containers):
            messagebox.showinfo("Ajustar Canvas", "Não há conteúdo para ajustar o canvas.")
            return
            
        all_items = self.app.boxes + self.app.containers
        x_min = min([item.x - item.width/2 for item in all_items])
        y_min = min([item.y - item.height/2 for item in all_items])
        x_max = max([item.x + item.width/2 for item in all_items])
        y_max = max([item.y + item.height/2 for item in all_items])
        
        margin = 500
        x_min = max(0, x_min - margin)
        y_min = max(0, y_min - margin)
        x_max += margin
        y_max += margin
        
        self.app.canvas_width = max(3000, int(x_max))
        self.app.canvas_height = max(2000, int(y_max))
        
        self.app.canvas.config(scrollregion=(0, 0, self.app.canvas_width, self.app.canvas_height))
        
        self.app.statusbar.config(text=f"Canvas ajustado para acomodar todo o conteúdo: {self.app.canvas_width}x{self.app.canvas_height}")