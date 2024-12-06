import tkinter as tk
from tkinter import ttk, filedialog
from ...api.divine_pride import ITEM_BASE_URL
from ..common import create_tab_content

def create_item_tab(tab):
    """Cria a aba de tradução de item_db"""
    create_tab_content(tab, ITEM_BASE_URL, "item_db")
