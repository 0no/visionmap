"""
Modelo para containers no VisionMap
"""

import tkinter as tk
from tkinter import simpledialog, colorchooser
from .base import VisualElement


class Container(VisualElement):
    """Classe que representa um container que pode agrupar várias caixas."""
    
    def __init__(self, canvas, x, y, width=300, height=200, title="Novo Container", 
                 fill_color="#F0F0F0", outline_color="#888888"):
        super().__init__(canvas, x, y, width, height)
        
        self.title = title
        self.fill_color = fill_color
        self.outline_color = outline_color
        
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
            from .note_box import NoteBox
            if isinstance(box, NoteBox):
                self.canvas.move(box.toggle_button, dx, dy)
                self.canvas.move(box.toggle_symbol, dx, dy)
            
            # Atualizar todas as conexões da caixa
            for connection in box.connections:
                connection.update()
        
        # Mover todos os containers filhos
        if hasattr(self, 'child_containers') and self.child_containers:
            # Criar um conjunto para rastrear os containers já processados
            processed = set()
            processed.add(self)
            
            for child_container in list(self.child_containers):
                # Verificações de segurança para evitar recursão infinita
                if child_container is None or child_container == self or id(child_container) in processed:
                    continue
                    
                # Marcar este container como processado
                processed.add(id(child_container))
                
                # Usar move_to para mover recursivamente containers filhos
                new_x = child_container.x + dx
                new_y = child_container.y + dy
                
                # Mover elementos visuais do container filho diretamente
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
                    from .note_box import NoteBox
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