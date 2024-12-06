import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import logging
from ...api.translation import traduzir_texto_llama

def create_npc_tab(tab):
    """Cria a aba de tradução de scripts NPC"""
    main_frame = ttk.Frame(tab, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Configuração
    config_frame = ttk.LabelFrame(main_frame, text="Configuração da Tradução", padding="5")
    config_frame.pack(fill=tk.X, pady=(0, 10))

    # Lista de modelos disponíveis
    modelos = [
        "gpt-4o", "gpt-4", "gpt-4o-mini", "gpt-4-turbo",
        "llama-3.1-70b", "claude-3.5-sonnet", "hermes-3"
    ]

    # Frame para modelo
    modelo_frame = ttk.Frame(config_frame)
    modelo_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(modelo_frame, text="Modelo:").pack(side=tk.LEFT, padx=(0, 10))
    modelo_var = tk.StringVar(value="gpt-4o-mini")  # Modelo padrão
    modelo_combo = ttk.Combobox(modelo_frame, textvariable=modelo_var, values=modelos, state="readonly")
    modelo_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Dropdown para seleção de idioma
    idioma_frame = ttk.Frame(config_frame)
    idioma_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(idioma_frame, text="Idioma de origem:").pack(side=tk.LEFT, padx=(0, 10))
    idiomas = ["Inglês", "Outro idioma"]
    idioma_var = tk.StringVar(value=idiomas[0])
    idioma_combo = ttk.Combobox(idioma_frame, textvariable=idioma_var, values=idiomas, state="readonly")
    idioma_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Seleção de arquivo
    file_frame = ttk.LabelFrame(main_frame, text="Seleção de Arquivo", padding="5")
    file_frame.pack(fill=tk.X, pady=(0, 10))

    file_entry = ttk.Label(file_frame, text="Nenhum arquivo selecionado", wraplength=350)
    file_entry.pack(fill=tk.X, padx=5, pady=5)

    selected_file = None

    def select_text_file():
        nonlocal selected_file
        filename = filedialog.askopenfilename(filetypes=[("Arquivos de texto", "*.txt")])
        if filename:
            truncated_path = f".../{os.path.basename(filename)}"
            file_entry.config(text=truncated_path)
            selected_file = filename
            translate_button.config(state="normal")

    select_button = ttk.Button(file_frame, text="Selecionar arquivo", command=select_text_file)
    select_button.pack(pady=5)

    # Progresso
    progress_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="5")
    progress_frame.pack(fill=tk.X, pady=(0, 10))

    status_label = ttk.Label(progress_frame, text="Aguardando arquivo...", wraplength=350)
    status_label.pack(fill=tk.X, padx=5, pady=5)

    progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
    progress_bar.pack(fill=tk.X, padx=5, pady=5)

    def traduzir_arquivo():
        if not selected_file:
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo para traduzir!")
            return

        # Desabilitar o botão durante a tradução
        translate_button.config(state="disabled")
        
        def processo_traducao():
            try:
                # Ler o arquivo
                with open(selected_file, 'r', encoding='utf-8') as file:
                    texto = file.read()

                if not texto.strip():
                    tab.after(0, lambda: messagebox.showwarning("Aviso", "O arquivo está vazio!"))
                    tab.after(0, lambda: translate_button.config(state="normal"))
                    return

                # Atualizar interface
                tab.after(0, lambda: status_label.config(text="Iniciando tradução..."))
                tab.after(0, lambda: progress_bar.configure(value=10))

                # Traduzir o texto
                traducao = traduzir_texto_llama(texto, idioma_var.get(), modelo_var.get())

                if not traducao:
                    raise Exception("A tradução retornou vazia")

                # Criar diretório de saída se não existir
                output_dir = "traduzido"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # Salvar tradução
                base_name = os.path.basename(selected_file)
                nome_traduzido = os.path.join(output_dir, f"traduzido_{base_name}")
                
                with open(nome_traduzido, 'w', encoding='utf-8') as file:
                    file.write(traducao)

                # Atualizar interface
                tab.after(0, lambda: progress_bar.configure(value=100))
                tab.after(0, lambda: status_label.config(text=f"Tradução concluída! Arquivo salvo em: {nome_traduzido}"))
                tab.after(0, lambda: messagebox.showinfo("Sucesso", "Tradução concluída com sucesso!"))

            except Exception as e:
                logging.error(f"Erro durante a tradução: {e}")
                tab.after(0, lambda: messagebox.showerror("Erro", f"Erro durante a tradução: {str(e)}"))
                tab.after(0, lambda: status_label.config(text="Erro durante a tradução"))
                tab.after(0, lambda: progress_bar.configure(value=0))
            finally:
                # Reabilitar o botão após a tradução
                tab.after(0, lambda: translate_button.config(state="normal"))

        # Iniciar thread de tradução
        threading.Thread(target=processo_traducao, daemon=True).start()

    # Botão de tradução
    translate_button = ttk.Button(main_frame, text="Traduzir arquivo", command=traduzir_arquivo, state="disabled")
    translate_button.pack(pady=10)

    return main_frame
