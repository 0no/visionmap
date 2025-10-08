"""
Modelo para caixas de anotação no VisionMap
"""

import tkinter as tk
from tkinter import scrolledtext
from .box import VisionMapBox


class NoteBox(VisionMapBox):
    """Classe que representa uma caixa de anotação com texto expansível no visionmap."""
    
    def __init__(self, canvas, x, y, text="Nova Anotação", width=150, height=80, 
                 fill_color="#FFFFD0", outline_color="#CCCCCC"):
        super().__init__(canvas, x, y, text, width, height, fill_color, outline_color)
        
        # Flag para controle da exibição do texto
        self.text_expanded = False
        
        # Posicionar o botão de expansão no canto superior direito
        button_x = x + width/2 - 10  # Um pouco para dentro da borda
        button_y = y - height/2 + 10  # Um pouco abaixo da borda superior
        button_size = 15
        
        # Criar botão de expansão
        self.toggle_button = canvas.create_rectangle(
            button_x - button_size/2, button_y - button_size/2,
            button_x + button_size/2, button_y + button_size/2,
            fill="#F0F0F0", outline="#CCCCCC"
        )
        
        # Símbolo "+" no botão
        self.toggle_symbol = canvas.create_text(
            button_x, button_y,
            text="+", font=("Arial", 10, "bold")
        )
        
        # Texto completo da anotação
        self.full_text = text
        
        # Caixa de texto expandida (inicialmente oculta)
        self.expanded_text_window = None
        
        # Registrar eventos do botão
        canvas.tag_bind(self.toggle_button, "<Button-1>", self.toggle_text)
        canvas.tag_bind(self.toggle_symbol, "<Button-1>", self.toggle_text)
    
    def bring_to_front(self):
        """Traz a caixa de anotação para a frente (topo das camadas)."""
        # Chamar o método da classe pai
        super().bring_to_front()
        
        # Trazer também os elementos específicos da caixa de anotação
        self.canvas.tag_raise(self.toggle_button)
        self.canvas.tag_raise(self.toggle_symbol)
    
    def send_to_back(self):
        """Envia a caixa de anotação para trás (fundo das camadas)."""
        # Chamar o método da classe pai
        super().send_to_back()
        
        # Enviar também os elementos específicos da caixa de anotação para o fundo
        # Mas deixar os controles visíveis
        self.canvas.tag_raise(self.toggle_button)
        self.canvas.tag_raise(self.toggle_symbol)
    
    def move(self, x, y):
        """Move a caixa de anotação para uma nova posição."""
        # Calcular o deslocamento antes de mover a caixa principal
        dx = x - self.offset_x - self.x
        dy = y - self.offset_y - self.y
        
        # Mover a caixa principal usando o método da classe pai
        super().move(x, y)
        
        # Mover o botão de expansão com o mesmo deslocamento
        self.canvas.move(self.toggle_button, dx, dy)
        self.canvas.move(self.toggle_symbol, dx, dy)
        
        # Se a janela expandida estiver aberta, reposicioná-la também
        if self.expanded_text_window and self.text_expanded:
            self.close_expanded_text()
            self.open_expanded_text()
    
    def toggle_text(self, event=None):
        """Alternar entre exibição resumida e expandida do texto."""
        if self.text_expanded:
            self.close_expanded_text()
        else:
            self.open_expanded_text()
    
    def open_expanded_text(self):
        """Abrir a janela de texto expandido."""
        if self.expanded_text_window:
            return
        
        # Calcular posição da janela de texto
        x, y = self.x + self.width/2 + 10, self.y - self.height/2
        
        # Criar uma nova janela
        self.expanded_text_window = tk.Toplevel()
        self.expanded_text_window.title("Anotação")
        self.expanded_text_window.geometry(f"300x200+{int(self.canvas.winfo_rootx() + x)}+{int(self.canvas.winfo_rooty() + y)}")
        
        # Adicionar widget de texto com scroll
        self.text_widget = scrolledtext.ScrolledText(self.expanded_text_window, wrap=tk.WORD)
        self.text_widget.insert(tk.INSERT, self.full_text)
        self.text_widget.pack(expand=True, fill=tk.BOTH)
        
        # Adicionar binding para Ctrl+S para salvar
        self.text_widget.bind("<Control-s>", lambda event: self.save_text())
        
        # Botão para salvar alterações
        save_frame = tk.Frame(self.expanded_text_window)
        save_frame.pack(fill=tk.X)
        
        save_button = tk.Button(save_frame, text="Salvar", command=self.save_text)
        save_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Botão para aplicar e fechar
        apply_close_button = tk.Button(save_frame, text="Aplicar e Fechar", 
                                     command=lambda: (self.save_text(), self.close_expanded_text()))
        apply_close_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Configurar evento de fechamento
        self.expanded_text_window.protocol("WM_DELETE_WINDOW", self.close_expanded_text)
        
        # Focar no widget de texto
        self.text_widget.focus_set()
        
        # Atualizar símbolo do botão
        self.canvas.itemconfig(self.toggle_symbol, text="−")
        
        self.text_expanded = True
    
    def close_expanded_text(self):
        """Fechar a janela de texto expandido."""
        if self.expanded_text_window:
            # Salvar o texto antes de fechar a janela
            if hasattr(self, 'text_widget') and self.text_widget:
                self.save_text()
            
            self.expanded_text_window.destroy()
            self.expanded_text_window = None
        
        # Restaurar o símbolo do botão
        self.canvas.itemconfig(self.toggle_symbol, text="+")
        
        self.text_expanded = False
    
    def save_text(self):
        """Salvar o texto editado."""
        if self.expanded_text_window and self.text_widget:
            new_text = self.text_widget.get("1.0", tk.END).strip()
            self.full_text = new_text
            
            # Atualizar o resumo na caixa
            summary = self.get_text_summary(new_text)
            self.text = summary
            
            # Atualizar o texto visível no canvas
            self.canvas.itemconfig(self.text_id, text=summary)
            
            # Forçar a atualização do canvas para mostrar o novo texto
            self.canvas.update_idletasks()
    
    def get_text_summary(self, text):
        """Obter um resumo do texto para exibição na caixa."""
        if not text or text.strip() == "":
            return "Nova Anotação"
        
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # Se a primeira linha estiver vazia mas houver outras linhas
        if first_line == "" and len(lines) > 1:
            # Procurar pela primeira linha não vazia
            for line in lines:
                if line.strip() != "":
                    first_line = line.strip()
                    break
        
        # Limitar tamanho e adicionar indicador de texto adicional
        if len(first_line) > 20:
            return first_line[:20] + "..."
        elif len(lines) > 1:
            return first_line + "..."
        else:
            return first_line
    
    def edit_text(self):
        """Editar o texto da anotação."""
        self.open_expanded_text()
    
    def delete(self):
        """Remove a caixa de anotação do canvas."""
        # Fechar qualquer janela de texto expandido primeiro
        self.close_expanded_text()
        
        # Remover elementos específicos da caixa de anotação
        if self.toggle_button:
            self.canvas.delete(self.toggle_button)
            self.toggle_button = None
        
        if self.toggle_symbol:
            self.canvas.delete(self.toggle_symbol)
            self.toggle_symbol = None
        
        # Chamar o método delete da classe pai para remover a caixa base
        super().delete()
    
    def get_state(self):
        """Retorna o estado da caixa de anotação para salvamento."""
        state = super().get_state()
        state.update({
            'full_text': self.full_text,
            'type': 'note'
        })
        return state
    
    @classmethod
    def from_state(cls, canvas, state):
        """Cria uma caixa de anotação a partir de um estado salvo."""
        note_box = cls(
            canvas, 
            state['x'], state['y'],
            state.get('text', 'Nova Anotação'),
            state.get('width', 150), 
            state.get('height', 80),
            state.get('fill_color', "#FFFFD0"),
            state.get('outline_color', "#CCCCCC")
        )
        
        if 'full_text' in state:
            note_box.full_text = state['full_text']
        
        return note_box