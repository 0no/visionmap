"""
Modelo para caixas básicas no VisionMap
"""

import tkinter as tk
from tkinter import simpledialog, colorchooser
from .base import VisualElement


class VisionMapBox(VisualElement):
    """Classe que representa uma caixa básica no visionmap."""
    
    def __init__(self, canvas, x, y, text="Novo Item", width=100, height=50, 
                 fill_color="lightblue", outline_color="#CCCCCC"):
        super().__init__(canvas, x, y, width, height)
        
        self.text = text
        self.fill_color = fill_color
        self.outline_color = outline_color
        
        # Referência ao container pai, se houver
        self.container = None
        
        # Criar a caixa no canvas
        self.rect = canvas.create_rectangle(
            x - width/2, y - height/2, 
            x + width/2, y + height/2,
            fill=self.fill_color, outline=self.outline_color, width=1
        )
        
        # Adicionar texto à caixa
        self.text_id = canvas.create_text(
            x, y, text=text, width=width-10,
            font=("Arial", 10), fill="black"
        )
    
    def update(self):
        """Atualiza a aparência da caixa."""
        self.canvas.itemconfig(self.rect, fill=self.fill_color, outline=self.outline_color)
    
    def move_to(self, x, y):
        """Move a caixa para coordenadas absolutas."""
        dx = x - self.x
        dy = y - self.y
        
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.text_id, dx, dy)
        
        self.x = x
        self.y = y
        
        # Atualizar todas as conexões
        for connection in self.connections:
            connection.update()

    def contains_point(self, x, y):
        """Verifica se um ponto está dentro da caixa."""
        return (self.x - self.width/2 <= x <= self.x + self.width/2 and
                self.y - self.height/2 <= y <= self.y + self.height/2)
    
    def select(self, event_x, event_y):
        """Seleciona a caixa e prepara para movimento."""
        self.selected = True
        self.offset_x = event_x - self.x
        self.offset_y = event_y - self.y
        self.canvas.itemconfig(self.rect, outline="red", width=3)
    
    def deselect(self):
        """Desseleciona a caixa."""
        self.selected = False
        self.canvas.itemconfig(self.rect, outline=self.outline_color, width=2)
        
    def change_color(self):
        """Muda a cor da caixa usando um seletor de cores."""
        color = colorchooser.askcolor(initialcolor=self.fill_color, title="Escolha a cor da caixa")
        if color[1]:  # Se uma cor foi selecionada (não foi cancelado)
            self.fill_color = color[1]
            self.canvas.itemconfig(self.rect, fill=self.fill_color)
    
    def bring_to_front(self):
        """Traz a caixa para a frente (topo das camadas)."""
        # Trazer o retângulo e o texto para a frente
        self.canvas.tag_raise(self.rect)
        self.canvas.tag_raise(self.text_id)
    
    def send_to_back(self):
        """Envia a caixa para trás (fundo das camadas)."""
        # Enviar o retângulo e o texto para o fundo
        self.canvas.tag_lower(self.rect)
        self.canvas.tag_lower(self.text_id)
    
    def move(self, x, y):
        """Move a caixa para uma nova posição."""
        dx = x - self.offset_x - self.x
        dy = y - self.offset_y - self.y
        
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.text_id, dx, dy)
        
        self.x += dx
        self.y += dy
        
        # Atualizar todas as conexões
        for connection in self.connections:
            connection.update()
    
    def edit_text(self):
        """Edita o texto da caixa."""
        new_text = simpledialog.askstring("Editar Texto", "Digite o novo texto:", initialvalue=self.text)
        if new_text:
            self.text = new_text
            self.canvas.itemconfig(self.text_id, text=new_text)
    
    def delete(self):
        """Remove a caixa do canvas."""
        # Remover todas as conexões primeiro
        for conn in list(self.connections):  # Criar uma cópia da lista para iterar
            conn.delete()
        
        # Remover a caixa
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text_id)
        
        # Remover do container, se pertencer a algum
        if self.container:
            self.container.remove_box(self)
    
    def get_state(self):
        """Retorna o estado da caixa para salvamento."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'text': self.text,
            'fill_color': self.fill_color,
            'outline_color': self.outline_color,
            'container_id': id(self.container) if self.container else None
        }
    
    @classmethod
    def from_state(cls, canvas, state, connections_dict=None):
        """Cria uma caixa a partir de um estado salvo."""
        # Verificar se existem cores no estado salvo (para compatibilidade com arquivos antigos)
        fill_color = state.get('fill_color', "lightblue")
        outline_color = state.get('outline_color', "#CCCCCC")
        
        box = cls(canvas, state['x'], state['y'], state['text'], 
                state['width'], state['height'], fill_color, outline_color)
        return box