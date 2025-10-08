"""
Utilitário para gerenciar recursos (assets) da aplicação
"""

import os


def get_asset_path(asset_name):
    """
    Retorna o caminho completo para um recurso da aplicação.
    
    Args:
        asset_name (str): Nome do arquivo de recurso (ex: "logo.png")
    
    Returns:
        str: Caminho completo para o recurso
    """
    # Obter diretório atual (src/utils/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navegar para src/assets/
    assets_dir = os.path.join(os.path.dirname(current_dir), "assets")
    
    # Retornar caminho completo do recurso
    return os.path.join(assets_dir, asset_name)


def asset_exists(asset_name):
    """
    Verifica se um recurso existe.
    
    Args:
        asset_name (str): Nome do arquivo de recurso
        
    Returns:
        bool: True se o recurso existe, False caso contrário
    """
    return os.path.exists(get_asset_path(asset_name))


def list_assets():
    """
    Lista todos os recursos disponíveis.
    
    Returns:
        list: Lista de nomes de arquivos de recursos
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(current_dir), "assets")
    
    if not os.path.exists(assets_dir):
        return []
    
    return [f for f in os.listdir(assets_dir) 
            if os.path.isfile(os.path.join(assets_dir, f)) and not f.startswith('__')]