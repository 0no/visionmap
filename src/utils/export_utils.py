"""
Utilitários para exportação (Mermaid, imagem)
"""

import os
import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageGrab


def export_to_mermaid(boxes, containers, connections):
    """Exporta o visionmap como código Mermaid."""
    # Criar dicionários para mapear IDs para nomes mais legíveis no Mermaid
    box_ids = {}
    container_ids = {}
    
    # Normalizar coordenadas para melhor posicionamento relativo
    all_items = boxes + containers
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
    for i, box in enumerate(boxes):
        # Criar um ID baseado no texto abreviado da caixa
        text_for_id = ''.join(ch for ch in box.text[:15] if ch.isalnum())
        box_id = f"box{i}_{text_for_id}"
        box_ids[id(box)] = box_id
    
    # Gerar IDs legíveis para containers
    for i, container in enumerate(containers):
        # Criar um ID baseado no título abreviado do container
        text_for_id = ''.join(ch for ch in container.title[:15] if ch.isalnum())
        container_id = f"container{i}_{text_for_id}"
        container_ids[id(container)] = container_id
    
    # Começar a construir o código Mermaid simples
    mermaid_code = "```mermaid\nflowchart TD\n"
    
    # Adicionar posicionamento explícito para caixas não contidas
    from ..models.note_box import NoteBox
    for box in boxes:
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
    for i, container in enumerate(containers):
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
    
    # Adicionar conexões
    from ..models.container import Container
    for connection in connections:
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
    
    # Adicionar estilo para notas
    mermaid_code += "    classDef noteStyle fill:#FFFFD0,stroke:#CCCCCC,color:#000000\n"
    mermaid_code += "```"
    
    return mermaid_code


def create_html_preview(mermaid_code, canvas_width=800, canvas_height=600):
    """Cria uma página HTML para visualização do diagrama Mermaid."""
    # Extrair apenas o conteúdo do mermaid sem os delimitadores
    mermaid_content = mermaid_code.replace("```mermaid\n", "").replace("```", "").strip()
    
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
    
    return html_content


def show_mermaid_preview_window(root, mermaid_code, html_path):
    """Mostra uma janela de preview do código Mermaid."""
    preview_window = tk.Toplevel(root)
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


def export_to_image(canvas, boxes, containers, file_path):
    """Exporta o visionmap como uma imagem."""
    try:
        # Obter as dimensões do canvas
        # Considerar tanto caixas quanto containers
        all_items = boxes + containers
        
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
        canvas.postscript(file=file_path + ".ps", x=x_min, y=y_min, 
                          width=x_max-x_min, height=y_max-y_min)
        
        # Converter PS para PNG
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
            return False
            
        return True
        
    except Exception as e:
        messagebox.showerror("Erro ao Exportar", f"Não foi possível exportar a imagem: {str(e)}")
        return False


def capture_screen_to_image(root, canvas, file_path):
    """Captura a tela para exportar como imagem."""
    try:
        # Obter coordenadas da janela
        x = root.winfo_rootx() + canvas.winfo_x()
        y = root.winfo_rooty() + canvas.winfo_y()
        x1 = x + canvas.winfo_width()
        y1 = y + canvas.winfo_height()
        
        # Capturar a tela
        img = ImageGrab.grab(bbox=(x, y, x1, y1))
        img.save(file_path)
        
        return True
        
    except Exception as e:
        messagebox.showerror("Erro ao Exportar", f"Não foi possível capturar a tela: {str(e)}")
        return False