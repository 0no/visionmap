"""
Modelo para conexões entre elementos no VisionMap
"""

import tkinter as tk
from tkinter import simpledialog
import math


class Connection:
    """Classe que representa uma conexão entre duas entidades (caixas ou containers)."""
    
    def __init__(self, canvas, obj1, obj2, label_text=""):
        self.canvas = canvas
        self.obj1 = obj1
        self.obj2 = obj2
        self.label_text = label_text
        # Definir se a conexão tem seta ou não (por padrão, tem seta)
        self.arrow = True
        
        # Adicionar esta conexão às listas de conexões
        if hasattr(obj1, 'connections'):
            obj1.connections.append(self)
        
        if hasattr(obj2, 'connections'):
            obj2.connections.append(self)
        
        # Criar a linha no canvas
        self.line = self.canvas.create_line(
            self.obj1.x, self.obj1.y,
            self.obj2.x, self.obj2.y,
            width=2, fill="gray", arrow=tk.LAST if self.arrow else None
        )
        
        # Texto da conexão (inicialmente vazio)
        self.text_id = None
        if label_text:
            self.create_label()
        
        # Área de detecção de clique (width maior para facilitar o clique)
        self.click_width = 6  # Largura da área clicável
        
        self.update()
    
    def update(self):
        """Atualiza a posição da linha de conexão."""
        try:
            # Verificar se os objetos conectados ainda existem
            if not hasattr(self.obj1, 'x') or not hasattr(self.obj2, 'x'):
                return
                
            # Calcular os pontos de intersecção com as bordas
            start_x, start_y = self.calculate_intersection(self.obj1, self.obj2)
            end_x, end_y = self.calculate_intersection(self.obj2, self.obj1)
            
            # Atualizar a linha
            self.canvas.coords(self.line, start_x, start_y, end_x, end_y)
            
            # Garantir que as propriedades da linha (incluindo a seta) sejam mantidas
            self.canvas.itemconfig(self.line, arrow=tk.LAST if self.arrow else None)
            
            # Atualizar posição do rótulo, se houver
            if self.text_id:
                self.create_label()  # Recria o rótulo na nova posição
        except (AttributeError, tk.TclError, ValueError) as e:
            print(f"Erro ao atualizar conexão: {e}")
            return
    
    def set_arrow(self, has_arrow):
        """Define se a conexão tem seta ou não."""
        self.arrow = has_arrow
        self.canvas.itemconfig(self.line, arrow=tk.LAST if has_arrow else None)
        
    def is_clicked(self, event_x, event_y):
        """Verifica se o ponto (event_x, event_y) está sobre a linha de conexão."""
        # Obter as coordenadas atuais da linha
        try:
            coords = self.canvas.coords(self.line)
            if not coords or len(coords) < 4:
                return False
                
            x1, y1, x2, y2 = coords
        except (IndexError, ValueError, tk.TclError):
            return False
        
        # Caso especial: linha vertical
        if x2 - x1 == 0:
            # Verifica se o ponto está próximo da linha vertical
            if abs(event_x - x1) <= self.click_width and min(y1, y2) <= event_y <= max(y1, y2):
                return True
            return False
            
        # Caso especial: linha horizontal
        if y2 - y1 == 0:
            # Verifica se o ponto está próximo da linha horizontal
            if abs(event_y - y1) <= self.click_width and min(x1, x2) <= event_x <= max(x1, x2):
                return True
            return False
        
        # Cálculo da distância para outros casos
        numerador = abs((y2 - y1) * event_x - (x2 - x1) * event_y + x2 * y1 - y2 * x1)
        denominador = ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5
        
        distancia = numerador / denominador
        
        # Verifica se o ponto está dentro do retângulo delimitado pelos pontos extremos
        dentro_retangulo = (min(x1, x2) - self.click_width <= event_x <= max(x1, x2) + self.click_width and 
                            min(y1, y2) - self.click_width <= event_y <= max(y1, y2) + self.click_width)
        
        return distancia <= self.click_width and dentro_retangulo
    
    def calculate_intersection(self, obj_from, obj_to):
        """Calcula o ponto de intersecção da linha com a borda do objeto."""
        # Vetor da linha
        dx = obj_to.x - obj_from.x
        dy = obj_to.y - obj_from.y
        
        # Verificar se é um Container e ajustar a intersecção para considerar a barra de título
        from .container import Container
        title_height = getattr(obj_from, 'title_height', 0) if isinstance(obj_from, Container) else 0
        
        # Determinar qual borda a linha atravessa
        if abs(dx) * obj_from.height > abs(dy) * obj_from.width:
            # Borda esquerda ou direita
            s = 1 if dx > 0 else -1
            x = obj_from.x + s * obj_from.width / 2
            slope = dy / dx if dx != 0 else float('inf')
            y = obj_from.y + slope * (x - obj_from.x)
            
            # Se for um container, verificar se estamos intersectando na barra de título
            if isinstance(obj_from, Container) and y < obj_from.y - obj_from.height/2 + title_height:
                # Ajustar para a borda da barra de título
                y = obj_from.y - obj_from.height/2 + title_height
                if dx != 0:
                    x = obj_from.x + (y - obj_from.y) / slope
        else:
            # Borda superior ou inferior
            s = 1 if dy > 0 else -1
            
            # Se for um container e estamos saindo pela borda superior, considerar a barra de título
            if isinstance(obj_from, Container) and s < 0:
                y = obj_from.y - obj_from.height/2 + title_height
            else:
                y = obj_from.y + s * obj_from.height / 2
            
            slope_inv = dx / dy if dy != 0 else float('inf')
            x = obj_from.x + slope_inv * (y - obj_from.y)
        
        return x, y
    
    def create_label(self):
        """Cria ou atualiza o texto do rótulo da conexão."""
        try:
            # Se já existe um rótulo, removê-lo primeiro
            if self.text_id:
                # Remover também o fundo do texto se existir
                try:
                    self.canvas.delete(f"conn_label_bg_{id(self)}")
                    self.canvas.delete(self.text_id)
                except tk.TclError:
                    pass
                
            if not self.label_text:
                self.text_id = None
                return
                
            # Calcular ponto médio da linha
            coords = self.canvas.coords(self.line)
            if not coords or len(coords) < 4:
                return
                
            x1, y1, x2, y2 = coords
        except (IndexError, ValueError, tk.TclError):
            self.text_id = None
            return
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Pequeno deslocamento para evitar que o texto fique exatamente sobre a linha
        angle = math.atan2(y2 - y1, x2 - x1)
        offset = 10  # Deslocamento perpendicular à linha
        offset_x = -offset * math.sin(angle)
        offset_y = offset * math.cos(angle)
        
        # Criar texto no canvas sem fundo para transparência
        self.text_id = self.canvas.create_text(
            mid_x + offset_x, mid_y + offset_y,
            text=self.label_text, font=("Arial", 8),
            fill="black", tags=f"conn_label_{id(self)}"
        )
        
        # Garantir que o texto fique acima da linha
        self.canvas.tag_raise(self.text_id)
    
    def edit_label(self):
        """Edita o texto do rótulo da conexão."""
        new_text = simpledialog.askstring("Editar Rótulo", "Digite o texto para o rótulo da conexão:", 
                                         initialvalue=self.label_text)
        if new_text is not None:  # Se não cancelou o diálogo
            self.label_text = new_text
            self.create_label()
    
    def delete(self):
        """Remove a conexão."""
        # Remover das listas de conexões
        if hasattr(self.obj1, 'connections') and self in self.obj1.connections:
            self.obj1.connections.remove(self)
        
        if hasattr(self.obj2, 'connections') and self in self.obj2.connections:
            self.obj2.connections.remove(self)
        
        # Remover o texto da conexão, se houver
        if self.text_id:
            self.canvas.delete(self.text_id)
            
        # Remover qualquer item de fundo do texto que possa existir
        try:
            self.canvas.delete(f"conn_label_bg_{id(self)}")
        except:
            pass
        
        # Remover a linha do canvas
        self.canvas.delete(self.line)
    
    def get_state(self):
        """Retorna o estado da conexão para salvamento."""
        # Determinar os tipos dos objetos conectados
        from .container import Container
        obj1_type = 'container' if isinstance(self.obj1, Container) else 'box'
        obj2_type = 'container' if isinstance(self.obj2, Container) else 'box'
        
        return {
            'obj1_id': id(self.obj1),
            'obj2_id': id(self.obj2),
            'obj1_type': obj1_type,
            'obj2_type': obj2_type,
            'label_text': self.label_text
        }