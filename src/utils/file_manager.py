"""
Utilitários para operações de arquivo (salvar/abrir)
"""

import pickle
import os
from tkinter import messagebox


def save_visionmap_to_file(file_path, boxes, containers, connections):
    """Salva o visionmap no arquivo especificado."""
    data = {
        'boxes': [],
        'containers': [],
        'connections': []
    }
    
    # Mapear id de objetos para índices
    box_id_to_index = {}
    container_id_to_index = {}
    
    # Salvar todos os containers
    for i, container in enumerate(containers):
        container_data = container.get_state()
        # Adicionar índice do container pai, se houver
        if container.parent_container:
            container_data['parent_container_index'] = container_id_to_index.get(id(container.parent_container))
        data['containers'].append(container_data)
        container_id_to_index[id(container)] = i
    
    # Salvar todas as caixas
    for i, box in enumerate(boxes):
        box_data = box.get_state()
        if box.container:
            box_data['container_index'] = container_id_to_index[id(box.container)]
        data['boxes'].append(box_data)
        box_id_to_index[id(box)] = i
    
    # Salvar todas as conexões
    for connection in connections:
        conn_data = {}
        # Determinar o tipo do primeiro objeto
        from ..models.container import Container
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
        
        conn_data['label_text'] = connection.label_text
        data['connections'].append(conn_data)
    
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def load_visionmap_from_file(file_path, canvas):
    """Carrega um visionmap a partir do arquivo especificado."""
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
        
        # Importar classes necessárias
        from ..models.container import Container
        from ..models.box import VisionMapBox
        from ..models.note_box import NoteBox
        from ..models.connection import Connection
        
        # Listas para retorno
        boxes = []
        containers = []
        connections = []
        
        # Recriar todos os containers primeiro
        containers_map = {}  # Mapear índices para objetos de container
        
        if 'containers' in data:
            for i, container_data in enumerate(data['containers']):
                container = Container(
                    canvas,
                    container_data['x'], container_data['y'],
                    container_data.get('width', 300), 
                    container_data.get('height', 200),
                    container_data.get('title', 'Novo Container'),
                    container_data.get('fill_color', "#F0F0F0"),
                    container_data.get('outline_color', "#888888")
                )
                containers.append(container)
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
                box = NoteBox.from_state(canvas, box_data)
            else:
                fill_color = box_data.get('fill_color', "lightblue")
                outline_color = box_data.get('outline_color', "#CCCCCC")
                box = VisionMapBox(
                    canvas, 
                    box_data['x'], box_data['y'],
                    box_data['text'], 
                    box_data['width'], box_data['height'],
                    fill_color, outline_color
                )
            boxes.append(box)
            
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
                            if obj1_index >= len(containers):
                                print(f"Aviso: Índice de container inválido: {obj1_index}")
                                continue
                            obj1 = containers[obj1_index]
                        else:
                            if obj1_index >= len(boxes):
                                print(f"Aviso: Índice de caixa inválido: {obj1_index}")
                                continue
                            obj1 = boxes[obj1_index]
                        
                        # Obter o segundo objeto (caixa ou container)
                        obj2_type = conn_data['obj2_type']
                        obj2_index = conn_data['obj2_index']
                        
                        # Verificar se o índice é válido
                        if obj2_type == 'container':
                            if obj2_index >= len(containers):
                                print(f"Aviso: Índice de container inválido: {obj2_index}")
                                continue
                            obj2 = containers[obj2_index]
                        else:
                            if obj2_index >= len(boxes):
                                print(f"Aviso: Índice de caixa inválido: {obj2_index}")
                                continue
                            obj2 = boxes[obj2_index]
                    else:  # Formato antigo (compatibilidade)
                        if 'box1_index' not in conn_data or 'box2_index' not in conn_data:
                            print("Aviso: Dados de conexão incompletos")
                            continue
                        
                        box1_index = conn_data['box1_index']
                        box2_index = conn_data['box2_index']
                        
                        if box1_index >= len(boxes) or box2_index >= len(boxes):
                            print(f"Aviso: Índices de caixa inválidos: {box1_index}, {box2_index}")
                            continue
                        
                        obj1 = boxes[box1_index]
                        obj2 = boxes[box2_index]
                    
                    # Verificar se há texto de rótulo
                    label_text = conn_data.get('label_text', "")
                    
                    connection = Connection(canvas, obj1, obj2, label_text)
                    connections.append(connection)
                    
                except (IndexError, KeyError, ValueError) as e:
                    print(f"Erro ao recriar conexão: {e}")
                    continue
        
        # Estabelecer relações entre containers depois que todos foram criados
        sorted_containers = sorted(containers, key=lambda c: c.width * c.height, reverse=True)
        
        for container in sorted_containers:
            # Se já tem um pai, não buscar outro
            if container.parent_container:
                continue
                
            for potential_parent in sorted_containers:
                if container != potential_parent and potential_parent.contains_container(container):
                    potential_parent.add_child_container(container)
                    break
        
        return boxes, containers, connections
        
    except Exception as e:
        messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o arquivo: {str(e)}")
        return [], [], []