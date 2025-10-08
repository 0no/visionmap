"""
Utilitários para importação (Mermaid)
"""

import re
from ..models.box import VisionMapBox
from ..models.note_box import NoteBox
from ..models.container import Container
from ..models.connection import Connection


def parse_mermaid_code(canvas, mermaid_code):
    """Analisa o código Mermaid e cria elementos no visionmap."""
    # Dicionários para mapear IDs para objetos
    node_objects = {}  # ID Mermaid -> objeto (caixa ou container)
    style_data = {}    # ID Mermaid -> dados de estilo
    subgraphs = {}     # ID Mermaid -> lista de IDs de nós filhos
    
    # Listas para retorno
    boxes = []
    containers = []
    connections = []
    
    # Posições iniciais para os elementos
    start_x, start_y = 100, 100
    x_offset = 200
    y_offset = 150
    current_x = start_x
    current_y = start_y
    
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
                canvas,
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
            
            containers.append(container)
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
                box = NoteBox(canvas, current_x, current_y, node_text)
            else:
                box = VisionMapBox(canvas, current_x, current_y, node_text)
            
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
            
            boxes.append(box)
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
                    connection = Connection(canvas, obj1, obj2, label_text)
                    connection.arrow = has_arrow
                    connections.append(connection)
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
    _reorganize_layout(boxes, containers)
    
    return boxes, containers, connections


def _reorganize_layout(boxes, containers):
    """Reorganiza o layout para evitar sobreposições."""
    # Primeiro, reposicionar os containers com alguma distância entre eles
    container_spacing = 350
    current_x = 100
    current_y = 100
    
    for container in containers:
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
    
    for box in boxes:
        if not box.container:
            box.move_to(current_x, current_y)
            current_x += box_spacing
            
            # Mudar para a próxima linha se ficar muito largo
            if current_x > 1000:
                current_x = 100
                current_y += 150