"""
Gerenciador de eventos para a interface do VisionMap
"""

import tkinter as tk
from ..models.box import VisionMapBox
from ..models.note_box import NoteBox
from ..models.container import Container
from ..models.connection import Connection


class EventHandlers:
    """Classe que gerencia todos os eventos da interface."""
    
    def __init__(self, app):
        self.app = app
    
    def on_canvas_click(self, event):
        """Manipula o evento de clique no canvas."""
        # Converter coordenadas da janela para coordenadas do canvas
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        
        if self.app.mode == "add_box":
            self._add_box_click(canvas_x, canvas_y)
        elif self.app.mode == "add_note":
            self._add_note_click(canvas_x, canvas_y)
        elif self.app.mode == "add_container":
            self._add_container_click(canvas_x, canvas_y)
        elif self.app.mode == "select":
            self._select_mode_click(event, canvas_x, canvas_y)
        elif self.app.mode == "connect":
            self._connect_mode_click(event, canvas_x, canvas_y)
    
    def _add_box_click(self, canvas_x, canvas_y):
        """Manipula clique no modo de adicionar caixa."""
        box = VisionMapBox(self.app.canvas, canvas_x, canvas_y)
        self.app.boxes.append(box)
        
        # Verificar se a caixa está dentro de algum container
        for container in self.app.containers:
            if container.contains_box(box):
                container.add_box(box)
                break
    
    def _add_note_click(self, canvas_x, canvas_y):
        """Manipula clique no modo de adicionar anotação."""
        note = NoteBox(self.app.canvas, canvas_x, canvas_y)
        self.app.boxes.append(note)
        
        # Verificar se a anotação está dentro de algum container
        for container in self.app.containers:
            if container.contains_box(note):
                container.add_box(note)
                break
    
    def _add_container_click(self, canvas_x, canvas_y):
        """Manipula clique no modo de adicionar container."""
        container = Container(self.app.canvas, canvas_x, canvas_y)
        self.app.containers.append(container)
        
        # Verificar se existem caixas que devem ser adicionadas ao container
        for box in self.app.boxes:
            if container.contains_box(box):
                container.add_box(box)
    
    def _select_mode_click(self, event, canvas_x, canvas_y):
        """Manipula clique no modo de seleção."""
        ctrl_pressed = (event.state & 0x4) != 0
        
        if not ctrl_pressed:
            self.app.clear_selection()
        
        # Verificar se clicou no manipulador de redimensionamento
        for container in self.app.containers:
            if container.is_on_resize_handle(canvas_x, canvas_y):
                self.app.resizing_container = container
                container.start_resize(canvas_x, canvas_y)
                return
        
        clicked_on_item = False
        
        # Verificar clique na barra de título de container
        for container in self.app.containers:
            if container.is_on_title_bar(canvas_x, canvas_y):
                self._handle_container_selection(container, ctrl_pressed, canvas_x, canvas_y)
                clicked_on_item = True
                return
        
        # Verificar clique em caixa
        for box in self.app.boxes:
            if box.contains_point(canvas_x, canvas_y):
                self._handle_box_selection(box, ctrl_pressed, canvas_x, canvas_y)
                clicked_on_item = True
                return
        
        # Verificar clique em container
        for container in self.app.containers:
            if container.contains_point(canvas_x, canvas_y):
                self._handle_container_selection(container, ctrl_pressed, canvas_x, canvas_y)
                clicked_on_item = True
                return
        
        # Se não clicou em item, iniciar seleção por área
        if not clicked_on_item and not ctrl_pressed:
            self.app.is_selecting = True
            self.app.selection_start_x = canvas_x
            self.app.selection_start_y = canvas_y
    
    def _handle_box_selection(self, box, ctrl_pressed, canvas_x, canvas_y):
        """Manipula seleção de caixas."""
        if ctrl_pressed and self._is_selected_multiple(box):
            self._remove_from_selection(box)
        else:
            if self._is_selected_multiple(box) and (self.app.selected_boxes or self.app.selected_containers):
                pass  # Preparar para mover múltiplos elementos
            elif not ctrl_pressed:
                self.app.selected_box = box
                box.select(canvas_x, canvas_y)
            else:
                self._add_to_selection(box)
    
    def _handle_container_selection(self, container, ctrl_pressed, canvas_x, canvas_y):
        """Manipula seleção de containers."""
        if ctrl_pressed and self._is_selected_multiple(container):
            self._remove_from_selection(container)
        else:
            if self._is_selected_multiple(container) and (self.app.selected_boxes or self.app.selected_containers):
                pass  # Preparar para mover múltiplos elementos
            elif not ctrl_pressed:
                self.app.selected_container = container
                container.select(canvas_x, canvas_y)
            else:
                self._add_to_selection(container)
    
    def _connect_mode_click(self, event, canvas_x, canvas_y):
        """Manipula clique no modo de conectar."""
        # Primeiro tentar com caixas
        for box in self.app.boxes:
            if box.contains_point(canvas_x, canvas_y):
                if not self.app.temp_connection_start:
                    self.app.temp_connection_start = box
                    self.app.temp_line = self.app.canvas.create_line(
                        box.x, box.y, box.x, box.y,
                        width=2, fill="gray", dash=(4, 4)
                    )
                return
        
        # Se não encontrou caixa, tentar com containers
        for container in self.app.containers:
            if container.contains_point(canvas_x, canvas_y):
                if not self.app.temp_connection_start:
                    self.app.temp_connection_start = container
                    self.app.temp_line = self.app.canvas.create_line(
                        container.x, container.y, container.x, container.y,
                        width=2, fill="gray", dash=(4, 4)
                    )
                break
    
    def on_canvas_drag(self, event):
        """Manipula o evento de arrastar no canvas."""
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        
        if self.app.resizing_container:
            self.app.resizing_container.resize(canvas_x, canvas_y)
        elif self.app.mode == "select":
            self._handle_select_drag(canvas_x, canvas_y)
        elif self.app.mode == "connect" and self.app.temp_connection_start:
            self._handle_connect_drag(event)
    
    def _handle_select_drag(self, canvas_x, canvas_y):
        """Manipula arrastar no modo seleção."""
        if self.app.is_selecting:
            self._update_selection_rectangle(canvas_x, canvas_y)
        elif self.app.selected_boxes or self.app.selected_containers:
            self._handle_multiple_move(canvas_x, canvas_y)
        elif self.app.selected_box:
            self._handle_single_box_move(canvas_x, canvas_y)
        elif self.app.selected_container:
            self._handle_single_container_move(canvas_x, canvas_y)
    
    def _update_selection_rectangle(self, canvas_x, canvas_y):
        """Atualiza o retângulo de seleção."""
        if self.app.selection_rectangle:
            self.app.canvas.delete(self.app.selection_rectangle)
        
        self.app.selection_rectangle = self.app.canvas.create_rectangle(
            self.app.selection_start_x, self.app.selection_start_y,
            canvas_x, canvas_y,
            outline="blue", width=1, dash=(5, 5)
        )
    
    def _handle_multiple_move(self, canvas_x, canvas_y):
        """Manipula movimento de múltiplos elementos."""
        if not self.app.is_moving_multiple:
            self.app.is_moving_multiple = True
            self.app.move_start_x = canvas_x
            self.app.move_start_y = canvas_y
            
            self.app.initial_positions = []
            
            for box in self.app.selected_boxes:
                self.app.initial_positions.append(('box', box, box.x, box.y))
            
            for container in self.app.selected_containers:
                self.app.initial_positions.append(('container', container, container.x, container.y))
        
        # Calcular deslocamento total
        dx_total = canvas_x - self.app.move_start_x
        dy_total = canvas_y - self.app.move_start_y
        
        # Mover todos os elementos
        for item_type, item, initial_x, initial_y in self.app.initial_positions:
            new_x = initial_x + dx_total
            new_y = initial_y + dy_total
            
            if item_type == 'box':
                self._move_box_directly(item, new_x, new_y)
            else:  # container
                item.move_to(new_x, new_y)
    
    def _move_box_directly(self, box, new_x, new_y):
        """Move uma caixa diretamente para novas coordenadas."""
        current_dx = new_x - box.x
        current_dy = new_y - box.y
        
        box.x = new_x
        box.y = new_y
        
        self.app.canvas.move(box.rect, current_dx, current_dy)
        self.app.canvas.move(box.text_id, current_dx, current_dy)
        
        if isinstance(box, NoteBox):
            self.app.canvas.move(box.toggle_button, current_dx, current_dy)
            self.app.canvas.move(box.toggle_symbol, current_dx, current_dy)
        
        for connection in box.connections:
            connection.update()
    
    def _handle_single_box_move(self, canvas_x, canvas_y):
        """Manipula movimento de caixa única."""
        self.app.selected_box.move(canvas_x, canvas_y)
        
        # Verificar se saiu de um container
        if self.app.selected_box.container:
            if not self.app.selected_box.container.contains_box(self.app.selected_box):
                self.app.selected_box.container.remove_box(self.app.selected_box)
        
        # Verificar se entrou em um container
        for container in self.app.containers:
            if container.contains_box(self.app.selected_box) and self.app.selected_box.container != container:
                if self.app.selected_box.container:
                    self.app.selected_box.container.remove_box(self.app.selected_box)
                container.add_box(self.app.selected_box)
                break
    
    def _handle_single_container_move(self, canvas_x, canvas_y):
        """Manipula movimento de container único."""
        if not hasattr(self.app.selected_container, 'child_containers'):
            self.app.selected_container.child_containers = []
        if not hasattr(self.app.selected_container, 'parent_container'):
            self.app.selected_container.parent_container = None
        
        self.app.selected_container.move(canvas_x, canvas_y)
        
        # Verificar mudança de container pai
        if hasattr(self.app.selected_container, 'parent_container') and self.app.selected_container.parent_container:
            old_parent = self.app.selected_container.parent_container
            if not old_parent.contains_container(self.app.selected_container):
                old_parent.remove_child_container(self.app.selected_container)
                self.app.statusbar.config(text=f"Container '{self.app.selected_container.title}' removido de '{old_parent.title}'")
        
        # Verificar se entrou em novo container
        for container in self.app.containers:
            if not hasattr(container, 'child_containers'):
                container.child_containers = []
                
            if (container != self.app.selected_container and 
                container.contains_container(self.app.selected_container) and 
                self.app.selected_container.parent_container != container):
                
                if self.app.selected_container.parent_container:
                    self.app.selected_container.parent_container.remove_child_container(self.app.selected_container)
                
                container.add_child_container(self.app.selected_container)
                self.app.statusbar.config(text=f"Container '{self.app.selected_container.title}' adicionado a '{container.title}'")
                break
    
    def _handle_connect_drag(self, event):
        """Manipula arrastar no modo conectar."""
        self.app.canvas.coords(
            self.app.temp_line,
            self.app.temp_connection_start.x, self.app.temp_connection_start.y,
            event.x, event.y
        )
    
    def on_canvas_release(self, event):
        """Manipula o evento de soltar o botão do mouse."""
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        
        if self.app.resizing_container:
            self.app.resizing_container.end_resize()
            self.app.resizing_container = None
        elif self.app.mode == "select" and self.app.is_selecting:
            self._finish_area_selection(canvas_x, canvas_y)
        elif self.app.mode == "select" and self.app.is_moving_multiple:
            self._finish_multiple_move()
        elif self.app.mode == "connect" and self.app.temp_connection_start:
            self._finish_connection(event)
    
    def _finish_area_selection(self, canvas_x, canvas_y):
        """Finaliza seleção por área."""
        if self.app.selection_rectangle:
            selected_items = self._get_selection_bounds(
                self.app.selection_start_x, self.app.selection_start_y,
                canvas_x, canvas_y
            )
            
            for item in selected_items:
                self._add_to_selection(item)
            
            self.app.canvas.delete(self.app.selection_rectangle)
            self.app.selection_rectangle = None
            
            self.app.statusbar.config(text=f"Selecionados: {len(self.app.selected_boxes)} caixas, {len(self.app.selected_containers)} containers")
        
        self.app.is_selecting = False
    
    def _finish_multiple_move(self):
        """Finaliza movimento múltiplo."""
        self.app.is_moving_multiple = False
        self.app.initial_positions = []
        self.app.move_start_x = 0
        self.app.move_start_y = 0
    
    def _finish_connection(self, event):
        """Finaliza criação de conexão."""
        connection_created = False
        
        # Verificar conexão com caixa
        for box in self.app.boxes:
            if box.contains_point(event.x, event.y) and box != self.app.temp_connection_start:
                connection = Connection(self.app.canvas, self.app.temp_connection_start, box)
                self.app.connections.append(connection)
                connection_created = True
                break
        
        # Se não conectou com caixa, verificar container
        if not connection_created:
            for container in self.app.containers:
                if container.contains_point(event.x, event.y) and container != self.app.temp_connection_start:
                    connection = Connection(self.app.canvas, self.app.temp_connection_start, container)
                    self.app.connections.append(connection)
                    connection_created = True
                    break
        
        # Remover linha temporária
        self.app.canvas.delete(self.app.temp_line)
        self.app.temp_connection_start = None
        
        if connection_created:
            self.app.statusbar.config(text="Conexão criada. Use o menu de contexto para adicionar um rótulo, se necessário.")
    
    def on_double_click(self, event):
        """Manipula o evento de duplo clique."""
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        
        if self.app.mode == "select":
            # Verificar clique em caixa
            for box in self.app.boxes:
                if box.contains_point(canvas_x, canvas_y):
                    box.edit_text()
                    return
            
            # Verificar clique na barra de título de container
            for container in self.app.containers:
                if container.is_on_title_bar(canvas_x, canvas_y):
                    container.edit_title()
                    return
    
    def on_right_click(self, event):
        """Manipula o evento de clique com o botão direito do mouse."""
        canvas_x = self.app.canvas.canvasx(event.x)
        canvas_y = self.app.canvas.canvasy(event.y)
        
        # Limpar seleção anterior da conexão
        if self.app.selected_connection:
            self.app.canvas.itemconfig(self.app.selected_connection.line, width=2, fill="gray")
            self.app.selected_connection = None
        
        clicked_on_item = False
        
        # Verificar clique em caixa
        for box in self.app.boxes:
            if box.contains_point(canvas_x, canvas_y):
                self._select_box_for_context(box, canvas_x, canvas_y, event)
                clicked_on_item = True
                break
        
        # Verificar clique em container
        if not clicked_on_item:
            for container in self.app.containers:
                if container.contains_point(canvas_x, canvas_y):
                    self._select_container_for_context(container, canvas_x, canvas_y, event)
                    clicked_on_item = True
                    break
        
        # Verificar clique em conexão
        if not clicked_on_item:
            for connection in self.app.connections:
                if connection.is_clicked(canvas_x, canvas_y):
                    self._select_connection_for_context(connection, event)
                    clicked_on_item = True
                    break
    
    def _select_box_for_context(self, box, canvas_x, canvas_y, event):
        """Seleciona caixa para menu de contexto."""
        if self.app.selected_box:
            self.app.selected_box.deselect()
        if self.app.selected_container:
            self.app.selected_container.deselect()
            self.app.selected_container = None
        
        self.app.selected_box = box
        box.select(canvas_x, canvas_y)
        self.app.context_menu.post(event.x_root, event.y_root)
    
    def _select_container_for_context(self, container, canvas_x, canvas_y, event):
        """Seleciona container para menu de contexto."""
        if self.app.selected_box:
            self.app.selected_box.deselect()
            self.app.selected_box = None
        if self.app.selected_container:
            self.app.selected_container.deselect()
        
        self.app.selected_container = container
        container.select(canvas_x, canvas_y)
        self.app.context_menu.post(event.x_root, event.y_root)
    
    def _select_connection_for_context(self, connection, event):
        """Seleciona conexão para menu de contexto."""
        if self.app.selected_box:
            self.app.selected_box.deselect()
            self.app.selected_box = None
        if self.app.selected_container:
            self.app.selected_container.deselect()
            self.app.selected_container = None
        
        self.app.selected_connection = connection
        self.app.canvas.itemconfig(connection.line, width=3, fill="red")
        self.app.connection_menu.post(event.x_root, event.y_root)
    
    # Métodos auxiliares para seleção múltipla
    def _add_to_selection(self, item):
        """Adiciona um item à seleção múltipla."""
        if isinstance(item, Container):
            if item not in self.app.selected_containers:
                item.select(item.x, item.y)
                self.app.selected_containers.append(item)
        else:
            if item not in self.app.selected_boxes:
                item.select(item.x, item.y)
                self.app.selected_boxes.append(item)
    
    def _remove_from_selection(self, item):
        """Remove um item da seleção múltipla."""
        if isinstance(item, Container):
            if item in self.app.selected_containers:
                item.deselect()
                self.app.selected_containers.remove(item)
        else:
            if item in self.app.selected_boxes:
                item.deselect()
                self.app.selected_boxes.remove(item)
    
    def _is_selected_multiple(self, item):
        """Verifica se um item está na seleção múltipla."""
        if isinstance(item, Container):
            return item in self.app.selected_containers
        else:
            return item in self.app.selected_boxes
    
    def _get_selection_bounds(self, x1, y1, x2, y2):
        """Retorna os elementos dentro do retângulo de seleção."""
        selected_items = []
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Verificar caixas
        for box in self.app.boxes:
            box_left = box.x - box.width/2
            box_right = box.x + box.width/2
            box_top = box.y - box.height/2
            box_bottom = box.y + box.height/2
            
            if (box_left >= min_x and box_right <= max_x and 
                box_top >= min_y and box_bottom <= max_y):
                selected_items.append(box)
        
        # Verificar containers
        for container in self.app.containers:
            cont_left = container.x - container.width/2
            cont_right = container.x + container.width/2
            cont_top = container.y - container.height/2
            cont_bottom = container.y + container.height/2
            
            if (cont_left >= min_x and cont_right <= max_x and 
                cont_top >= min_y and cont_bottom <= max_y):
                selected_items.append(container)
        
        return selected_items
    
    # Métodos para eventos de mouse wheel e pan
    def on_mouse_wheel(self, event):
        """Permite usar a roda do mouse para mover o canvas."""
        if event.num == 4:
            direction = -1
        elif event.num == 5:
            direction = 1
        else:
            direction = -1 if event.delta > 0 else 1
        
        ctrl_pressed = (event.state & 4) > 0
        
        if ctrl_pressed:
            self.app.canvas.xview_scroll(direction, "units")
        else:
            self.app.canvas.yview_scroll(direction, "units")
    
    def start_pan(self, event):
        """Inicia o modo de navegação por arrasto."""
        self.app.canvas.config(cursor="fleur")
        self.app.panning = True
        self.app.pan_start_x = event.x
        self.app.pan_start_y = event.y
    
    def pan_canvas(self, event):
        """Move o canvas quando o usuário arrasta."""
        if not self.app.panning:
            return
            
        dx = self.app.pan_start_x - event.x
        dy = self.app.pan_start_y - event.y
        
        self.app.canvas.xview_scroll(dx, "units")
        self.app.canvas.yview_scroll(dy, "units")
        
        self.app.pan_start_x = event.x
        self.app.pan_start_y = event.y
    
    def stop_pan(self, event):
        """Para o modo de navegação por arrasto."""
        self.app.panning = False
        self.app.canvas.config(cursor="")