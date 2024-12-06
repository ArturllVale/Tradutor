import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asyncio
import os
from ..api.divine_pride import test_api_connection
from ..database.translator import translate_file

def select_file(label):
    """Função para selecionar arquivo"""
    filename = filedialog.askopenfilename(
        title="Selecione o arquivo",
        filetypes=[("YAML files", "*.yml"), ("All files", "*.*")]
    )
    if filename:
        label.config(text=filename)
        return filename
    return None

def create_tab_content(tab, base_url, tipo):
    """Cria o conteúdo comum das abas de tradução"""
    frame = ttk.Frame(tab)
    frame.pack(fill='both', expand=True, padx=10, pady=5)

    # Frame para API Key
    api_frame = ttk.LabelFrame(frame, text="Configuração da API")
    api_frame.pack(fill='x', padx=5, pady=5)

    ttk.Label(api_frame, text="Divine Pride API Key:").pack(side='left', padx=5)
    api_key_entry = ttk.Entry(api_frame, width=40)
    api_key_entry.pack(side='left', padx=5)

    # Frame para seleção de arquivo
    file_frame = ttk.LabelFrame(frame, text="Seleção de Arquivo")
    file_frame.pack(fill='x', padx=5, pady=5)

    file_label = ttk.Label(file_frame, text="Nenhum arquivo selecionado")
    file_label.pack(side='left', padx=5, fill='x', expand=True)

    def select_file_wrapper():
        select_file(file_label)

    ttk.Button(file_frame, text="Selecionar Arquivo", command=select_file_wrapper).pack(side='right', padx=5)

    # Barra de progresso
    progress_frame = ttk.Frame(frame)
    progress_frame.pack(fill='x', padx=5, pady=5)
    
    progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
    progress_bar.pack(fill='x', expand=True, side='left', padx=(0, 5))
    
    status_label = ttk.Label(progress_frame, text="")
    status_label.pack(side='left')

    # Botão de tradução
    def translate():
        api_key = api_key_entry.get().strip()
        input_file = file_label.cget("text")

        if input_file == "Nenhum arquivo selecionado":
            messagebox.showerror("Erro", "Por favor, selecione um arquivo para traduzir.")
            return

        if not api_key and base_url:
            messagebox.showerror("Erro", "Por favor, insira sua API Key do Divine Pride.")
            return

        if base_url and not test_api_connection(api_key, base_url):
            messagebox.showerror("Erro", "Falha na conexão com a API. Verifique sua API Key.")
            return

        # Iniciar tradução
        translate_file(api_key, input_file, progress_bar, status_label, base_url)

    ttk.Button(frame, text="Traduzir", command=translate).pack(pady=10)
