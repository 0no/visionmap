import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, colorchooser, scrolledtext
import json
import os
import pickle
import math
from PIL import Image, ImageTk

class VisionMapBox:
    """Classe que representa uma caixa no visionmap."""
    def __init__(self, canvas, x, y, text="Novo Item", width=100, height=50, fill_color="lightblue", outline_color="#CCCCCC"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.fill_color = fill_color
        self.outline_color = outline_color
        
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
        
        # Atributos para armazenar o estado de movimento
        self.selected = False
        self.offset_x = 0
        self.offset_y = 0
        
        # Lista de conexões
        self.connections = []
        
        # Referência ao container pai, se houver
        self.container = None
        
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

class Container:
    """Classe que representa um container que pode agrupar várias caixas."""
    def __init__(self, canvas, x, y, width=300, height=200, title="Novo Container", fill_color="#F0F0F0", outline_color="#888888"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.fill_color = fill_color
        self.outline_color = outline_color
        
        # Lista de conexões do container
        self.connections = []
        
        # Criar o retângulo do container
        self.rect = canvas.create_rectangle(
            x - width/2, y - height/2, 
            x + width/2, y + height/2,
            fill=self.fill_color, outline=self.outline_color, width=2
        )
        
        # Adicionar uma barra de título
        self.title_height = 25
        self.title_bar = canvas.create_rectangle(
            x - width/2, y - height/2,
            x + width/2, y - height/2 + self.title_height,
            fill="#DDDDDD", outline=self.outline_color
        )
        
        # Adicionar título
        self.text_id = canvas.create_text(
            x, y - height/2 + self.title_height/2,
            text=title, font=("Arial", 10, "bold"),
            fill="black"
        )
        
        # Armazenar o estado de movimento
        self.selected = False
        self.offset_x = 0
        self.offset_y = 0
        
        # Lista de caixas dentro deste container
        self.boxes = []
        
        # Lista de containers filhos dentro deste container
        self.child_containers = []
        
        # Referência ao container pai, se estiver dentro de outro container
        self.parent_container = None
        
        # Redimensionamento
        self.resize_handle = canvas.create_rectangle(
            x + width/2 - 10, y + height/2 - 10,
            x + width/2, y + height/2,
            fill="#AAAAAA", outline=self.outline_color
        )
        self.resizing = False
    
    def update(self):
        """Atualiza o container para ajustar seu tamanho aos elementos contidos."""
        if not self.boxes:
            return  # Nada para fazer se não houver caixas
            
        # Encontrar as extremidades das caixas contidas
        min_x = min([box.x - box.width/2 for box in self.boxes]) - 20
        min_y = min([box.y - box.height/2 for box in self.boxes]) - 20
        max_x = max([box.x + box.width/2 for box in self.boxes]) + 20
        max_y = max([box.y + box.height/2 for box in self.boxes]) + 20
        
        # Ajustar o tamanho do container
        new_width = max(300, max_x - min_x)
        new_height = max(200, max_y - min_y + self.title_height)
        
        # Ajustar a posição central
        new_center_x = min_x + new_width/2
        new_center_y = min_y + new_height/2 - self.title_height/2
        
        # Mover para a nova posição e ajustar o tamanho
        self.move_to(new_center_x, new_center_y)
        self.resize_to(new_width, new_height)
    
    def move_to(self, x, y):
        """Move o container para coordenadas absolutas."""
        dx = x - self.x
        dy = y - self.y
        
        # Mover os elementos visuais do container
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.title_bar, dx, dy)
        self.canvas.move(self.text_id, dx, dy)
        self.canvas.move(self.resize_handle, dx, dy)
        
        # Atualizar as coordenadas
        self.x = x
        self.y = y
        
        # Mover todas as caixas dentro do container
        for box in self.boxes:
            # Atualizar as coordenadas da caixa
            box.x += dx
            box.y += dy
            
            # Mover os elementos visuais da caixa
            self.canvas.move(box.rect, dx, dy)
            self.canvas.move(box.text_id, dx, dy)
            
            # Se for uma caixa de anotação, mover os elementos adicionais
            if isinstance(box, NoteBox):
                self.canvas.move(box.toggle_button, dx, dy)
                self.canvas.move(box.toggle_symbol, dx, dy)
            
            # Atualizar todas as conexões da caixa
            for connection in box.connections:
                connection.update()
        
        # Mover todos os containers filhos
        if hasattr(self, 'child_containers') and self.child_containers:  # Verifica se o atributo existe e não está vazio
            # Criar um conjunto para rastrear os containers já processados para evitar loops infinitos
            processed = set()
            processed.add(self)  # Adiciona a si mesmo ao conjunto de processados
            
            for child_container in list(self.child_containers):  # Usamos uma cópia da lista para evitar problemas durante a iteração
                # Verificações de segurança para evitar recursão infinita
                if child_container is None or child_container == self or id(child_container) in processed:
                    continue
                    
                # Marcar este container como processado
                processed.add(id(child_container))
                
                # Usar move_to para mover recursivamente containers filhos
                new_x = child_container.x + dx
                new_y = child_container.y + dy
                
                # Mover elementos visuais do container filho diretamente, sem recursão
                child_container.canvas.move(child_container.rect, dx, dy)
                child_container.canvas.move(child_container.title_bar, dx, dy)
                child_container.canvas.move(child_container.text_id, dx, dy)
                child_container.canvas.move(child_container.resize_handle, dx, dy)
                
                # Atualizar coordenadas
                child_container.x = new_x
                child_container.y = new_y
                
                # Mover as caixas dentro do container filho
                for box in child_container.boxes:
                    box.x += dx
                    box.y += dy
                    child_container.canvas.move(box.rect, dx, dy)
                    child_container.canvas.move(box.text_id, dx, dy)
                    
                    # Se for uma caixa de anotação, mover os elementos adicionais
                    if isinstance(box, NoteBox):
                        child_container.canvas.move(box.toggle_button, dx, dy)
                        child_container.canvas.move(box.toggle_symbol, dx, dy)
                        
                    # Atualizar conexões da caixa
                    for connection in box.connections:
                        connection.update()
                
                # Atualizar as conexões do container filho
                if hasattr(child_container, 'connections'):
                    for connection in child_container.connections:
                        connection.update()
        
        # Atualizar todas as conexões do próprio container
        for connection in self.connections:
            connection.update()
        
        # Verificar se há conexões entre containers filhos que também precisam ser atualizadas
        self.update_all_connections()
    
    def resize_to(self, width, height):
        """Redimensiona o container para as dimensões especificadas."""
        # Atualizar as dimensões
        self.width = width
        self.height = height
        
        # Atualizar os elementos visuais do container
        self.canvas.coords(
            self.rect,
            self.x - self.width/2, self.y - self.height/2,
            self.x + self.width/2, self.y + self.height/2
        )
        
        self.canvas.coords(
            self.title_bar,
            self.x - self.width/2, self.y - self.height/2,
            self.x + self.width/2, self.y - self.height/2 + self.title_height
        )
        
        self.canvas.coords(
            self.resize_handle,
            self.x + self.width/2 - 10, self.y + self.height/2 - 10,
            self.x + self.width/2, self.y + self.height/2
        )

    def contains_point(self, x, y):
        """Verifica se um ponto está dentro do container."""
        return (self.x - self.width/2 <= x <= self.x + self.width/2 and
                self.y - self.height/2 <= y <= self.y + self.height/2)
    
    def is_on_title_bar(self, x, y):
        """Verifica se um ponto está na barra de título."""
        return (self.x - self.width/2 <= x <= self.x + self.width/2 and
                self.y - self.height/2 <= y <= self.y - self.height/2 + self.title_height)

    def is_on_resize_handle(self, x, y):
        """Verifica se um ponto está no manipulador de redimensionamento."""
        return (self.x + self.width/2 - 10 <= x <= self.x + self.width/2 and
                self.y + self.height/2 - 10 <= y <= self.y + self.height/2)
    
    def select(self, event_x, event_y):
        """Seleciona o container para movimento."""
        self.selected = True
        self.offset_x = event_x - self.x
        self.offset_y = event_y - self.y
        self.canvas.itemconfig(self.rect, outline="red", width=3)
    
    def deselect(self):
        """Desseleciona o container."""
        self.selected = False
        self.canvas.itemconfig(self.rect, outline=self.outline_color, width=2)
    
    def start_resize(self, event_x, event_y):
        """Inicia o redimensionamento do container."""
        self.resizing = True
        self.resize_start_x = event_x
        self.resize_start_y = event_y
        self.resize_start_width = self.width
        self.resize_start_height = self.height
    
    def resize(self, event_x, event_y):
        """Redimensiona o container."""
        if not self.resizing:
            return
        
        # Calcular novas dimensões
        new_width = max(100, self.resize_start_width + (event_x - self.resize_start_x) * 2)
        new_height = max(100, self.resize_start_height + (event_y - self.resize_start_y) * 2)
        
        # Atualizar as dimensões
        dx = (new_width - self.width) / 2
        dy = (new_height - self.height) / 2
        
        self.width = new_width
        self.height = new_height
        
        # Atualizar os elementos visuais do container
        self.canvas.coords(
            self.rect,
            self.x - self.width/2, self.y - self.height/2,
            self.x + self.width/2, self.y + self.height/2
        )
        
        self.canvas.coords(
            self.title_bar,
            self.x - self.width/2, self.y - self.height/2,
            self.x + self.width/2, self.y - self.height/2 + self.title_height
        )
        
        self.canvas.coords(
            self.text_id,
            self.x, self.y - self.height/2 + self.title_height/2
        )
        
        self.canvas.coords(
            self.resize_handle,
            self.x + self.width/2 - 10, self.y + self.height/2 - 10,
            self.x + self.width/2, self.y + self.height/2
        )
    
    def end_resize(self):
        """Termina o redimensionamento."""
        self.resizing = False
    
    def move(self, x, y):
        """Move o container e todas as caixas dentro dele."""
        dx = x - self.offset_x - self.x
        dy = y - self.offset_y - self.y
        
        # Calcular a nova posição
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Usar o método move_to que já inclui o movimento de containers filhos
        self.move_to(new_x, new_y)
    
    def update_all_connections(self):
        """Atualiza todas as conexões relacionadas a este container e seus filhos."""
        # Atualizar as conexões diretas deste container
        for connection in self.connections:
            connection.update()
        
        # Atualizar recursivamente para todos os containers filhos
        if hasattr(self, 'child_containers') and self.child_containers:
            processed = set([id(self)])  # Evitar loops infinitos
            
            for child in self.child_containers:
                if child is not None and id(child) not in processed:
                    processed.add(id(child))
                    
                    # Atualizar conexões deste container filho
                    if hasattr(child, 'connections'):
                        for connection in child.connections:
                            connection.update()
                            
                    # Procurar recursivamente em níveis mais profundos
                    if hasattr(child, 'update_all_connections'):
                        child.update_all_connections()
    
    def add_box(self, box):
        """Adiciona uma caixa ao container."""
        if box not in self.boxes:
            self.boxes.append(box)
            box.container = self  # Definir a referência do container na caixa
    
    def remove_box(self, box):
        """Remove uma caixa do container."""
        if box in self.boxes:
            self.boxes.remove(box)
            box.container = None  # Remover a referência do container na caixa
    
    def contains_box(self, box):
        """Verifica se uma caixa está totalmente dentro do container."""
        return (box.x - box.width/2 >= self.x - self.width/2 and
                box.x + box.width/2 <= self.x + self.width/2 and
                box.y - box.height/2 >= self.y - self.height/2 + self.title_height and
                box.y + box.height/2 <= self.y + self.height/2)
                
    def contains_container(self, container):
        """Verifica se um container está totalmente dentro deste container."""
        if container == self:  # Um container não pode conter a si mesmo
            return False
            
        # Verificação mais tolerante - considera que o container está dentro
        # se ao menos 75% da sua área estiver dentro do container pai
        center_inside = (container.x >= self.x - self.width/2 and
                         container.x <= self.x + self.width/2 and
                         container.y >= self.y - self.height/2 + self.title_height and
                         container.y <= self.y + self.height/2)
        
        fully_inside = (container.x - container.width/2 >= self.x - self.width/2 and
                        container.x + container.width/2 <= self.x + self.width/2 and
                        container.y - container.height/2 >= self.y - self.height/2 + self.title_height and
                        container.y + container.height/2 <= self.y + self.height/2)
        
        # Para containers pequenos dentro de containers grandes, usamos verificação completa
        if container.width < self.width*0.75 and container.height < self.height*0.75:
            return fully_inside
            
        # Para containers de tamanho semelhante, apenas verificamos se o centro está dentro
        return center_inside
                
    def add_child_container(self, container):
        """Adiciona um container filho a este container."""
        # Garante que o atributo child_containers existe
        if not hasattr(self, 'child_containers'):
            self.child_containers = []
            
        # Verificações de segurança
        # Evita adicionar o mesmo container ou criar uma recursão
        if container in self.child_containers or container == self:
            return False
            
        # Verificar se essa operação criaria um ciclo
        # (exemplo: se o container que estamos adicionando é pai deste container)
        current = self
        visited = set()
        
        while current and hasattr(current, 'parent_container'):
            if current == container:
                # Isso criaria um ciclo, então não permitimos
                print(f"AVISO: Tentativa de criar ciclo de containers detectada! {container.title} -> {self.title}")
                return False
                
            # Verificar se já visitamos este container (ciclo existente)
            if current in visited:
                break
                
            visited.add(current)
            current = current.parent_container
        
        # A operação é segura, podemos prosseguir
        # Verifica se o container já tem um pai
        if hasattr(container, 'parent_container') and container.parent_container:
            # Remove do pai atual antes de adicionar ao novo
            container.parent_container.remove_child_container(container)
            
        # Adiciona à lista de containers filhos
        self.child_containers.append(container)
        
        # Define a referência ao container pai
        container.parent_container = self
        
        # Debug na console
        print(f"Container '{container.title}' adicionado como filho de '{self.title}'")
        return True
            
    def remove_child_container(self, container):
        """Remove um container filho deste container."""
        # Garante que o atributo child_containers existe
        if not hasattr(self, 'child_containers'):
            self.child_containers = []
            return
            
        if container in self.child_containers:
            self.child_containers.remove(container)
            container.parent_container = None  # Remover a referência ao container pai
            
            # Debug na console
            print(f"Container '{container.title}' removido como filho de '{self.title}'")
    
    def edit_title(self):
        """Edita o título do container."""
        new_title = simpledialog.askstring("Editar Título", "Digite o novo título:", initialvalue=self.title)
        if new_title:
            self.title = new_title
            self.canvas.itemconfig(self.text_id, text=new_title)
    
    def change_color(self):
        """Muda a cor do container usando um seletor de cores."""
        color = colorchooser.askcolor(initialcolor=self.fill_color, title="Escolha a cor do container")
        if color[1]:  # Se uma cor foi selecionada (não foi cancelado)
            self.fill_color = color[1]
            self.canvas.itemconfig(self.rect, fill=self.fill_color)
    
    def bring_to_front(self):
        """Traz o container para a frente (topo das camadas)."""
        # Trazer todos os elementos visuais do container para a frente
        self.canvas.tag_raise(self.rect)
        self.canvas.tag_raise(self.title_bar)
        self.canvas.tag_raise(self.text_id)
        self.canvas.tag_raise(self.resize_handle)
        
        # Opcionalmente, trazer também as caixas contidas nele para a frente
        for box in self.boxes:
            box.bring_to_front()
    
    def send_to_back(self):
        """Envia o container para trás (fundo das camadas)."""
        # Enviar todos os elementos visuais do container para o fundo
        # Primeiro as caixas contidas, se desejarmos que elas fiquem visíveis acima do container
        for box in self.boxes:
            box.bring_to_front()
            
        # Depois os elementos do container
        self.canvas.tag_lower(self.rect)
        self.canvas.tag_lower(self.title_bar)
        
        # Manter o texto e o manipulador de redimensionamento acima para serem visíveis
        self.canvas.tag_raise(self.text_id)
        self.canvas.tag_raise(self.resize_handle)
    
    def delete(self):
        """Remove o container do canvas."""
        # Remover todas as conexões primeiro
        for conn in list(self.connections):  # Criar uma cópia da lista para iterar
            conn.delete()
        
        # Remover a referência de container de todas as caixas dentro dele
        for box in list(self.boxes):  # Usar uma cópia para evitar problemas durante a iteração
            box.container = None
        
        # Remover a referência de container pai de todos os containers filhos
        for child_container in list(self.child_containers):
            child_container.parent_container = None
        
        # Se este container tem um pai, removê-lo da lista de filhos do pai
        if self.parent_container:
            self.parent_container.remove_child_container(self)
        
        # Limpar a lista de caixas e containers filhos
        self.boxes.clear()
        self.child_containers.clear()
        
        # Remover os elementos visuais do container
        self.canvas.delete(self.rect)
        self.canvas.delete(self.title_bar)
        self.canvas.delete(self.text_id)
        self.canvas.delete(self.resize_handle)
    
    def get_state(self):
        """Retorna o estado do container para salvamento."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'title': self.title,
            'fill_color': self.fill_color,
            'outline_color': self.outline_color,
            'type': 'container',
            'parent_container_id': id(self.parent_container) if self.parent_container else None
        }
    
    @classmethod
    def from_state(cls, canvas, state):
        """Cria um container a partir de um estado salvo."""
        container = cls(
            canvas, 
            state['x'], state['y'],
            state.get('width', 300), 
            state.get('height', 200),
            state.get('title', 'Novo Container'),
            state.get('fill_color', "#F0F0F0"),
            state.get('outline_color', "#888888")
        )
        
        # A vinculação ao container pai será feita posteriormente pelo método open_from_file
        
        return container

class NoteBox(VisionMapBox):
    """Classe que representa uma caixa de anotação com texto expansível no visionmap."""
    def __init__(self, canvas, x, y, text="Nova Anotação", width=150, height=80, fill_color="#FFFFD0", outline_color="#CCCCCC"):
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
        obj1_type = 'container' if isinstance(self.obj1, Container) else 'box'
        obj2_type = 'container' if isinstance(self.obj2, Container) else 'box'
        
        return {
            'obj1_id': id(self.obj1),
            'obj2_id': id(self.obj2),
            'obj1_type': obj1_type,
            'obj2_type': obj2_type,
            'label_text': self.label_text
        }

class VisionMapApp:
    """Aplicativo principal de visionmap."""
    def __init__(self, root):
        self.root = root
        self.root.title("VisionMap Creator")
        self.root.geometry("1000x700")
        
        # Configurar eventos de redimensionamento
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Agendar verificação periódica de relacionamentos entre containers
        self.root.after(1000, self.check_container_relationships)
        
        # Definir o ícone da aplicação
        try:
            # Carrega a imagem usando PIL
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                logo_image = Image.open(logo_path)
                logo_photo = ImageTk.PhotoImage(logo_image)
                
                # Define o ícone da janela
                self.root.iconphoto(True, logo_photo)
                
                # Mantém uma referência para evitar que seja coletada pelo garbage collector
                self.logo_photo = logo_photo
            else:
                print(f"Arquivo de logo não encontrado: {logo_path}")
        except Exception as e:
            print(f"Erro ao carregar o ícone: {e}")
        
        # Frame principal
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Criar o menu
        self.create_menu()
        
        # Frame para o canvas e a barra de ferramentas
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de ferramentas
        self.toolbar = tk.Frame(self.canvas_frame, bg="lightgray", height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Botões da barra de ferramentas
        self.create_toolbar()
        
        # Criar um frame para o canvas com barras de rolagem
        self.canvas_container = tk.Frame(self.canvas_frame)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Definir o tamanho inicial do canvas (pode ser maior que a janela visível)
        self.canvas_width = 3000  # Tamanho inicial horizontal do canvas
        self.canvas_height = 2000  # Tamanho inicial vertical do canvas
        
        # Criar barras de rolagem
        self.h_scrollbar = tk.Scrollbar(self.canvas_container, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = tk.Scrollbar(self.canvas_container)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Criar o canvas com barras de rolagem
        self.canvas = tk.Canvas(self.canvas_container, bg="white",
                               scrollregion=(0, 0, self.canvas_width, self.canvas_height),
                               xscrollcommand=self.h_scrollbar.set,
                               yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Configurar barras de rolagem para controlar o canvas
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Permitir zoom com a roda do mouse
        self.canvas.bind("<Control-MouseWheel>", self.on_mouse_wheel)
        
        # Barra de status
        self.statusbar = tk.Label(self.main_frame, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Listas para armazenar caixas, containers e conexões
        self.boxes = []
        self.containers = []
        self.connections = []
        
        # Controlar o estado da aplicação
        self.mode = "select"  # Modos: select, add_box, add_note, add_container, connect
        self.selected_box = None
        self.selected_container = None
        self.selected_connection = None
        self.temp_connection_start = None
        self.resizing_container = None
        
        # Variáveis para controle de navegação do canvas
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Seleção múltipla
        self.selected_boxes = []  # Lista de caixas selecionadas
        self.selected_containers = []  # Lista de containers selecionados
        self.selection_rectangle = None  # Retângulo de seleção
        self.selection_start_x = 0
        self.selection_start_y = 0
        self.is_selecting = False  # Flag para seleção por arrastar
        self.is_moving_multiple = False  # Flag para mover múltiplos objetos
        
        # Controle de movimento múltiplo
        self.initial_positions = []  # Posições iniciais dos elementos
        self.move_start_x = 0  # Posição inicial do mouse X
        self.move_start_y = 0  # Posição inicial do mouse Y
        
        # Binds para eventos do mouse
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_right_click)  # Botão direito para menu de contexto
        
        # Eventos para navegação por arrastar (pan)
        self.canvas.bind("<Button-2>", self.start_pan)  # Botão do meio do mouse para iniciar pan
        self.canvas.bind("<B2-Motion>", self.pan_canvas)  # Arrastar com botão do meio para mover o canvas
        self.canvas.bind("<ButtonRelease-2>", self.stop_pan)  # Soltar botão do meio para parar pan
        
        # Permitir pan com Ctrl+arrastar com botão esquerdo (alternativa para quem não tem botão do meio)
        self.canvas.bind("<Control-Button-1>", self.start_pan)
        self.canvas.bind("<Control-B1-Motion>", self.pan_canvas)
        self.canvas.bind("<Control-ButtonRelease-1>", self.stop_pan)
        
        # Suporte para rolagem com o mouse (Windows e Linux)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux (rolar para cima)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux (rolar para baixo)
        self.canvas.bind("<Control-Button-4>", self.on_mouse_wheel)  # Linux (rolar horizontalmente para cima)
        self.canvas.bind("<Control-Button-5>", self.on_mouse_wheel)  # Linux (rolar horizontalmente para baixo)
        
        # Nome do arquivo atual
        self.current_file = None
        
        # Menu de contexto para elementos (caixas e containers)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Trazer para frente", command=self.bring_selected_to_front)
        self.context_menu.add_command(label="Enviar para trás", command=self.send_selected_to_back)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Editar", command=self.edit_selected)
        self.context_menu.add_command(label="Trocar cor", command=self.change_box_color)
        self.context_menu.add_command(label="Excluir", command=self.delete_selected)
        
        # Menu de contexto para conexões
        self.connection_menu = tk.Menu(self.root, tearoff=0)
        self.connection_menu.add_command(label="Editar Rótulo", command=self.edit_connection_label)
        self.connection_menu.add_separator()
        self.connection_menu.add_command(label="Excluir conexão", command=self.delete_selected_connection)
        
        # Atalhos de teclado - operações de arquivo e edição
        self.root.bind("<Delete>", self.delete_selected)
        self.root.bind("<Control-s>", self.save_visionmap)
        self.root.bind("<Control-o>", self.open_visionmap)
        self.root.bind("<Control-n>", self.new_visionmap)
        
        # Atalhos de teclado para os modos (letras A-H)
        self.root.bind("<a>", lambda event: self.set_select_mode())
        self.root.bind("<A>", lambda event: self.set_select_mode())
        self.root.bind("<b>", lambda event: self.set_add_box_mode())
        self.root.bind("<B>", lambda event: self.set_add_box_mode())
        self.root.bind("<c>", lambda event: self.set_add_note_mode())
        self.root.bind("<C>", lambda event: self.set_add_note_mode())
        self.root.bind("<d>", lambda event: self.set_add_container_mode())
        self.root.bind("<D>", lambda event: self.set_add_container_mode())
        self.root.bind("<e>", lambda event: self.set_connect_mode())
        self.root.bind("<E>", lambda event: self.set_connect_mode())
        self.root.bind("<f>", lambda event: self.change_box_color())
        self.root.bind("<F>", lambda event: self.change_box_color())
        self.root.bind("<g>", lambda event: self.bring_selected_to_front())
        self.root.bind("<G>", lambda event: self.bring_selected_to_front())
        self.root.bind("<h>", lambda event: self.send_selected_to_back())
        self.root.bind("<H>", lambda event: self.send_selected_to_back())
        
        # Atalhos para seleção múltipla
        self.root.bind("<Control-a>", self.select_all)
        self.root.bind("<Escape>", self.clear_selection)
    
    def create_menu(self):
        """Cria o menu da aplicação."""
        menubar = tk.Menu(self.root)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo", command=self.new_visionmap, accelerator="Ctrl+N")
        file_menu.add_command(label="Abrir", command=self.open_visionmap, accelerator="Ctrl+O")
        file_menu.add_command(label="Salvar", command=self.save_visionmap, accelerator="Ctrl+S")
        file_menu.add_command(label="Salvar Como", command=self.save_as_visionmap)
        file_menu.add_separator()
        file_menu.add_command(label="Importar do Mermaid", command=self.import_from_mermaid)
        file_menu.add_command(label="Exportar como Imagem", command=self.export_image)
        file_menu.add_command(label="Exportar como Mermaid", command=self.export_mermaid)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Inserir
        insert_menu = tk.Menu(menubar, tearoff=0)
        insert_menu.add_command(label="Nova Caixa (B)", command=self.set_add_box_mode)
        insert_menu.add_command(label="Nova Anotação (C)", command=self.set_add_note_mode)
        insert_menu.add_command(label="Novo Container (D)", command=self.set_add_container_mode)
        menubar.add_cascade(label="Inserir", menu=insert_menu)
        
        # Menu Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Selecionar (A)", command=self.set_select_mode)
        edit_menu.add_command(label="Conectar Elementos (E)", command=self.set_connect_mode)
        edit_menu.add_separator()
        edit_menu.add_command(label="Selecionar Tudo", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Limpar Seleção", command=self.clear_selection, accelerator="Esc")
        edit_menu.add_separator()
        edit_menu.add_command(label="Editar Item", command=self.edit_selected)
        edit_menu.add_command(label="Trocar Cor (F)", command=self.change_box_color)
        edit_menu.add_command(label="Excluir Item", command=self.delete_selected, accelerator="Delete")
        
        # Menu Canvas
        canvas_menu = tk.Menu(menubar, tearoff=0)
        canvas_menu.add_command(label="Aumentar Tamanho do Canvas", command=lambda: self.resize_canvas(1.5))
        canvas_menu.add_command(label="Diminuir Tamanho do Canvas", command=lambda: self.resize_canvas(0.75))
        canvas_menu.add_command(label="Redefinir Tamanho do Canvas", command=lambda: self.resize_canvas(1.0, reset=True))
        canvas_menu.add_separator()
        canvas_menu.add_command(label="Centralizar Visão", command=self.center_canvas_view)
        canvas_menu.add_command(label="Ajustar Canvas ao Conteúdo", command=self.fit_canvas_to_content)
        menubar.add_cascade(label="Canvas", menu=canvas_menu)
        edit_menu.add_separator()
        edit_menu.add_command(label="Trazer para Frente (G)", command=self.bring_selected_to_front)
        edit_menu.add_command(label="Enviar para Trás (H)", command=self.send_selected_to_back)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Sobre", command=self.show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        """Cria a barra de ferramentas."""
        # Botão de seleção
        self.select_button = tk.Button(self.toolbar, text="Selecionar (A)", 
                                       command=self.set_select_mode)
        self.select_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.select_button.config(relief=tk.SUNKEN)  # Inicialmente ativo
        
        # Botão de adicionar caixa
        self.add_box_button = tk.Button(self.toolbar, text="Adicionar Caixa (B)", 
                                       command=self.set_add_box_mode)
        self.add_box_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão de adicionar anotação
        self.add_note_button = tk.Button(self.toolbar, text="Adicionar Anotação (C)", 
                                      command=self.set_add_note_mode)
        self.add_note_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão de adicionar container
        self.add_container_button = tk.Button(self.toolbar, text="Adicionar Container (D)", 
                                           command=self.set_add_container_mode)
        self.add_container_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão de conectar caixas
        self.connect_button = tk.Button(self.toolbar, text="Conectar (E)", 
                                       command=self.set_connect_mode)
        self.connect_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Botão para trocar a cor da caixa/container selecionado
        self.color_button = tk.Button(self.toolbar, text="Trocar Cor (F)", 
                                     command=self.change_box_color)
        self.color_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Separador
        separator = tk.Frame(self.toolbar, width=2, bg="gray")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Botões de seleção múltipla
        self.select_all_button = tk.Button(self.toolbar, text="Sel. Tudo (Ctrl+A)", 
                                          command=self.select_all)
        self.select_all_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.clear_selection_button = tk.Button(self.toolbar, text="Limpar Sel. (Esc)", 
                                               command=self.clear_selection)
        self.clear_selection_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Separador para ferramentas de debug
        debug_separator = tk.Frame(self.toolbar, width=2, bg="gray")
        debug_separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # # Botão para debug de containers
        # self.debug_containers_button = tk.Button(self.toolbar, text="Debug Containers", 
        #                                       command=self.show_container_debug,
        #                                       bg="#FFE0E0")  # Cor de fundo diferente para destacar
        # self.debug_containers_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def reset_toolbar_buttons(self):
        """Reseta todos os botões da barra de ferramentas."""
        self.select_button.config(relief=tk.RAISED)
        self.add_box_button.config(relief=tk.RAISED)
        self.add_note_button.config(relief=tk.RAISED)
        self.add_container_button.config(relief=tk.RAISED)
        self.connect_button.config(relief=tk.RAISED)
    
    def set_select_mode(self):
        """Ativa o modo de seleção."""
        self.mode = "select"
        self.reset_toolbar_buttons()
        self.select_button.config(relief=tk.SUNKEN)
        self.statusbar.config(text="Modo: Selecionar e mover itens | Ctrl+clique para seleção múltipla | Arrastar para selecionar área")
    
    def set_add_box_mode(self):
        """Ativa o modo de adicionar caixa."""
        self.mode = "add_box"
        self.reset_toolbar_buttons()
        self.add_box_button.config(relief=tk.SUNKEN)
        self.statusbar.config(text="Modo: Adicionar nova caixa")
    
    def set_add_note_mode(self):
        """Ativa o modo de adicionar anotação."""
        self.mode = "add_note"
        self.reset_toolbar_buttons()
        self.add_note_button.config(relief=tk.SUNKEN)
        self.statusbar.config(text="Modo: Adicionar nova anotação")
    
    def set_add_container_mode(self):
        """Ativa o modo de adicionar container."""
        self.mode = "add_container"
        self.reset_toolbar_buttons()
        self.add_container_button.config(relief=tk.SUNKEN)
        self.statusbar.config(text="Modo: Adicionar novo container")
    
    def set_connect_mode(self):
        """Ativa o modo de conectar caixas."""
        self.mode = "connect"
        self.reset_toolbar_buttons()
        self.connect_button.config(relief=tk.SUNKEN)
        self.statusbar.config(text="Modo: Conectar caixas")
    
    def create_container_at(self, x, y, width, height, title="Novo Container"):
        """Cria um container nas coordenadas e dimensões especificadas."""
        # Criar um container diretamente (sem usar o modo de interface)
        container = Container(
            self.canvas, 
            x, y, 
            title=title, 
            width=width, 
            height=height
        )
        
        # Adicionar o container à lista de containers
        self.containers.append(container)
        
        # Inicializar atributos necessários para hierarquia
        if not hasattr(container, 'child_containers'):
            container.child_containers = []
        container.parent_container = None
        
        # Retornar o container criado para permitir manipulação adicional
        return container
        
    def create_box_at(self, x, y, text="Nova Caixa", width=100, height=50, fill_color="lightblue"):
        """Cria uma caixa nas coordenadas especificadas."""
        # Criar uma caixa diretamente (sem usar o modo de interface)
        box = VisionMapBox(
            self.canvas, 
            x, y, 
            text=text, 
            width=width, 
            height=height, 
            fill_color=fill_color
        )
        
        # Adicionar a caixa à lista de caixas
        self.boxes.append(box)
        
        # Retornar a caixa criada para permitir manipulação adicional
        return box
    
    def on_canvas_click(self, event):
        """Manipula o evento de clique no canvas."""
        if self.mode == "add_box":
            # Criar nova caixa
            box = VisionMapBox(self.canvas, event.x, event.y)
            self.boxes.append(box)
            
            # Verificar se a caixa está dentro de algum container
            for container in self.containers:
                if container.contains_box(box):
                    container.add_box(box)
                    break
        
        elif self.mode == "add_note":
            # Criar nova caixa de anotação
            note = NoteBox(self.canvas, event.x, event.y)
            self.boxes.append(note)
            
            # Verificar se a anotação está dentro de algum container
            for container in self.containers:
                if container.contains_box(note):
                    container.add_box(note)
                    break
        
        elif self.mode == "add_container":
            # Criar novo container
            container = Container(self.canvas, event.x, event.y)
            self.containers.append(container)
            
            # Verificar se existem caixas que devem ser adicionadas ao container
            for box in self.boxes:
                if container.contains_box(box):
                    container.add_box(box)
        
        elif self.mode == "select":
            # Verificar se Ctrl está pressionado para seleção múltipla
            ctrl_pressed = (event.state & 0x4) != 0
            
            # Se não está pressionando Ctrl, limpar seleção anterior
            if not ctrl_pressed:
                self.clear_selection()
            
            # Verificar se clicou no manipulador de redimensionamento de algum container
            for container in self.containers:
                if container.is_on_resize_handle(event.x, event.y):
                    self.resizing_container = container
                    container.start_resize(event.x, event.y)
                    return
            
            clicked_on_item = False
            
            # Verificar se clicou na barra de título de algum container
            for container in self.containers:
                if container.is_on_title_bar(event.x, event.y):
                    if ctrl_pressed and self.is_selected_multiple(container):
                        # Se Ctrl pressionado e já está selecionado, remover da seleção
                        self.remove_from_selection(container)
                    else:
                        # Adicionar à seleção ou selecionar único
                        if not ctrl_pressed:
                            self.selected_container = container
                            container.select(event.x, event.y)
                        else:
                            self.add_to_selection(container)
                    clicked_on_item = True
                    return
            
            # Verificar se clicou em uma caixa existente
            for box in self.boxes:
                if box.contains_point(event.x, event.y):
                    if ctrl_pressed and self.is_selected_multiple(box):
                        # Se Ctrl pressionado e já está selecionado, remover da seleção
                        self.remove_from_selection(box)
                    else:
                        # Se clicou em uma caixa que já está na seleção múltipla, preparar movimento
                        if self.is_selected_multiple(box) and (self.selected_boxes or self.selected_containers):
                            # Preparar para mover múltiplos elementos
                            pass  # Não alterar seleção, só preparar movimento
                        elif not ctrl_pressed:
                            # Seleção única
                            self.selected_box = box
                            box.select(event.x, event.y)
                        else:
                            # Adicionar à seleção múltipla
                            self.add_to_selection(box)
                    clicked_on_item = True
                    return
            
            # Verificar se clicou em um container
            for container in self.containers:
                if container.contains_point(event.x, event.y):
                    if ctrl_pressed and self.is_selected_multiple(container):
                        # Se Ctrl pressionado e já está selecionado, remover da seleção
                        self.remove_from_selection(container)
                    else:
                        # Se clicou em um container que já está na seleção múltipla, preparar movimento
                        if self.is_selected_multiple(container) and (self.selected_boxes or self.selected_containers):
                            # Preparar para mover múltiplos elementos
                            pass  # Não alterar seleção, só preparar movimento
                        elif not ctrl_pressed:
                            # Seleção única
                            self.selected_container = container
                            container.select(event.x, event.y)
                        else:
                            # Adicionar à seleção múltipla
                            self.add_to_selection(container)
                    clicked_on_item = True
                    return
            
            # Se não clicou em nenhum item e não está com Ctrl, iniciar seleção por arrastar
            if not clicked_on_item and not ctrl_pressed:
                self.is_selecting = True
                self.selection_start_x = event.x
                self.selection_start_y = event.y
        
        elif self.mode == "connect":
            # Primeiro tentar com caixas
            for box in self.boxes:
                if box.contains_point(event.x, event.y):
                    if not self.temp_connection_start:
                        # Início da conexão
                        self.temp_connection_start = box
                        # Criar linha temporária
                        self.temp_line = self.canvas.create_line(
                            box.x, box.y, box.x, box.y,
                            width=2, fill="gray", dash=(4, 4)
                        )
                        return
            
            # Se não encontrou uma caixa, tentar com containers
            for container in self.containers:
                if container.contains_point(event.x, event.y):
                    if not self.temp_connection_start:
                        # Início da conexão
                        self.temp_connection_start = container
                        # Criar linha temporária
                        self.temp_line = self.canvas.create_line(
                            container.x, container.y, container.x, container.y,
                            width=2, fill="gray", dash=(4, 4)
                        )
                    break
    
    def on_canvas_drag(self, event):
        """Manipula o evento de arrastar no canvas."""
        if self.resizing_container:
            # Redimensionar o container selecionado
            self.resizing_container.resize(event.x, event.y)
        
        elif self.mode == "select":
            if self.is_selecting:
                # Atualizar retângulo de seleção
                if self.selection_rectangle:
                    self.canvas.delete(self.selection_rectangle)
                
                self.selection_rectangle = self.canvas.create_rectangle(
                    self.selection_start_x, self.selection_start_y,
                    event.x, event.y,
                    outline="blue", width=1, dash=(5, 5)
                )
                
            elif self.selected_boxes or self.selected_containers:
                # Mover múltiplos elementos selecionados
                if not self.is_moving_multiple:
                    # Primeira vez que move, calcular offsets e posição de referência
                    self.is_moving_multiple = True
                    self.move_start_x = event.x
                    self.move_start_y = event.y
                    
                    # Armazenar posições iniciais de todos os elementos
                    self.initial_positions = []
                    
                    for box in self.selected_boxes:
                        self.initial_positions.append(('box', box, box.x, box.y))
                    
                    for container in self.selected_containers:
                        self.initial_positions.append(('container', container, container.x, container.y))
                
                # Calcular deslocamento total desde o início do movimento
                dx_total = event.x - self.move_start_x
                dy_total = event.y - self.move_start_y
                
                # Mover todos os elementos com o mesmo deslocamento
                for item_type, item, initial_x, initial_y in self.initial_positions:
                    new_x = initial_x + dx_total
                    new_y = initial_y + dy_total
                    
                    if item_type == 'box':
                        # Calcular deslocamento atual do elemento
                        current_dx = new_x - item.x
                        current_dy = new_y - item.y
                        
                        # Atualizar posição da caixa
                        item.x = new_x
                        item.y = new_y
                        
                        # Mover elementos visuais
                        self.canvas.move(item.rect, current_dx, current_dy)
                        self.canvas.move(item.text_id, current_dx, current_dy)
                        
                        # Se for uma NoteBox, mover elementos adicionais
                        if isinstance(item, NoteBox):
                            self.canvas.move(item.toggle_button, current_dx, current_dy)
                            self.canvas.move(item.toggle_symbol, current_dx, current_dy)
                        
                        # Atualizar conexões
                        for connection in item.connections:
                            connection.update()
                            
                    else:  # container
                        # Para containers, usar move_to que já cuida das caixas internas
                        item.move_to(new_x, new_y)
                
            elif self.selected_box:
                # Mover a caixa selecionada (comportamento original)
                self.selected_box.move(event.x, event.y)
                
                # Se a caixa estava em um container e saiu, removê-la
                if self.selected_box.container:
                    if not self.selected_box.container.contains_box(self.selected_box):
                        self.selected_box.container.remove_box(self.selected_box)
                
                # Verificar se a caixa entrou em algum container
                for container in self.containers:
                    if container.contains_box(self.selected_box) and self.selected_box.container != container:
                        # Se já estava em outro container, remover
                        if self.selected_box.container:
                            self.selected_box.container.remove_box(self.selected_box)
                        # Adicionar ao novo container
                        container.add_box(self.selected_box)
                        break
            
            elif self.selected_container:
                # Verificar se o container selecionado já tem atributos necessários
                if not hasattr(self.selected_container, 'child_containers'):
                    self.selected_container.child_containers = []
                if not hasattr(self.selected_container, 'parent_container'):
                    self.selected_container.parent_container = None
                
                # Salvar a posição atual antes de mover
                old_x = self.selected_container.x
                old_y = self.selected_container.y
                
                # Mover o container selecionado e todas as caixas dentro dele
                self.selected_container.move(event.x, event.y)
                
                # Se o container estava em um container pai e saiu, removê-lo
                if hasattr(self.selected_container, 'parent_container') and self.selected_container.parent_container:
                    old_parent = self.selected_container.parent_container
                    if not old_parent.contains_container(self.selected_container):
                        # Salvar informações do container pai antes de removê-lo
                        parent_title = old_parent.title
                        old_parent.remove_child_container(self.selected_container)
                        self.statusbar.config(text=f"Container '{self.selected_container.title}' removido de '{parent_title}'")
                
                # Verificar se o container entrou em algum outro container
                for container in self.containers:
                    # Garantir que o container de destino tenha os atributos necessários
                    if not hasattr(container, 'child_containers'):
                        container.child_containers = []
                        
                    # Verificar se o container selecionado está dentro de outro container
                    if (container != self.selected_container and 
                        container.contains_container(self.selected_container) and 
                        self.selected_container.parent_container != container):
                        
                        # Se já estava em outro container, remover
                        if self.selected_container.parent_container:
                            self.selected_container.parent_container.remove_child_container(self.selected_container)
                        
                        # Adicionar ao novo container
                        container.add_child_container(self.selected_container)
                        self.statusbar.config(text=f"Container '{self.selected_container.title}' adicionado a '{container.title}'")
                        break
        
        elif self.mode == "connect" and self.temp_connection_start:
            # Atualizar a linha temporária
            self.canvas.coords(
                self.temp_line,
                self.temp_connection_start.x, self.temp_connection_start.y,
                event.x, event.y
            )
    
    def on_canvas_release(self, event):
        """Manipula o evento de soltar o botão do mouse."""
        if self.resizing_container:
            # Finalizar o redimensionamento
            self.resizing_container.end_resize()
            self.resizing_container = None
        
        elif self.mode == "select" and self.is_selecting:
            # Finalizar seleção por arrastar
            if self.selection_rectangle:
                # Obter elementos dentro do retângulo de seleção
                selected_items = self.get_selection_bounds(
                    self.selection_start_x, self.selection_start_y,
                    event.x, event.y
                )
                
                # Adicionar itens à seleção múltipla
                for item in selected_items:
                    self.add_to_selection(item)
                
                # Remover retângulo de seleção
                self.canvas.delete(self.selection_rectangle)
                self.selection_rectangle = None
                
                # Atualizar barra de status
                self.statusbar.config(text=f"Selecionados: {len(self.selected_boxes)} caixas, {len(self.selected_containers)} containers")
            
            self.is_selecting = False
        
        elif self.mode == "select" and self.is_moving_multiple:
            # Finalizar movimento múltiplo
            self.is_moving_multiple = False
            self.initial_positions = []
            self.move_start_x = 0
            self.move_start_y = 0
        
        elif self.mode == "connect" and self.temp_connection_start:
            # Flag para verificar se uma conexão foi criada
            connection_created = False
            
            # Verificar se soltou sobre uma caixa
            for box in self.boxes:
                if box.contains_point(event.x, event.y) and box != self.temp_connection_start:
                    # Criar conexão entre os objetos
                    connection = Connection(self.canvas, self.temp_connection_start, box)
                    self.connections.append(connection)
                    connection_created = True
                    break
            
            # Se não conectou com uma caixa, verificar se soltou sobre um container
            if not connection_created:
                for container in self.containers:
                    if container.contains_point(event.x, event.y) and container != self.temp_connection_start:
                        # Criar conexão entre os objetos
                        connection = Connection(self.canvas, self.temp_connection_start, container)
                        self.connections.append(connection)
                        connection_created = True
                        break
            
            # Remover a linha temporária
            self.canvas.delete(self.temp_line)
            self.temp_connection_start = None
            
            # Atualizar barra de status se uma conexão foi criada
            if connection_created:
                self.statusbar.config(text="Conexão criada. Use o menu de contexto para adicionar um rótulo, se necessário.")
    
    def on_double_click(self, event):
        """Manipula o evento de duplo clique."""
        if self.mode == "select":
            # Verificar se clicou em uma caixa existente
            for box in self.boxes:
                if box.contains_point(event.x, event.y):
                    box.edit_text()
                    return
            
            # Verificar se clicou na barra de título de um container
            for container in self.containers:
                if container.is_on_title_bar(event.x, event.y):
                    container.edit_title()
                    return
    
    def edit_selected(self, event=None):
        """Edita o texto da caixa ou título do container selecionado."""
        if self.selected_box:
            self.selected_box.edit_text()
        elif self.selected_container:
            self.selected_container.edit_title()
    
    def delete_selected(self, event=None):
        """Exclui a caixa ou container selecionado."""
        # Deletar múltiplos elementos selecionados
        if self.selected_boxes or self.selected_containers:
            # Deletar todas as caixas selecionadas
            for box in list(self.selected_boxes):  # Usar list() para evitar modificação durante iteração
                box.delete()
                if box in self.boxes:
                    self.boxes.remove(box)
            
            # Deletar todos os containers selecionados
            for container in list(self.selected_containers):
                container.delete()
                if container in self.containers:
                    self.containers.remove(container)
            
            # Limpar listas de seleção
            self.selected_boxes = []
            self.selected_containers = []
            
            self.statusbar.config(text="Elementos selecionados excluídos")
            
        elif self.selected_box:
            self.selected_box.delete()
            self.boxes.remove(self.selected_box)
            self.selected_box = None
        elif self.selected_container:
            self.selected_container.delete()
            self.containers.remove(self.selected_container)
            self.selected_container = None
        elif self.selected_connection:
            self.delete_selected_connection()
            
    def delete_selected_connection(self):
        """Exclui a conexão selecionada."""
        if self.selected_connection:
            # Remover a conexão da lista
            if self.selected_connection in self.connections:
                self.connections.remove(self.selected_connection)
            
            # Deletar a conexão
            self.selected_connection.delete()
            self.selected_connection = None
            
            # Atualizar a interface
            self.statusbar.config(text="Conexão excluída")
            
    def edit_connection_label(self):
        """Edita o rótulo da conexão selecionada."""
        if self.selected_connection:
            self.selected_connection.edit_label()
            # Restaurar a cor normal da linha após a edição
            self.canvas.itemconfig(self.selected_connection.line, width=2, fill="gray")
    
    def change_box_color(self):
        """Altera a cor da caixa ou container selecionado."""
        if self.selected_boxes or self.selected_containers:
            # Alterar cor de todos os elementos selecionados
            if self.selected_boxes:
                # Pegar a cor da primeira caixa como referência
                color = colorchooser.askcolor(initialcolor=self.selected_boxes[0].fill_color, title="Escolha a cor")
                if color[1]:  # Se uma cor foi selecionada
                    for box in self.selected_boxes:
                        box.fill_color = color[1]
                        box.canvas.itemconfig(box.rect, fill=box.fill_color)
            
            if self.selected_containers:
                # Se não houve seleção de caixas, pedir cor para containers
                if not self.selected_boxes:
                    color = colorchooser.askcolor(initialcolor=self.selected_containers[0].fill_color, title="Escolha a cor")
                    if color[1]:  # Se uma cor foi selecionada
                        for container in self.selected_containers:
                            container.fill_color = color[1]
                            container.canvas.itemconfig(container.rect, fill=container.fill_color)
                else:
                    # Usar a mesma cor das caixas para os containers
                    if 'color' in locals() and color[1]:
                        for container in self.selected_containers:
                            container.fill_color = color[1]
                            container.canvas.itemconfig(container.rect, fill=container.fill_color)
        elif self.selected_box:
            self.selected_box.change_color()
        elif self.selected_container:
            self.selected_container.change_color()
        else:
            messagebox.showinfo("Trocar Cor", "Selecione uma caixa ou container primeiro.")
    
    def bring_selected_to_front(self):
        """Traz o elemento selecionado para a frente."""
        if self.selected_boxes or self.selected_containers:
            # Trazer todos os elementos selecionados para a frente
            for box in self.selected_boxes:
                box.bring_to_front()
            for container in self.selected_containers:
                container.bring_to_front()
        elif self.selected_box:
            self.selected_box.bring_to_front()
        elif self.selected_container:
            self.selected_container.bring_to_front()
        else:
            messagebox.showinfo("Ordenar Camadas", "Selecione uma caixa ou container primeiro.")
    
    def send_selected_to_back(self):
        """Envia o elemento selecionado para trás."""
        if self.selected_boxes or self.selected_containers:
            # Enviar todos os elementos selecionados para trás
            for box in self.selected_boxes:
                box.send_to_back()
            for container in self.selected_containers:
                container.send_to_back()
        elif self.selected_box:
            self.selected_box.send_to_back()
        elif self.selected_container:
            self.selected_container.send_to_back()
        else:
            messagebox.showinfo("Ordenar Camadas", "Selecione uma caixa ou container primeiro.")
    
    def clear_selection(self, event=None):
        """Limpa toda a seleção."""
        # Desselecionar elemento único
        if self.selected_box:
            self.selected_box.deselect()
            self.selected_box = None
        if self.selected_container:
            self.selected_container.deselect()
            self.selected_container = None
        if self.selected_connection:
            try:
                self.canvas.itemconfig(self.selected_connection.line, width=2, fill="gray")
            except tk.TclError:
                pass
            self.selected_connection = None
        
        # Desselecionar elementos múltiplos
        for box in self.selected_boxes:
            box.deselect()
        for container in self.selected_containers:
            container.deselect()
        
        self.selected_boxes = []
        self.selected_containers = []
        
        # Remover retângulo de seleção se existir
        if self.selection_rectangle:
            self.canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None
        
        self.is_selecting = False
        self.is_moving_multiple = False
        
        # Limpar variáveis de movimento múltiplo
        self.initial_positions = []
        self.move_start_x = 0
        self.move_start_y = 0
    
    def select_all(self, event=None):
        """Seleciona todos os elementos."""
        self.clear_selection()
        
        # Selecionar todas as caixas
        for box in self.boxes:
            if box not in self.selected_boxes:
                box.select(box.x, box.y)
                self.selected_boxes.append(box)
        
        # Selecionar todos os containers
        for container in self.containers:
            if container not in self.selected_containers:
                container.select(container.x, container.y)
                self.selected_containers.append(container)
        
        self.statusbar.config(text=f"Selecionados: {len(self.selected_boxes)} caixas, {len(self.selected_containers)} containers")
    
    def add_to_selection(self, item):
        """Adiciona um item à seleção múltipla."""
        if isinstance(item, Container):
            if item not in self.selected_containers:
                item.select(item.x, item.y)
                self.selected_containers.append(item)
        else:  # VisionMapBox ou NoteBox
            if item not in self.selected_boxes:
                item.select(item.x, item.y)
                self.selected_boxes.append(item)
    
    def remove_from_selection(self, item):
        """Remove um item da seleção múltipla."""
        if isinstance(item, Container):
            if item in self.selected_containers:
                item.deselect()
                self.selected_containers.remove(item)
        else:  # VisionMapBox ou NoteBox
            if item in self.selected_boxes:
                item.deselect()
                self.selected_boxes.remove(item)
    
    def is_selected_multiple(self, item):
        """Verifica se um item está na seleção múltipla."""
        if isinstance(item, Container):
            return item in self.selected_containers
        else:
            return item in self.selected_boxes
    
    def get_selection_bounds(self, x1, y1, x2, y2):
        """Retorna os elementos dentro do retângulo de seleção."""
        selected_items = []
        
        # Normalizar coordenadas do retângulo
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Verificar caixas
        for box in self.boxes:
            box_left = box.x - box.width/2
            box_right = box.x + box.width/2
            box_top = box.y - box.height/2
            box_bottom = box.y + box.height/2
            
            # Verificar se a caixa está completamente dentro do retângulo
            if (box_left >= min_x and box_right <= max_x and 
                box_top >= min_y and box_bottom <= max_y):
                selected_items.append(box)
        
        # Verificar containers
        for container in self.containers:
            cont_left = container.x - container.width/2
            cont_right = container.x + container.width/2
            cont_top = container.y - container.height/2
            cont_bottom = container.y + container.height/2
            
            # Verificar se o container está completamente dentro do retângulo
            if (cont_left >= min_x and cont_right <= max_x and 
                cont_top >= min_y and cont_bottom <= max_y):
                selected_items.append(container)
        
        return selected_items
            
    def on_right_click(self, event):
        """Manipula o evento de clique com o botão direito do mouse."""
        # Limpar seleção anterior da conexão
        if self.selected_connection:
            self.canvas.itemconfig(self.selected_connection.line, width=2, fill="gray")
            self.selected_connection = None
        
        # Verificar se clicou em alguma caixa, container ou conexão
        clicked_on_item = False
        
        # Verificar caixas
        for box in self.boxes:
            if box.contains_point(event.x, event.y):
                # Selecionar a caixa
                if self.selected_box:
                    self.selected_box.deselect()
                if self.selected_container:
                    self.selected_container.deselect()
                    self.selected_container = None
                
                self.selected_box = box
                box.select(event.x, event.y)
                clicked_on_item = True
                # Mostrar menu de contexto para caixa
                self.context_menu.post(event.x_root, event.y_root)
                break
        
        # Se não clicou em uma caixa, verificar containers
        if not clicked_on_item:
            for container in self.containers:
                if container.contains_point(event.x, event.y):
                    # Selecionar o container
                    if self.selected_box:
                        self.selected_box.deselect()
                        self.selected_box = None
                    if self.selected_container:
                        self.selected_container.deselect()
                    
                    self.selected_container = container
                    container.select(event.x, event.y)
                    clicked_on_item = True
                    # Mostrar menu de contexto para container
                    self.context_menu.post(event.x_root, event.y_root)
                    break
        
        # Se não clicou em caixa ou container, verificar conexões
        if not clicked_on_item:
            for connection in self.connections:
                if connection.is_clicked(event.x, event.y):
                    # Limpar outras seleções
                    if self.selected_box:
                        self.selected_box.deselect()
                        self.selected_box = None
                    if self.selected_container:
                        self.selected_container.deselect()
                        self.selected_container = None
                    
                    # Selecionar a conexão
                    self.selected_connection = connection
                    # Destacar visualmente a conexão selecionada
                    self.canvas.itemconfig(connection.line, width=3, fill="red")
                    clicked_on_item = True
                    # Mostrar menu de contexto para conexão
                    self.connection_menu.post(event.x_root, event.y_root)
                    break
    
    def check_boxes_in_containers(self):
        """Verifica todas as caixas para determinar se estão dentro de algum container."""
        # Limpar todas as associações atuais
        for container in self.containers:
            container.boxes.clear()
        
        for box in self.boxes:
            box.container = None
        
        # Recalcular as associações
        for box in self.boxes:
            for container in self.containers:
                if container.contains_box(box):
                    container.add_box(box)
                    break
    
    def check_container_relationships(self):
        """Verifica e atualiza as relações entre containers."""
        # Limpar todas as relações de containers filhos
        for container in self.containers:
            if hasattr(container, 'child_containers'):
                container.child_containers.clear()
            else:
                container.child_containers = []
            container.parent_container = None
        
        # Criar um conjunto para manter o controle de quais containers já têm pais
        # para evitar relacionamentos circulares
        has_parent = set()
        
        # Recalcular as relações com base na posição atual
        # Começamos com os maiores containers (possíveis pais) primeiro
        sorted_containers = sorted(self.containers, key=lambda c: c.width * c.height, reverse=True)
        
        for container in self.containers:
            # Pular se já tem um pai
            if container in has_parent:
                continue
                
            # Verificar cada container como possível filho
            for potential_parent in sorted_containers:
                # Evitar auto-referência e ciclos
                if (container != potential_parent and 
                    potential_parent.contains_container(container) and
                    # Garantir que não teremos ciclos nos relacionamentos
                    not self._would_create_cycle(container, potential_parent)):
                    
                    potential_parent.add_child_container(container)
                    has_parent.add(container)
                    # Uma vez encontrado um pai, não procuramos mais (evita containers com múltiplos pais)
                    break
    
    def _would_create_cycle(self, child, potential_parent):
        """Verifica se adicionar o container filho ao container pai criaria um ciclo."""
        # Se o filho é igual ao potencial pai, temos um ciclo
        if child == potential_parent:
            return True
            
        # Se o potencial pai não tem atributo parent_container, não há ciclo
        if not hasattr(potential_parent, 'parent_container') or potential_parent.parent_container is None:
            return False
            
        # Verifica recursivamente se algum dos ancestrais do potencial pai é igual ao filho
        current = potential_parent.parent_container
        visited = set([potential_parent])
        
        while current:
            if current == child:
                return True
                
            if current in visited:
                # Detectou ciclo existente (não relacionado ao novo relacionamento)
                return False
                
            visited.add(current)
            
            if not hasattr(current, 'parent_container'):
                break
                
            current = current.parent_container
            
        return False
        
        # Verificar todas as caixas também
        self.check_boxes_in_containers()
        
        # Agendar a próxima verificação (menos frequente para melhorar performance)
        self.root.after(5000, self.check_container_relationships)
        
        # Mensagem de debug na barra de status para verificar se as relações estão sendo estabelecidas
        if self.containers:
            child_count = sum(len(c.child_containers) if hasattr(c, 'child_containers') else 0 for c in self.containers)
            if child_count > 0:
                self.statusbar.config(text=f"Detectados {child_count} containers aninhados")
    
    def new_visionmap(self, event=None):
        """Cria um novo visionmap."""
        if (self.boxes or self.containers) and messagebox.askyesno("Novo VisionMap", 
                                          "Deseja salvar o visionmap atual antes de criar um novo?"):
            self.save_visionmap()
        
        # Limpar o canvas
        self.canvas.delete("all")
        self.boxes = []
        self.containers = []
        self.connections = []
        self.selected_box = None
        self.selected_container = None
        self.current_file = None
        self.statusbar.config(text="Novo visionmap criado")
    
    def save_visionmap(self, event=None):
        """Salva o visionmap atual."""
        if not self.current_file:
            self.save_as_visionmap()
            return True
        
        self.save_to_file(self.current_file)
        self.statusbar.config(text=f"VisionMap salvo em: {self.current_file}")
        return True
    
    def save_as_visionmap(self):
        """Salva o visionmap com um novo nome de arquivo."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".vmap",
            filetypes=[("VisionMap files", "*.vmap"), ("All files", "*.*")]
        )
        if not file_path:
            return False
        
        self.save_to_file(file_path)
        self.current_file = file_path
        self.statusbar.config(text=f"VisionMap salvo em: {file_path}")
        return True
    
    def save_to_file(self, file_path):
        """Salva o visionmap no arquivo especificado."""
        data = {
            'boxes': [],
            'containers': [],
            'connections': []
        }
        
        # Mapear id de objetos para índices
        box_id_to_index = {}
        container_id_to_index = {}
        
        # Atualizar as relações entre containers antes de salvar
        self.check_container_relationships()
        
        # Salvar todos os containers
        for i, container in enumerate(self.containers):
            container_data = container.get_state()
            # Adicionar índice do container pai, se houver
            if container.parent_container:
                container_data['parent_container_index'] = container_id_to_index.get(id(container.parent_container))
            data['containers'].append(container_data)
            container_id_to_index[id(container)] = i
        
        # Salvar todas as caixas
        for i, box in enumerate(self.boxes):
            box_data = box.get_state()
            if box.container:
                box_data['container_index'] = container_id_to_index[id(box.container)]
            data['boxes'].append(box_data)
            box_id_to_index[id(box)] = i
        
        # Salvar todas as conexões
        for connection in self.connections:
            conn_data = {}
            # Determinar o tipo do primeiro objeto
            if isinstance(connection.obj1, Container):
                conn_data['obj1_type'] = 'container'
                conn_data['obj1_index'] = container_id_to_index[id(connection.obj1)]
            else:  # É uma caixa
                conn_data['obj1_type'] = 'box'
                conn_data['obj1_index'] = box_id_to_index[id(connection.obj1)]
            
            # Determinar o tipo do segundo objeto
            if isinstance(connection.obj2, Container):
                conn_data['obj2_type'] = 'container'
                conn_data['obj2_index'] = container_id_to_index[id(connection.obj2)]
            else:  # É uma caixa
                conn_data['obj2_type'] = 'box'
                conn_data['obj2_index'] = box_id_to_index[id(connection.obj2)]
            
            data['connections'].append(conn_data)
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    
    def open_visionmap(self, event=None):
        """Abre um arquivo de visionmap existente."""
        if (self.boxes or self.containers) and messagebox.askyesno("Abrir VisionMap", 
                                          "Deseja salvar o visionmap atual antes de abrir outro?"):
            self.save_visionmap()
        
        file_path = filedialog.askopenfilename(
            filetypes=[("VisionMap files", "*.vmap"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        self.open_from_file(file_path)
    
    def open_from_file(self, file_path):
        """Abre um visionmap a partir do arquivo especificado."""
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # Verificar se os dados têm a estrutura esperada
            if not isinstance(data, dict):
                raise ValueError("Arquivo com formato inválido")
                
            # Garantir que as chaves esperadas existam
            if 'boxes' not in data:
                data['boxes'] = []
            if 'containers' not in data:
                data['containers'] = []
            if 'connections' not in data:
                data['connections'] = []
            
            # Limpar o canvas atual
            self.canvas.delete("all")
            self.boxes = []
            self.containers = []
            self.connections = []
            
            # Recriar todos os containers primeiro
            containers_map = {}  # Mapear índices para objetos de container
            container_id_map = {}  # Mapear IDs originais para novos objetos de container
            parent_container_map = {}  # Mapear IDs de containers para seus containers pais
            
            if 'containers' in data:
                for i, container_data in enumerate(data['containers']):
                    container = Container(
                        self.canvas,
                        container_data['x'], container_data['y'],
                        container_data.get('width', 300), 
                        container_data.get('height', 200),
                        container_data.get('title', 'Novo Container'),
                        container_data.get('fill_color', "#F0F0F0"),
                        container_data.get('outline_color', "#888888")
                    )
                    self.containers.append(container)
                    containers_map[i] = container
                    
                    # Armazenar o índice do container pai se houver
                    if 'parent_container_index' in container_data and container_data['parent_container_index'] is not None:
                        parent_index = container_data['parent_container_index']
                        # Relacionar posteriormente quando todos os containers forem criados
                        if parent_index in containers_map:
                            parent = containers_map[parent_index]
                            parent.add_child_container(container)
            
            # Recriar todas as caixas
            for box_data in data['boxes']:
                # Verificar o tipo da caixa (normal ou anotação)
                if box_data.get('type') == 'note':
                    box = NoteBox.from_state(self.canvas, box_data)
                else:
                    fill_color = box_data.get('fill_color', "lightblue")
                    outline_color = box_data.get('outline_color', "#CCCCCC")
                    box = VisionMapBox(
                        self.canvas, 
                        box_data['x'], box_data['y'],
                        box_data['text'], 
                        box_data['width'], box_data['height'],
                        fill_color, outline_color
                    )
                self.boxes.append(box)
                
                # Associar a caixa ao container, se necessário
                if 'container_index' in box_data and box_data['container_index'] in containers_map:
                    container = containers_map[box_data['container_index']]
                    container.add_box(box)
            
            # Recriar todas as conexões
            if 'connections' in data:
                for conn_data in data['connections']:
                    try:
                        # Obter o primeiro objeto (caixa ou container)
                        if 'obj1_type' in conn_data:  # Novo formato
                            obj1_type = conn_data['obj1_type']
                            obj1_index = conn_data['obj1_index']
                            
                            # Verificar se o índice é válido
                            if obj1_type == 'container':
                                if obj1_index >= len(self.containers):
                                    print(f"Aviso: Índice de container inválido: {obj1_index}")
                                    continue
                                obj1 = self.containers[obj1_index]
                            else:
                                if obj1_index >= len(self.boxes):
                                    print(f"Aviso: Índice de caixa inválido: {obj1_index}")
                                    continue
                                obj1 = self.boxes[obj1_index]
                            
                            # Obter o segundo objeto (caixa ou container)
                            obj2_type = conn_data['obj2_type']
                            obj2_index = conn_data['obj2_index']
                            
                            # Verificar se o índice é válido
                            if obj2_type == 'container':
                                if obj2_index >= len(self.containers):
                                    print(f"Aviso: Índice de container inválido: {obj2_index}")
                                    continue
                                obj2 = self.containers[obj2_index]
                            else:
                                if obj2_index >= len(self.boxes):
                                    print(f"Aviso: Índice de caixa inválido: {obj2_index}")
                                    continue
                                obj2 = self.boxes[obj2_index]
                        else:  # Formato antigo (compatibilidade)
                            if 'box1_index' not in conn_data or 'box2_index' not in conn_data:
                                print("Aviso: Dados de conexão incompletos")
                                continue
                            
                            box1_index = conn_data['box1_index']
                            box2_index = conn_data['box2_index']
                            
                            if box1_index >= len(self.boxes) or box2_index >= len(self.boxes):
                                print(f"Aviso: Índices de caixa inválidos: {box1_index}, {box2_index}")
                                continue
                            
                            obj1 = self.boxes[box1_index]
                            obj2 = self.boxes[box2_index]
                        
                        # Verificar se há texto de rótulo
                        label_text = conn_data.get('label_text', "")
                        
                        connection = Connection(self.canvas, obj1, obj2, label_text)
                        self.connections.append(connection)
                        
                    except (IndexError, KeyError, ValueError) as e:
                        print(f"Erro ao recriar conexão: {e}")
                        continue
                    
            # Estabelecer relações entre containers depois que todos foram criados
            # Verificar todos os containers para determinar relações pai-filho com base na posição
            # Começamos com os maiores containers para garantir hierarquia correta
            sorted_containers = sorted(self.containers, key=lambda c: c.width * c.height, reverse=True)
            
            for container in sorted_containers:
                # Se já tem um pai, não buscar outro
                if container.parent_container:
                    continue
                    
                for potential_parent in sorted_containers:
                    if container != potential_parent and potential_parent.contains_container(container):
                        potential_parent.add_child_container(container)
                        break
            
            self.current_file = file_path
            self.statusbar.config(text=f"VisionMap aberto de: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o arquivo: {str(e)}")
    
    def export_image(self):
        """Exporta o visionmap como uma imagem."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            # Obter as dimensões do canvas
            # Considerar tanto caixas quanto containers
            all_items = self.boxes + self.containers
            
            if not all_items:
                x_min, y_min = 0, 0
                x_max, y_max = 800, 600
            else:
                x_min = min([item.x - item.width/2 for item in all_items])
                y_min = min([item.y - item.height/2 for item in all_items])
                x_max = max([item.x + item.width/2 for item in all_items])
                y_max = max([item.y + item.height/2 for item in all_items])
            
            # Adicionar margem
            margin = 50
            x_min -= margin
            y_min -= margin
            x_max += margin
            y_max += margin
            
            # Criar imagem do canvas
            self.canvas.postscript(file=file_path + ".ps", x=x_min, y=y_min, 
                                  width=x_max-x_min, height=y_max-y_min)
            
            # Converter PS para PNG
            # Nota: isso requer o pacote Pillow e o ghostscript instalados
            from PIL import Image, ImageGrab
            import subprocess
            
            try:
                # Tentar usar ghostscript (mais preciso)
                subprocess.call(
                    ["gswin64c", "-sDEVICE=pngalpha", "-o", file_path, "-r300", file_path + ".ps"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                os.remove(file_path + ".ps")
            except Exception:
                # Alternativa: capturar a tela (menos preciso)
                messagebox.showinfo(
                    "Exportar Imagem", 
                    "Para exportar a imagem, a tela será capturada em 3 segundos.\n"
                    "Por favor, não mova a janela."
                )
                self.root.after(3000, lambda: self._capture_screen(file_path))
                
            self.statusbar.config(text=f"Imagem exportada para: {file_path}")
        
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Não foi possível exportar a imagem: {str(e)}")
            
    def export_mermaid(self):
        """Exporta o visionmap como código Mermaid com informações de posicionamento."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            # Criar dicionários para mapear IDs para nomes mais legíveis no Mermaid
            box_ids = {}
            container_ids = {}
            
            # Normalizar coordenadas para melhor posicionamento relativo
            all_items = self.boxes + self.containers
            if all_items:
                min_x = min([item.x for item in all_items])
                min_y = min([item.y for item in all_items])
                max_x = max([item.x for item in all_items])
                max_y = max([item.y for item in all_items])
                
                # Evitar divisão por zero
                width_range = max(max_x - min_x, 1)
                height_range = max(max_y - min_y, 1)
            else:
                min_x = min_y = 0
                width_range = height_range = 1
            
            # Função para normalizar coordenadas (0-1)
            def normalize_coord(x, y):
                norm_x = round((x - min_x) / width_range, 2)
                norm_y = round((y - min_y) / height_range, 2)
                return norm_x, norm_y
            
            # Gerar IDs legíveis para caixas
            for i, box in enumerate(self.boxes):
                # Criar um ID baseado no texto abreviado da caixa
                text_for_id = ''.join(ch for ch in box.text[:15] if ch.isalnum())
                box_id = f"box{i}_{text_for_id}"
                box_ids[id(box)] = box_id
            
            # Gerar IDs legíveis para containers
            for i, container in enumerate(self.containers):
                # Criar um ID baseado no título abreviado do container
                text_for_id = ''.join(ch for ch in container.title[:15] if ch.isalnum())
                container_id = f"container{i}_{text_for_id}"
                container_ids[id(container)] = container_id
            
            # Começar a construir o código Mermaid simples, sem comentários ou configurações extras
            mermaid_code = "```mermaid\nflowchart TD\n"
            
            # Adicionar posicionamento explícito para caixas não contidas
            for box in self.boxes:
                if not box.container:  # Se não está em um container
                    box_id = box_ids[id(box)]
                    
                    # Escapar aspas e caracteres especiais no texto
                    safe_text = box.text.replace('"', '\\"').replace('<', '&lt;').replace('>', '&gt;')
                    
                    if isinstance(box, NoteBox):
                        mermaid_code += f"    {box_id}[[\"{safe_text}\"]]:::noteStyle\n"
                    else:
                        mermaid_code += f"    {box_id}[\"{safe_text}\"]\n"
                    
                    # Adicionar estilo simples com cor do texto preta
                    mermaid_code += f"    style {box_id} fill:{box.fill_color},stroke:{box.outline_color},color:#000000\n"
            
            # Adicionar subgráficos para containers com posicionamento
            for i, container in enumerate(self.containers):
                container_id = container_ids[id(container)]
                
                # Escapar aspas e caracteres especiais no título
                safe_title = container.title.replace('"', '\\"').replace('<', '&lt;').replace('>', '&gt;')
                
                mermaid_code += f"    subgraph {container_id}[\"{safe_title}\"]\n"
                
                # Estilizar o container de forma simples com cor do texto preta
                mermaid_code += f"        style {container_id} fill:{container.fill_color},stroke:{container.outline_color},color:#000000\n"
                
                # Adicionar caixas que estão dentro deste container
                for box in container.boxes:
                    box_id = box_ids[id(box)]
                    
                    # Escapar aspas e caracteres especiais no texto
                    safe_text = box.text.replace('"', '\\"').replace('<', '&lt;').replace('>', '&gt;')
                    
                    if isinstance(box, NoteBox):
                        mermaid_code += f"        {box_id}[[\"{safe_text}\"]]:::noteStyle\n"
                    else:
                        mermaid_code += f"        {box_id}[\"{safe_text}\"]\n"
                    
                    # Estilizar a caixa de forma simples com cor do texto preta
                    mermaid_code += f"        style {box_id} fill:{box.fill_color},stroke:{box.outline_color},color:#000000\n"
                
                mermaid_code += "    end\n"
                
                mermaid_code += "    end\n"
            
            # Adicionar conexões
            for connection in self.connections:
                # Determinar os IDs dos objetos conectados
                if isinstance(connection.obj1, Container):
                    obj1_id = container_ids[id(connection.obj1)]
                else:
                    obj1_id = box_ids[id(connection.obj1)]
                    
                if isinstance(connection.obj2, Container):
                    obj2_id = container_ids[id(connection.obj2)]
                else:
                    obj2_id = box_ids[id(connection.obj2)]
                
                # Escolher o tipo de linha com base no tipo de seta
                line_type = "-->" if connection.arrow else "---"
                
                # Adicionar a conexão com o rótulo, se houver
                if connection.label_text:
                    # Escapar aspas e caracteres especiais no texto
                    safe_label = connection.label_text.replace('"', '\\"').replace('<', '&lt;').replace('>', '&gt;')
                    mermaid_code += f"    {obj1_id} {line_type}|{safe_label}| {obj2_id}\n"
                else:
                    mermaid_code += f"    {obj1_id} {line_type} {obj2_id}\n"
            
            # Adicionar estilo para notas sem comentários extras
            mermaid_code += "    classDef noteStyle fill:#FFFFD0,stroke:#CCCCCC,color:#000000\n"
            mermaid_code += "```"
            
            # Escrever o código em um arquivo
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code)
                
            self.statusbar.config(text=f"Diagrama exportado como Mermaid para: {file_path}")
            
            # Criar uma página HTML para visualização mais precisa
            html_path = file_path + ".html"
            
            # Obter as dimensões do canvas e adicionar margem
            canvas_width = self.canvas.winfo_width() + 100
            canvas_height = self.canvas.winfo_height() + 100
            
            # Extrair apenas o conteúdo do mermaid sem os delimitadores
            mermaid_content = mermaid_code.replace("```mermaid\n", "").replace("```\n", "").strip()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>VisionMap Preview</title>
                <meta charset="UTF-8">
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: 'default'
                    }});
                </script>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                    }}
                    .preview-container {{ 
                        border: 1px solid #ccc;
                        padding: 20px;
                        border-radius: 5px;
                        width: {canvas_width}px;
                        height: {canvas_height}px;
                        position: relative;
                        overflow: auto;
                    }}
                    .mermaid svg {{ 
                        width: 100%;
                        height: auto;
                    }}
                </style>
            </head>
            <body>
                <h1>Visualização do VisionMap</h1>
                <div class="preview-container">
                    <pre class="mermaid">
{mermaid_content}
                    </pre>
                </div>
            </body>
            </html>
            """
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Opcionalmente, mostrar o código para o usuário
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Código Mermaid Gerado")
            preview_window.geometry("700x500")
            
            text_widget = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD)
            text_widget.insert(tk.INSERT, mermaid_code)
            text_widget.pack(expand=True, fill=tk.BOTH)
            
            # Frame para botões
            button_frame = tk.Frame(preview_window)
            button_frame.pack(fill=tk.X, pady=10)
            
            # Botão para copiar para a área de transferência
            def copy_to_clipboard():
                preview_window.clipboard_clear()
                preview_window.clipboard_append(mermaid_code)
                messagebox.showinfo("Copiado", "Código Mermaid copiado para a área de transferência!")
            
            copy_button = tk.Button(button_frame, text="Copiar para Área de Transferência", command=copy_to_clipboard)
            copy_button.pack(side=tk.LEFT, padx=10)
            
            # Botão para abrir a visualização HTML
            def open_html_preview():
                import webbrowser
                webbrowser.open('file://' + os.path.abspath(html_path))
                
            preview_button = tk.Button(button_frame, text="Abrir Visualização HTML", command=open_html_preview)
            preview_button.pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Não foi possível exportar como Mermaid: {str(e)}")
    
    def _capture_screen(self, file_path):
        """Captura a tela para exportar como imagem."""
        try:
            from PIL import ImageGrab
            
            # Obter coordenadas da janela
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            
            # Capturar a tela
            img = ImageGrab.grab(bbox=(x, y, x1, y1))
            img.save(file_path)
            
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Não foi possível capturar a tela: {str(e)}")
    
    def on_window_resize(self, event):
        """Atualiza a região de rolagem do canvas quando a janela é redimensionada."""
        # Verificar se o evento está relacionado à janela principal e não a outros widgets
        if event.widget == self.root:
            # Manter a região de rolagem do canvas pelo menos do tamanho atual
            if hasattr(self, 'canvas_width') and hasattr(self, 'canvas_height'):
                self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
    
    def on_mouse_wheel(self, event):
        """Permite usar a roda do mouse para mover o canvas verticalmente ou horizontalmente com Ctrl."""
        # Determinar a direção do movimento
        if event.num == 4:
            # Linux: Button-4 é rolagem para cima
            direction = -1
        elif event.num == 5:
            # Linux: Button-5 é rolagem para baixo
            direction = 1
        else:
            # Windows/macOS: Usar delta da roda do mouse
            direction = -1 if event.delta > 0 else 1
        
        # Verifica se a tecla Ctrl está pressionada
        # No Windows: event.state & 4 (valor binário para Ctrl)
        # No Linux: event.state & 0x4
        ctrl_pressed = (event.state & 4) > 0 or (hasattr(event, 'keysym') and event.keysym == 'Control_L')
        
        if ctrl_pressed or hasattr(event, 'widget') and 'Control' in str(event.type):
            # Rolagem horizontal
            self.canvas.xview_scroll(direction, "units")
        else:
            # Rolagem vertical
            self.canvas.yview_scroll(direction, "units")
    
    def resize_canvas(self, scale_factor, reset=False):
        """Redimensiona o canvas pelo fator de escala fornecido."""
        if reset:
            # Redefine para o tamanho padrão
            self.canvas_width = 3000
            self.canvas_height = 2000
        else:
            # Calcula novo tamanho com base no fator de escala
            self.canvas_width = int(self.canvas_width * scale_factor)
            self.canvas_height = int(self.canvas_height * scale_factor)
        
        # Atualizar a região de rolagem do canvas
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        # Atualizar a barra de status
        self.statusbar.config(text=f"Tamanho do canvas ajustado para {self.canvas_width}x{self.canvas_height}")
    
    def center_canvas_view(self):
        """Centraliza a visão do canvas."""
        # Obter as dimensões da região de rolagem
        x1, y1, x2, y2 = self.canvas.cget("scrollregion").split()
        width = float(x2) - float(x1)
        height = float(y2) - float(y1)
        
        # Obter o centro da região de rolagem
        x_center = width / 2
        y_center = height / 2
        
        # Mover a visão para o centro
        self.canvas.xview_moveto((x_center - self.canvas.winfo_width() / 2) / width)
        self.canvas.yview_moveto((y_center - self.canvas.winfo_height() / 2) / height)
        
        self.statusbar.config(text="Visão centralizada")
    
    def fit_canvas_to_content(self):
        """Ajusta o tamanho do canvas para acomodar todo o conteúdo atual."""
        if not (self.boxes or self.containers):
            messagebox.showinfo("Ajustar Canvas", "Não há conteúdo para ajustar o canvas.")
            return
            
        # Encontrar os limites do conteúdo
        all_items = self.boxes + self.containers
        x_min = min([item.x - item.width/2 for item in all_items])
        y_min = min([item.y - item.height/2 for item in all_items])
        x_max = max([item.x + item.width/2 for item in all_items])
        y_max = max([item.y + item.height/2 for item in all_items])
        
        # Adicionar margem
        margin = 500  # Margem extra para facilitar edição
        x_min = max(0, x_min - margin)
        y_min = max(0, y_min - margin)
        x_max += margin
        y_max += margin
        
        # Garantir tamanho mínimo
        self.canvas_width = max(3000, int(x_max))
        self.canvas_height = max(2000, int(y_max))
        
        # Atualizar a região de rolagem
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        self.statusbar.config(text=f"Canvas ajustado para acomodar todo o conteúdo: {self.canvas_width}x{self.canvas_height}")
    
    def start_pan(self, event):
        """Inicia o modo de navegação por arrasto."""
        # Mudar o cursor para indicar movimento
        self.canvas.config(cursor="fleur")  # Cursor de movimento
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def pan_canvas(self, event):
        """Move o canvas quando o usuário arrasta com o botão do meio do mouse."""
        if not self.panning:
            return
            
        # Calcular a diferença de posição
        dx = self.pan_start_x - event.x
        dy = self.pan_start_y - event.y
        
        # Mover a visualização do canvas
        self.canvas.xview_scroll(dx, "units")
        self.canvas.yview_scroll(dy, "units")
        
        # Atualizar posição inicial para o próximo movimento
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def stop_pan(self, event):
        """Para o modo de navegação por arrasto."""
        self.panning = False
        self.canvas.config(cursor="")  # Restaurar cursor padrão
        
    def import_from_mermaid(self):
        """Importa um diagrama Mermaid para o visionmap."""
        if (self.boxes or self.containers) and messagebox.askyesno(
            "Importar Mermaid",
            "Deseja salvar o visionmap atual antes de importar um diagrama Mermaid?"
        ):
            self.save_visionmap()
        
        # Abrir o arquivo Mermaid
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Markdown files", "*.md"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            title="Importar diagrama Mermaid"
        )
        if not file_path:
            return
        
        try:
            # Verificar se o arquivo existe e pode ser lido
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Ler o conteúdo do arquivo
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                raise ValueError("Arquivo está vazio")
            
            # Extrair o código Mermaid entre ```mermaid e ```
            mermaid_code = ""
            
            # Verificar se o conteúdo está entre delimitadores ```mermaid
            import re
            mermaid_match = re.search(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)
            if mermaid_match:
                mermaid_code = mermaid_match.group(1)
            else:
                # Se não encontrou os delimitadores, assume que todo o conteúdo é código Mermaid
                mermaid_code = content
            
            if not mermaid_code.strip():
                raise ValueError("Nenhum código Mermaid válido encontrado no arquivo")
            
            # Limpar o canvas
            self.canvas.delete("all")
            self.boxes = []
            self.containers = []
            self.connections = []
            self.selected_box = None
            self.selected_container = None
            
            # Processar o código Mermaid
            self.parse_mermaid_code(mermaid_code)
            
            self.statusbar.config(text=f"Diagrama Mermaid importado de: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro ao Importar", f"Não foi possível importar o diagrama Mermaid: {str(e)}")
    
    def parse_mermaid_code(self, mermaid_code):
        """Analisa o código Mermaid e cria elementos no visionmap."""
        # Dicionários para mapear IDs para objetos
        node_objects = {}  # ID Mermaid -> objeto (caixa ou container)
        style_data = {}    # ID Mermaid -> dados de estilo
        subgraphs = {}     # ID Mermaid -> lista de IDs de nós filhos
        
        # Posições iniciais para os elementos
        start_x, start_y = 100, 100
        x_offset = 200
        y_offset = 150
        current_x = start_x
        current_y = start_y
        
        # Analisar nós
        import re
        
        # Extrair definições de estilo
        style_matches = re.findall(r"style\s+(\w+)\s+([^\\n]+)", mermaid_code)
        for style_match in style_matches:
            node_id, style_text = style_match
            style_data[node_id] = {}
            
            # Extrair propriedades do estilo
            style_props = re.findall(r"([^:,]+):([^,]+)", style_text)
            for prop, value in style_props:
                style_data[node_id][prop.strip()] = value.strip()
        
        # Extrair definições de classe
        class_matches = re.findall(r"classDef\s+(\w+)\s+([^\\n]+)", mermaid_code)
        class_styles = {}
        for class_match in class_matches:
            class_name, style_text = class_match
            class_styles[class_name] = {}
            
            # Extrair propriedades da classe
            style_props = re.findall(r"([^:,]+):([^,]+)", style_text)
            for prop, value in style_props:
                class_styles[class_name][prop.strip()] = value.strip()
        
        # Encontrar nós e subgráficos
        lines = mermaid_code.split('\n')
        in_subgraph = False
        current_subgraph = None
        
        for line in lines:
            line = line.strip()
            
            # Ignorar linhas vazias e comentários
            if not line or line.startswith("%%"):
                continue
                
            # Verificar se é um início de subgráfico
            subgraph_match = re.match(r"subgraph\s+(\w+)(?:\[(.*?)\])?", line)
            if subgraph_match:
                in_subgraph = True
                subgraph_id = subgraph_match.group(1)
                subgraph_title = subgraph_match.group(2) if subgraph_match.group(2) else "Container"
                subgraph_title = subgraph_title.strip('"')
                
                # Criar container
                container = Container(
                    self.canvas,
                    current_x, current_y,
                    300, 200,  # tamanho padrão
                    subgraph_title,
                    "#F0F0F0", "#888888"  # cores padrão
                )
                
                # Aplicar estilo se disponível
                if subgraph_id in style_data:
                    style = style_data[subgraph_id]
                    if 'fill' in style:
                        container.fill_color = style['fill']
                    if 'stroke' in style:
                        container.outline_color = style['stroke']
                
                self.containers.append(container)
                node_objects[subgraph_id] = container
                subgraphs[subgraph_id] = []
                current_subgraph = subgraph_id
                
                current_y += y_offset
                continue
            
            # Verificar se é um fim de subgráfico
            if line == "end" and in_subgraph:
                in_subgraph = False
                current_subgraph = None
                continue
            
            # Verificar se é um nó normal
            node_match = re.match(r"(\w+)(?:\[(.*?)\]|\[\[(.*?)\]\])", line)
            if node_match:
                node_id = node_match.group(1)
                node_text = node_match.group(2) if node_match.group(2) else node_match.group(3)
                node_text = node_text.strip('"')
                
                # Determinar se é uma nota ou caixa normal
                is_note = "[[" in line and "]]" in line
                
                # Criar caixa ou nota
                if is_note:
                    box = NoteBox(self.canvas, current_x, current_y, node_text)
                else:
                    box = VisionMapBox(self.canvas, current_x, current_y, node_text)
                
                # Aplicar estilo se disponível
                if node_id in style_data:
                    style = style_data[node_id]
                    if 'fill' in style:
                        box.fill_color = style['fill']
                        box.update()
                    if 'stroke' in style:
                        box.outline_color = style['stroke']
                        box.update()
                
                # Aplicar classe se houver
                class_match = re.search(r":::(\w+)", line)
                if class_match and class_match.group(1) in class_styles:
                    class_name = class_match.group(1)
                    style = class_styles[class_name]
                    if 'fill' in style:
                        box.fill_color = style['fill']
                        box.update()
                    if 'stroke' in style:
                        box.outline_color = style['stroke']
                        box.update()
                
                self.boxes.append(box)
                node_objects[node_id] = box
                
                # Adicionar ao subgráfico atual, se estiver em um
                if current_subgraph:
                    subgraphs[current_subgraph].append(node_id)
                    container = node_objects[current_subgraph]
                    container.add_box(box)
                
                current_x += x_offset
                if current_x > 800:  # Evitar que vá muito para a direita
                    current_x = start_x
                    current_y += y_offset
                
                continue
            
            # Verificar se é uma conexão
            conn_match = re.match(r"(\w+)\s+(-->|---|\.->.|\.--.|\==>|\=\=\=)\s+(\w+)", line)
            if conn_match:
                try:
                    node1_id = conn_match.group(1)
                    conn_type = conn_match.group(2)
                    node2_id = conn_match.group(3)
                    
                    # Verificar se os nós existem
                    if node1_id in node_objects and node2_id in node_objects:
                        obj1 = node_objects[node1_id]
                        obj2 = node_objects[node2_id]
                        
                        # Verificar se há texto para o rótulo da conexão
                        label_text = ""
                        label_match = re.search(r"\|(.+?)\|", line)
                        if label_match:
                            label_text = label_match.group(1).strip()
                        
                        # Determinar se a conexão tem seta
                        has_arrow = "-->" in conn_type or ".->" in conn_type or "==>" in conn_type
                        
                        # Criar conexão
                        connection = Connection(self.canvas, obj1, obj2, label_text)
                        connection.arrow = has_arrow
                        self.connections.append(connection)
                except (IndexError, AttributeError, ValueError) as e:
                    print(f"Erro ao criar conexão: {e}")
                    continue
        
        # Posicionar os containers de acordo com seus conteúdos
        for container_id, box_ids in subgraphs.items():
            if container_id in node_objects:
                container = node_objects[container_id]
                # Atualizar o container para ajustar seu tamanho aos elementos contidos
                container.update()
        
        # Reorganizar o layout para evitar sobreposições
        self.reorganize_layout()
        
        self.statusbar.config(text="Diagrama Mermaid importado com sucesso!")

    def reorganize_layout(self):
        """Reorganiza o layout para evitar sobreposições."""
        # Implementação simples para espalhar os elementos
        # Esta é uma versão básica, você pode melhorar com algoritmos mais avançados
        
        # Primeiro, reposicionar os containers com alguma distância entre eles
        container_spacing = 350
        current_x = 100
        current_y = 100
        
        for container in self.containers:
            container.move_to(current_x + container.width/2, current_y + container.height/2)
            current_x += container.width + container_spacing
            
            # Mudar para a próxima linha se ficar muito largo
            if current_x > 1000:
                current_x = 100
                current_y += 300
        
        # Depois, reposicionar as caixas que não estão em containers
        box_spacing = 200
        if current_x > 800:
            current_x = 100
            current_y += 250
        
        for box in self.boxes:
            if not box.container:
                box.move_to(current_x, current_y)
                current_x += box_spacing
                
                # Mudar para a próxima linha se ficar muito largo
                if current_x > 1000:
                    current_x = 100
                    current_y += 150

    def debug_containers(self):
        """Método para depuração de containers aninhados."""
        # Forçar uma verificação dos relacionamentos
        self.check_container_relationships()
        
        # Verificar todos os containers
        debug_info = "Informações de containers:\n\n"
        for i, container in enumerate(self.containers):
            # Garantir que os atributos existam
            if not hasattr(container, 'child_containers'):
                container.child_containers = []
            if not hasattr(container, 'parent_container'):
                container.parent_container = None
            
            # Contar filhos
            child_containers = len(container.child_containers)
            child_boxes = len(container.boxes)
            
            # Adicionar destaque visual temporário
            original_outline = container.outline_color
            self.canvas.itemconfig(container.rect, outline="red", width=3)
            self.canvas.update()
            
            debug_info += f"{i+1}. '{container.title}' ({container.x}, {container.y}):\n"
            debug_info += f"   - {child_containers} containers filhos\n"
            debug_info += f"   - {child_boxes} caixas\n"
            
            if container.parent_container:
                debug_info += f"   - Dentro de: '{container.parent_container.title}'\n"
            else:
                debug_info += f"   - Container de nível superior\n"
            
            # Restaurar aparência após 500ms
            self.root.after(500, lambda c=container, o=original_outline: 
                self.canvas.itemconfig(c.rect, outline=o, width=2))
        
        # Mostrar informações
        messagebox.showinfo("Debug de Containers", debug_info)

    def show_about(self):
        """Mostra a caixa de diálogo 'Sobre'."""
        messagebox.showinfo(
            "Sobre VisionMap Creator",
            "VisionMap Creator v1.2\n\n"
            "Um aplicativo simples para criar mapas visuais.\n\n"
            "Novas funcionalidades:\n"
            "• Seleção múltipla (Ctrl+clique)\n"
            "• Seleção por área (arrastar)\n"
            "• Movimentação múltipla\n"
            "• Operações em lote\n"
            "• Containers aninhados\n\n"
            "Desenvolvido com Python e Tkinter."
        )

# Função principal
def main():
    root = tk.Tk()
    app = VisionMapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()