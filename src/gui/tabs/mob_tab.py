import tkinter as tk
from tkinter import ttk, filedialog
from ...api.divine_pride import MONSTER_BASE_URL
from ..common import create_tab_content

def create_mob_tab(tab):
    """Cria a aba de tradução de mob_db"""
    create_tab_content(tab, MONSTER_BASE_URL, "mob_db")
