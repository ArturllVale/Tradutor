import tkinter as tk
from tkinter import ttk
from .tabs.mob_tab import create_mob_tab
from .tabs.item_tab import create_item_tab
from .tabs.npc_tab import create_npc_tab

def create_gui():
    """Cria a interface gráfica principal"""
    root = tk.Tk()
    root.title("RO Database Tradutor")
    root.geometry("600x400")  # Definindo o tamanho inicial da janela
    
    # Configurar o tema
    style = ttk.Style()
    style.theme_use('clam')
    
    # Criar notebook para as abas
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=5)
    
    # Criar as abas
    mob_tab = ttk.Frame(notebook)
    item_tab = ttk.Frame(notebook)
    npc_tab = ttk.Frame(notebook)
    
    notebook.add(mob_tab, text='Mob DB')
    notebook.add(item_tab, text='Item DB')
    notebook.add(npc_tab, text='Tradução de NPC')
    
    # Configurar o conteúdo de cada aba
    create_mob_tab(mob_tab)
    create_item_tab(item_tab)
    create_npc_tab(npc_tab)
    
    return root
