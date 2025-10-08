"""
Utilitário para processamento de ícones da aplicação com alta resolução
"""

import os
from PIL import Image
from ..utils.assets import get_asset_path


def setup_window_icon(window):
    """
    Configura o ícone da janela com alta resolução para melhor qualidade na barra de tarefas.
    
    Args:
        window: Janela tkinter para configurar o ícone
    
    Returns:
        bool: True se configurou com sucesso, False caso contrário
    """
    try:
        from PIL import Image, ImageTk
        
        # Usar PNG de alta resolução
        png_path = get_asset_path("logo_icon.png")
        
        if not os.path.exists(png_path):
            print(f"PNG de alta resolução não encontrado: {png_path}")
            return False
        
        # Carregar imagem de alta resolução
        img = Image.open(png_path)
        
        # Criar versão otimizada para barra de tarefas (48x48 é um bom tamanho)
        taskbar_size = (48, 48)
        taskbar_img = img.resize(taskbar_size, Image.Resampling.LANCZOS)
        
        # Aplicar sharpening para melhor definição
        try:
            from PIL import ImageFilter, ImageEnhance
            taskbar_img = taskbar_img.filter(ImageFilter.SHARPEN)
            
            # Leve aumento de contraste
            enhancer = ImageEnhance.Contrast(taskbar_img)
            taskbar_img = enhancer.enhance(1.1)
        except:
            pass
        
        # Converter para PhotoImage
        photo = ImageTk.PhotoImage(taskbar_img)
        
        # Configurar ícone da janela
        window.iconphoto(True, photo)
        
        # Manter referência para evitar garbage collection
        window._icon_photo = photo
        
        return True
        
    except Exception as e:
        print(f"Erro ao configurar ícone: {e}")
        return False


def create_optimized_icon(source_image_path, output_path=None, size=(32, 32)):
    """
    Cria um ícone otimizado para o Windows a partir de uma imagem.
    
    Args:
        source_image_path (str): Caminho da imagem fonte
        output_path (str): Caminho de saída (opcional)
        size (tuple): Tamanho desejado do ícone (width, height)
    
    Returns:
        str: Caminho do ícone criado
    """
    try:
        # Abrir a imagem original
        original = Image.open(source_image_path)
        
        # Se não especificou saída, usar o mesmo diretório com sufixo _icon
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(source_image_path))[0]
            output_dir = os.path.dirname(source_image_path)
            output_path = os.path.join(output_dir, f"{base_name}_icon.png")
        
        # Redimensionar mantendo proporção
        original.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Criar uma nova imagem com fundo transparente
        icon = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Centralizar a imagem redimensionada
        paste_x = (size[0] - original.size[0]) // 2
        paste_y = (size[1] - original.size[1]) // 2
        
        # Colar a imagem original no centro
        if original.mode == 'RGBA':
            icon.paste(original, (paste_x, paste_y), original)
        else:
            # Se não tem canal alpha, converter para RGBA primeiro
            original_rgba = original.convert('RGBA')
            icon.paste(original_rgba, (paste_x, paste_y))
        
        # Salvar o ícone otimizado
        icon.save(output_path, 'PNG')
        
        return output_path
        
    except Exception as e:
        print(f"Erro ao criar ícone otimizado: {e}")
        return source_image_path


def create_ico_file(png_path, ico_path=None):
    """
    Converte um PNG para ICO (formato nativo do Windows) com tratamento adequado de transparência.
    
    Args:
        png_path (str): Caminho do arquivo PNG
        ico_path (str): Caminho de saída do ICO (opcional)
    
    Returns:
        str: Caminho do arquivo ICO criado
    """
    try:
        if ico_path is None:
            base_name = os.path.splitext(png_path)[0]
            ico_path = f"{base_name}.ico"
        
        # Abrir a imagem PNG
        img = Image.open(png_path)
        
        # Converter para RGBA se necessário
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Criar múltiplos tamanhos para o ICO (incluindo alta resolução)
        # Windows usa diferentes tamanhos dependendo do DPI e contexto
        sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), 
                (64, 64), (96, 96), (128, 128), (256, 256)]
        images = []
        
        for size in sizes:
            # Redimensionar para cada tamanho usando algoritmo de alta qualidade
            resized = img.copy()
            resized = resized.resize(size, Image.Resampling.LANCZOS)
            
            # Para tamanhos pequenos, aplicar sharpening para melhor nitidez
            if size[0] <= 48:
                try:
                    from PIL import ImageFilter
                    resized = resized.filter(ImageFilter.SHARPEN)
                except:
                    pass  # Se não conseguir aplicar filtro, continua sem
            
            images.append(resized)
        
        # Salvar como ICO com múltiplas resoluções
        images[0].save(ico_path, format='ICO', sizes=[img.size for img in images])
        
        return ico_path
        
    except Exception as e:
        print(f"Erro ao criar arquivo ICO: {e}")
        return png_path


def get_optimized_icon_path():
    """
    Retorna o caminho do ícone otimizado, criando-o se necessário.
    
    Returns:
        str: Caminho do ícone otimizado
    """
    logo_path = get_asset_path("logo.png")
    
    # Verificar se já existe um ícone otimizado
    icon_path = get_asset_path("logo_icon.png")
    ico_path = get_asset_path("logo.ico")
    
    # Se não existe, criar
    if not os.path.exists(icon_path):
        icon_path = create_optimized_icon(logo_path)
    
    # Se não existe ICO, criar
    if not os.path.exists(ico_path):
        ico_path = create_ico_file(icon_path)
    
    # Preferir ICO no Windows, PNG como fallback
    if os.name == 'nt' and os.path.exists(ico_path):
        return ico_path
    else:
        return icon_path


def setup_window_icon(root):
    """
    Configura o ícone da janela de forma otimizada.
    
    Args:
        root: Janela principal do Tkinter
    
    Returns:
        bool: True se configurou com sucesso, False caso contrário
    """
    try:
        from PIL import Image, ImageTk
        
        # Obter ícone otimizado
        icon_path = get_optimized_icon_path()
        
        if not os.path.exists(icon_path):
            print(f"Ícone não encontrado: {icon_path}")
            return False
        
        # Se for ICO, usar wm_iconbitmap (melhor para Windows)
        if icon_path.endswith('.ico'):
            root.wm_iconbitmap(icon_path)
            return True
        else:
            # Se for PNG, usar iconphoto
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            root.iconphoto(True, icon_photo)
            
            # Manter referência para evitar garbage collection
            if not hasattr(root, '_icon_refs'):
                root._icon_refs = []
            root._icon_refs.append(icon_photo)
            
            return True
            
    except Exception as e:
        print(f"Erro ao configurar ícone da janela: {e}")
        return False