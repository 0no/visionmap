"""
Janela principal da aplicação VisionMap Creator
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os

from ..models.box import VisionMapBox
from ..models.note_box import NoteBox
from ..models.container import Container
from ..models.connection import Connection
from ..utils.file_manager import save_visionmap_to_file, load_visionmap_from_file
from ..utils.export_utils import export_to_mermaid, create_html_preview, show_mermaid_preview_window, export_to_image, capture_screen_to_image
from ..utils.import_utils import parse_mermaid_code
from ..utils.assets import get_asset_path, asset_exists
from ..utils.icon_utils import setup_window_icon
from .event_handlers import EventHandlers
from .menu_manager import MenuManager
from .toolbar_manager import ToolbarManager


class VisionMapApp:
    """Aplicativo principal de visionmap."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("VisionMap Creator")
        self.root.geometry("1000x700")
        
        # Configurar eventos de redimensionamento
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Definir o ícone da aplicação
        self._setup_icon()
        
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
        
        # Nome do arquivo atual
        self.current_file = None
        
        # Criar a interface
        self._create_interface()
        
        # Configurar eventos
        self._setup_events()
        
        # Agendar verificação periódica de relacionamentos entre containers
        self.root.after(1000, self.check_container_relationships)
    
    def _setup_icon(self):
        """Define o ícone da aplicação com múltiplas tentativas para Windows."""
        icon_configured = False
        
        # Tentativa 1: Método do utilitário
        try:
            if setup_window_icon(self.root):
                icon_configured = True
                print("✅ Ícone configurado via utilitário")
        except Exception as e:
            print(f"⚠️ Método 1 falhou: {e}")
        
        # Tentativa 2: PNG de alta resolução com iconphoto (melhor qualidade e transparência)
        if not icon_configured:
            try:
                from PIL import Image, ImageTk
                png_path = get_asset_path("logo_icon.png")
                if os.path.exists(png_path):
                    # Carregar imagem de alta resolução
                    img = Image.open(png_path)
                    
                    # Criar múltiplas versões para diferentes tamanhos
                    sizes = [16, 24, 32, 48, 64]
                    photos = []
                    
                    for size in sizes:
                        # Redimensionar com alta qualidade
                        resized = img.resize((size, size), Image.Resampling.LANCZOS)
                        
                        # Aplicar sharpening para tamanhos pequenos
                        if size <= 32:
                            try:
                                from PIL import ImageFilter
                                resized = resized.filter(ImageFilter.SHARPEN)
                            except:
                                pass
                        
                        photo = ImageTk.PhotoImage(resized)
                        photos.append(photo)
                    
                    # Usar a versão de 32x32 como principal (boa para barra de tarefas)
                    self.root.iconphoto(True, photos[2])  # 32x32
                    
                    # Manter referências para evitar garbage collection
                    self.root._icon_photos = photos
                    icon_configured = True
                    print("✅ Ícone PNG de alta resolução configurado")
            except Exception as e:
                print(f"⚠️ Método 2 falhou: {e}")
        
        # Tentativa 3: ICO como fallback
        if not icon_configured:
            try:
                ico_path = get_asset_path("logo_icon.ico")
                if os.path.exists(ico_path):
                    self.root.iconbitmap(ico_path)
                    icon_configured = True
                    print("✅ Ícone ICO configurado como fallback")
            except Exception as e:
                print(f"⚠️ Método 3 falhou: {e}")
        
        if not icon_configured:
            print("❌ Não foi possível configurar nenhum ícone")
    
    def _create_interface(self):
        """Cria a interface da aplicação."""
        # Frame principal
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Criar o menu
        self.menu_manager = MenuManager(self)
        
        # Frame para o canvas e a barra de ferramentas
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de ferramentas
        self.toolbar_manager = ToolbarManager(self.canvas_frame, self)
        
        # Criar um frame para o canvas com barras de rolagem
        self.canvas_container = tk.Frame(self.canvas_frame)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Definir o tamanho inicial do canvas
        self.canvas_width = 3000
        self.canvas_height = 2000
        
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
        
        # Barra de status
        self.statusbar = tk.Label(self.main_frame, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
    
    def _setup_events(self):
        """Configura os eventos da aplicação."""
        # Criar o gerenciador de eventos
        self.event_handlers = EventHandlers(self)
        
        # Binds para eventos do mouse
        self.canvas.bind("<Button-1>", self.event_handlers.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.event_handlers.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.event_handlers.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.event_handlers.on_double_click)
        self.canvas.bind("<Button-3>", self.event_handlers.on_right_click)
        
        # Eventos para navegação por arrastar (pan)
        self.canvas.bind("<Button-2>", self.event_handlers.start_pan)
        self.canvas.bind("<B2-Motion>", self.event_handlers.pan_canvas)
        self.canvas.bind("<ButtonRelease-2>", self.event_handlers.stop_pan)
        
        # Permitir pan com Shift+arrastar
        self.canvas.bind("<Shift-Button-1>", self.event_handlers.start_pan)
        self.canvas.bind("<Shift-B1-Motion>", self.event_handlers.pan_canvas)
        self.canvas.bind("<Shift-ButtonRelease-1>", self.event_handlers.stop_pan)
        
        # Suporte para rolagem com o mouse
        self.canvas.bind("<Control-MouseWheel>", self.event_handlers.on_mouse_wheel)
        self.canvas.bind("<MouseWheel>", self.event_handlers.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.event_handlers.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.event_handlers.on_mouse_wheel)
        self.canvas.bind("<Control-Button-4>", self.event_handlers.on_mouse_wheel)
        self.canvas.bind("<Control-Button-5>", self.event_handlers.on_mouse_wheel)
        
        # Atalhos de teclado - operações de arquivo e edição
        self.root.bind("<Delete>", self.delete_selected)
        self.root.bind("<Control-s>", self.save_visionmap)
        self.root.bind("<Control-o>", self.open_visionmap)
        self.root.bind("<Control-n>", self.new_visionmap)
        
        # Atalhos de teclado para os modos
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
    
    # Métodos de controle de modo
    def set_select_mode(self):
        """Ativa o modo de seleção."""
        self.mode = "select"
        self.toolbar_manager.set_active_mode("select")
        self.statusbar.config(text="Modo: Selecionar e mover itens | Ctrl+clique para seleção múltipla | Arrastar para selecionar área")
    
    def set_add_box_mode(self):
        """Ativa o modo de adicionar caixa."""
        self.mode = "add_box"
        self.toolbar_manager.set_active_mode("add_box")
        self.statusbar.config(text="Modo: Adicionar nova caixa")
    
    def set_add_note_mode(self):
        """Ativa o modo de adicionar anotação."""
        self.mode = "add_note"
        self.toolbar_manager.set_active_mode("add_note")
        self.statusbar.config(text="Modo: Adicionar nova anotação")
    
    def set_add_container_mode(self):
        """Ativa o modo de adicionar container."""
        self.mode = "add_container"
        self.toolbar_manager.set_active_mode("add_container")
        self.statusbar.config(text="Modo: Adicionar novo container")
    
    def set_connect_mode(self):
        """Ativa o modo de conectar caixas."""
        self.mode = "connect"
        self.toolbar_manager.set_active_mode("connect")
        self.statusbar.config(text="Modo: Conectar caixas")
    
    # Métodos utilitários para criação de elementos
    def create_container_at(self, x, y, width, height, title="Novo Container"):
        """Cria um container nas coordenadas e dimensões especificadas."""
        container = Container(self.canvas, x, y, title=title, width=width, height=height)
        self.containers.append(container)
        
        if not hasattr(container, 'child_containers'):
            container.child_containers = []
        container.parent_container = None
        
        return container
        
    def create_box_at(self, x, y, text="Nova Caixa", width=100, height=50, fill_color="lightblue"):
        """Cria uma caixa nas coordenadas especificadas."""
        box = VisionMapBox(self.canvas, x, y, text=text, width=width, height=height, fill_color=fill_color)
        self.boxes.append(box)
        return box
    
    # Métodos de arquivo
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
        # Atualizar as relações entre containers antes de salvar
        self.check_container_relationships()
        save_visionmap_to_file(file_path, self.boxes, self.containers, self.connections)
    
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
        # Limpar o canvas atual
        self.canvas.delete("all")
        self.boxes = []
        self.containers = []
        self.connections = []
        
        # Carregar dados
        self.boxes, self.containers, self.connections = load_visionmap_from_file(file_path, self.canvas)
        
        if self.boxes or self.containers:
            self.current_file = file_path
            self.statusbar.config(text=f"VisionMap aberto de: {file_path}")
        else:
            self.statusbar.config(text="Erro ao abrir o arquivo")
    
    # Métodos de exportação
    def export_image(self):
        """Exporta o visionmap como uma imagem."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        if export_to_image(self.canvas, self.boxes, self.containers, file_path):
            self.statusbar.config(text=f"Imagem exportada para: {file_path}")
        else:
            # Tentar captura de tela como alternativa
            messagebox.showinfo(
                "Exportar Imagem", 
                "Para exportar a imagem, a tela será capturada em 3 segundos.\n"
                "Por favor, não mova a janela."
            )
            self.root.after(3000, lambda: self._capture_screen(file_path))
    
    def _capture_screen(self, file_path):
        """Captura a tela para exportar como imagem."""
        if capture_screen_to_image(self.root, self.canvas, file_path):
            self.statusbar.config(text=f"Imagem capturada e salva em: {file_path}")
    
    def export_mermaid(self):
        """Exporta o visionmap como código Mermaid."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            mermaid_code = export_to_mermaid(self.boxes, self.containers, self.connections)
            
            # Escrever o código em um arquivo
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code)
                
            self.statusbar.config(text=f"Diagrama exportado como Mermaid para: {file_path}")
            
            # Criar uma página HTML para visualização
            html_path = file_path + ".html"
            canvas_width = self.canvas.winfo_width() + 100
            canvas_height = self.canvas.winfo_height() + 100
            
            html_content = create_html_preview(mermaid_code, canvas_width, canvas_height)
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Mostrar janela de preview
            show_mermaid_preview_window(self.root, mermaid_code, html_path)
            
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Não foi possível exportar como Mermaid: {str(e)}")
    
    def import_from_mermaid(self):
        """Importa um diagrama Mermaid para o visionmap."""
        if (self.boxes or self.containers) and messagebox.askyesno(
            "Importar Mermaid",
            "Deseja salvar o visionmap atual antes de importar um diagrama Mermaid?"
        ):
            self.save_visionmap()
        
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
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                raise ValueError("Arquivo está vazio")
            
            # Extrair o código Mermaid
            import re
            mermaid_match = re.search(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)
            if mermaid_match:
                mermaid_code = mermaid_match.group(1)
            else:
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
            self.boxes, self.containers, self.connections = parse_mermaid_code(self.canvas, mermaid_code)
            
            self.statusbar.config(text=f"Diagrama Mermaid importado de: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro ao Importar", f"Não foi possível importar o diagrama Mermaid: {str(e)}")
    
    # Métodos de seleção e edição
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
            for box in list(self.selected_boxes):
                box.delete()
                if box in self.boxes:
                    self.boxes.remove(box)
            
            for container in list(self.selected_containers):
                container.delete()
                if container in self.containers:
                    self.containers.remove(container)
            
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
            if self.selected_connection in self.connections:
                self.connections.remove(self.selected_connection)
            
            self.selected_connection.delete()
            self.selected_connection = None
            self.statusbar.config(text="Conexão excluída")
    
    def edit_connection_label(self):
        """Edita o rótulo da conexão selecionada."""
        if self.selected_connection:
            self.selected_connection.edit_label()
            self.canvas.itemconfig(self.selected_connection.line, width=2, fill="gray")
    
    def change_box_color(self):
        """Altera a cor da caixa ou container selecionado."""
        from tkinter import colorchooser
        
        if self.selected_boxes or self.selected_containers:
            if self.selected_boxes:
                color = colorchooser.askcolor(initialcolor=self.selected_boxes[0].fill_color, title="Escolha a cor")
                if color[1]:
                    for box in self.selected_boxes:
                        box.fill_color = color[1]
                        box.canvas.itemconfig(box.rect, fill=box.fill_color)
            
            if self.selected_containers:
                if not self.selected_boxes:
                    color = colorchooser.askcolor(initialcolor=self.selected_containers[0].fill_color, title="Escolha a cor")
                    if color[1]:
                        for container in self.selected_containers:
                            container.fill_color = color[1]
                            container.canvas.itemconfig(container.rect, fill=container.fill_color)
                else:
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
    
    # Métodos de seleção múltipla
    def clear_selection(self, event=None):
        """Limpa toda a seleção."""
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
        
        for box in self.selected_boxes:
            box.deselect()
        for container in self.selected_containers:
            container.deselect()
        
        self.selected_boxes = []
        self.selected_containers = []
        
        if self.selection_rectangle:
            self.canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None
        
        self.is_selecting = False
        self.is_moving_multiple = False
        self.initial_positions = []
        self.move_start_x = 0
        self.move_start_y = 0
    
    def select_all(self, event=None):
        """Seleciona todos os elementos."""
        self.clear_selection()
        
        for box in self.boxes:
            if box not in self.selected_boxes:
                box.select(box.x, box.y)
                self.selected_boxes.append(box)
        
        for container in self.containers:
            if container not in self.selected_containers:
                container.select(container.x, container.y)
                self.selected_containers.append(container)
        
        self.statusbar.config(text=f"Selecionados: {len(self.selected_boxes)} caixas, {len(self.selected_containers)} containers")
    
    # Métodos utilitários
    def on_window_resize(self, event):
        """Atualiza a região de rolagem do canvas quando a janela é redimensionada."""
        if event.widget == self.root:
            if hasattr(self, 'canvas_width') and hasattr(self, 'canvas_height'):
                self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
    
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
        has_parent = set()
        
        # Recalcular as relações com base na posição atual
        sorted_containers = sorted(self.containers, key=lambda c: c.width * c.height, reverse=True)
        
        for container in self.containers:
            if container in has_parent:
                continue
                
            for potential_parent in sorted_containers:
                if (container != potential_parent and 
                    potential_parent.contains_container(container) and
                    not self._would_create_cycle(container, potential_parent)):
                    
                    potential_parent.add_child_container(container)
                    has_parent.add(container)
                    break
        
        # Verificar todas as caixas também
        self.check_boxes_in_containers()
        
        # Agendar a próxima verificação
        self.root.after(5000, self.check_container_relationships)
        
        # Atualizar barra de status se houver containers aninhados
        if self.containers:
            child_count = sum(len(c.child_containers) if hasattr(c, 'child_containers') else 0 for c in self.containers)
            if child_count > 0:
                self.statusbar.config(text=f"Detectados {child_count} containers aninhados")
    
    def _would_create_cycle(self, child, potential_parent):
        """Verifica se adicionar o container filho ao container pai criaria um ciclo."""
        if child == potential_parent:
            return True
            
        if not hasattr(potential_parent, 'parent_container') or potential_parent.parent_container is None:
            return False
            
        current = potential_parent.parent_container
        visited = set([potential_parent])
        
        while current:
            if current == child:
                return True
                
            if current in visited:
                return False
                
            visited.add(current)
            
            if not hasattr(current, 'parent_container'):
                break
                
            current = current.parent_container
            
        return False
    
    def check_boxes_in_containers(self):
        """Verifica todas as caixas para determinar se estão dentro de algum container."""
        for container in self.containers:
            container.boxes.clear()
        
        for box in self.boxes:
            box.container = None
        
        for box in self.boxes:
            for container in self.containers:
                if container.contains_box(box):
                    container.add_box(box)
                    break
    
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