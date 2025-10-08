"""
Classe base para todos os elementos visuais no VisionMap
"""

import tkinter as tk
from tkinter import simpledialog, colorchooser
from abc import ABC, abstractmethod


class VisualElement(ABC):
    """Classe abstrata base para todos os elementos visuais."""
    
    def __init__(self, canvas, x, y, width, height):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Atributos para controle de seleção e movimento
        self.selected = False
        self.offset_x = 0
        self.offset_y = 0
        
        # Lista de conexões
        self.connections = []
    
    @abstractmethod
    def contains_point(self, x, y):
        """Verifica se um ponto está dentro do elemento."""
        pass
    
    @abstractmethod
    def select(self, event_x, event_y):
        """Seleciona o elemento."""
        pass
    
    @abstractmethod
    def deselect(self):
        """Desseleciona o elemento."""
        pass
    
    @abstractmethod
    def move_to(self, x, y):
        """Move o elemento para coordenadas absolutas."""
        pass
    
    @abstractmethod
    def delete(self):
        """Remove o elemento do canvas."""
        pass
    
    @abstractmethod
    def get_state(self):
        """Retorna o estado do elemento para salvamento."""
        pass
    
    def bring_to_front(self):
        """Traz o elemento para a frente."""
        # Implementação padrão - subclasses devem sobrescrever
        pass
    
    def send_to_back(self):
        """Envia o elemento para trás."""
        # Implementação padrão - subclasses devem sobrescrever
        pass