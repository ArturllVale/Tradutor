import tkinter as tk
from tkinter import ttk
import asyncio
from ...api.translation import traduzir_texto_llama

def create_text_translation_tab(tab):
    """Cria a aba de tradução de texto livre"""
    # Frame superior para controles
    control_frame = ttk.Frame(tab)
    control_frame.pack(fill='x', padx=5, pady=5)

    # Combobox para seleção de idioma
    ttk.Label(control_frame, text="Idioma de origem:").pack(side='left', padx=5)
    idioma_var = tk.StringVar(value="Inglês")
    idioma_combo = ttk.Combobox(control_frame, textvariable=idioma_var, values=["Inglês", "Outros"], state="readonly")
    idioma_combo.pack(side='left', padx=5)

    # Combobox para seleção de modelo
    ttk.Label(control_frame, text="Modelo:").pack(side='left', padx=5)
    modelo_var = tk.StringVar(value="gpt-3.5-turbo")
    modelo_combo = ttk.Combobox(control_frame, textvariable=modelo_var, 
                               values=["gpt-3.5-turbo", "gpt-4", "llama2-7b", "claude-2"], 
                               state="readonly")
    modelo_combo.pack(side='left', padx=5)

    # Frame para os campos de texto
    text_frame = ttk.Frame(tab)
    text_frame.pack(fill='both', expand=True, padx=5, pady=5)

    # Campo de texto original
    ttk.Label(text_frame, text="Texto Original:").pack(fill='x')
    texto_original = tk.Text(text_frame, height=10)
    texto_original.pack(fill='both', expand=True, pady=5)

    # Campo de texto traduzido
    ttk.Label(text_frame, text="Tradução:").pack(fill='x')
    texto_traduzido = tk.Text(text_frame, height=10)
    texto_traduzido.pack(fill='both', expand=True, pady=5)

    # Função assíncrona para tradução
    async def traduzir_async():
        texto = texto_original.get("1.0", tk.END).strip()
        if texto:
            traducao = await traduzir_texto_llama(
                texto, 
                idioma_var.get(),
                modelo_var.get()
            )
            if traducao:
                texto_traduzido.delete("1.0", tk.END)
                texto_traduzido.insert("1.0", traducao)

    # Função wrapper para chamar a função assíncrona
    def traduzir():
        if asyncio.get_event_loop().is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(traduzir_async())

    ttk.Button(tab, text="Traduzir", command=traduzir).pack(pady=10)
