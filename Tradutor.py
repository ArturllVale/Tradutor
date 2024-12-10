#  __                       |
# |  |   _ _ _____ ___ ___  |
# |  |__| | |     | -_|   | |
# |_____|___|_|_|_|___|_|_| |
#         lumen#0110        |
#        2024 - 2025        |
#___________________________|
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import threading
import time
from functools import lru_cache
from g4f.client import Client
import json
from pathlib import Path
import asyncio
import aiohttp
from ruamel.yaml import YAML

# Configurar o logging
logging.basicConfig(level=logging.INFO)

# Inicializar o objeto YAML
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

# Configuração do cache
CACHE_DIR = Path.home() / '.mobdb_cache'
CACHE_TTL = 86400  # Tempo de expiração do cache em segundos (1 dia)
CACHE_DIR.mkdir(exist_ok=True)
BATCH_SIZE = 20  # Número de requisições simultâneas
MAX_RETRIES = 3  # Número máximo de tentativas para cada requisição 

# URLs base para cada tipo
MONSTER_BASE_URL = 'https://www.divine-pride.net/api/database/Monster/'
ITEM_BASE_URL = 'https://www.divine-pride.net/api/database/Item/'

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@lru_cache(maxsize=1000)
def get_cached_data(data_id, api_key, data_type):
    """Recupera dados do cache local, verificando a validade (TTL)."""
    cache_file = CACHE_DIR / f"{data_type}_{api_key}_{data_id}.json"  # Inclui api_key na chave
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if time.time() - data.get('timestamp', 0) < CACHE_TTL:
                    return data['data']
        except (json.JSONDecodeError, KeyError):
            pass  # Ignora dados inválidos ou expirados
    return None  # Retorna None se não encontrado ou inválido

def save_to_cache(data_id, data, data_type):
    """Salva dados no cache local."""
    cache_file = CACHE_DIR / f"{data_type}_{api_key}_{data_id}.json"  # Inclui api_key na chave
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump({'data': data, 'timestamp': time.time()}, f) 

async def fetch_data(session, base_url, data_id, api_key, headers, retries=0):
    """Função assíncrona para buscar dados específicos."""
    url = f"{base_url}{data_id}?apiKey={api_key}"
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                save_to_cache(data_id, data, 'monster' if 'Monster' in base_url else 'item')
                return data_id, data  # Retorna os dados se a requisição for bem-sucedida
            elif response.status == 429:  # Rate limit
                if retries < MAX_RETRIES:
                    await asyncio.sleep(1 * (retries + 1))  # Aguarda antes de tentar novamente
                    return await fetch_data(session, base_url, data_id, api_key, headers, retries + 1)
                else:
                    logging.error(f"Rate limit excedido para ID {data_id}.")
                    return data_id, None  # Retorna None se o limite de tentativas for atingido
            else:
                logging.error(f"Erro ao buscar ID {data_id}: Código de status {response.status}")
                return data_id, None  # Retorna None se houver um erro na requisição
    except aiohttp.ClientError as e:
        logging.error(f"Erro de conexão ao buscar ID {data_id}: {e}")
        if retries < MAX_RETRIES:
            await asyncio.sleep(1 * (retries + 1))  # Aguarda antes de tentar novamente
            return await fetch_data(session, base_url, data_id, api_key, headers, retries + 1)
        return data_id, None  # Retorna None se o limite de tentativas for atingido

async def process_batch(session, base_url, batch_ids, api_key, headers):
    """Processa um lote de IDs."""
    tasks = []
    for data_id in batch_ids: 
        cached_data = get_cached_data(data_id, api_key, 'monster' if 'Monster' in base_url else 'item')
        if cached_data:  
            tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Pula se estiver no cache
        else: 
            tasks.append(asyncio.create_task(
                fetch_data(session, base_url, data_id, api_key, headers)
            ))
    
    return await asyncio.gather(*tasks)

def test_api_connection(api_key, base_url):
    """Testa a conexão com a API usando aiohttp."""
    async def _test_connection():
        try:
            test_url = f"{base_url}1?apiKey={api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.head(test_url) as response:
                    return response.status == 200
        except aiohttp.ClientError as e:
            logging.error(f"Erro ao conectar à API: {e}")
            return False

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_test_connection())

async def translate_file_async(api_key, input_file, progress_bar, status_label, base_url):
    """Versão assíncrona da função de tradução."""
    if not api_key or not input_file:
        messagebox.showerror("Erro", "Por favor, verifique a chave da API e o arquivo selecionado.")
        return

    headers = {'Accept-Language': 'pt-BR'}

    if not test_api_connection(api_key, base_url):
        messagebox.showerror("Erro", "Não foi possível conectar ao host da API. Verifique a conexão.")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
            if not content.strip():  # Verifica se o arquivo está vazio
                messagebox.showwarning("Aviso", "O arquivo selecionado está vazio.")
                return

            data = yaml.load(file)

        total_items = len(data['Body'])
        progress_bar['maximum'] = total_items
        progress = 0

        monster_ids = [item['Id'] for item in data['Body']]
        batches = [monster_ids[i:i + BATCH_SIZE] for i in range(0, len(monster_ids), BATCH_SIZE)]

        async with aiohttp.ClientSession() as session:
            for batch in batches:
                status_label.config(text=f"Processando lote... ({progress}/{total_items})")
                
                results = await process_batch(session, base_url, batch, api_key, headers)
                
                for data_id, response_data in results:
                    if response_data: 
                        if 'name' in response_data and response_data['name']:  # Verifica se 'name' existe e não é vazio
                            for item in data['Body']:
                                if item['Id'] == data_id:
                                    item['Name'] = response_data['name']
                                    break
                        else:
                            logging.warning(f"Resposta vazia para ID {data_id}.")
                    
                    progress += 1
                    progress_bar['value'] = progress

        if not os.path.exists('traduzido'):
            os.makedirs('traduzido')

        output_file = os.path.join('traduzido', os.path.basename(input_file))
        with open(output_file, 'w', encoding='utf-8') as file:
            yaml.dump(data, file)

        status_label.config(text="Tradução concluída!")
        messagebox.showinfo("Sucesso", "A tradução foi concluída com sucesso!")

    except Exception as e:
        logging.error(f"Erro durante a tradução: {e}")
        messagebox.showerror("Erro", f"Ocorreu um erro durante a tradução: {str(e)}")

def select_file(label):
    global selected_file
    filename = filedialog.askopenfilename(filetypes=[("Arquivos YAML", "*.yml")])
    if filename:
        truncated_path = f".../{os.path.basename(filename)}"
        label.config(text=truncated_path)
        selected_file = filename

def create_tab_content(tab, base_url, tipo):
    """Cria o conteúdo de uma aba."""
    main_frame = ttk.Frame(tab, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    api_frame = ttk.LabelFrame(main_frame, text="Configuração da API", padding="5")
    api_frame.pack(fill=tk.X, pady=(0, 10))
    
    api_key_entry = ttk.Entry(api_frame)
    api_key_entry.pack(fill=tk.X, padx=5, pady=5)

    file_frame = ttk.LabelFrame(main_frame, text=f"Seleção de Arquivo {tipo}", padding="5")
    file_frame.pack(fill=tk.X, pady=(0, 10))

    file_entry = ttk.Label(file_frame, text="Nenhum .yml selecionado", wraplength=350)
    file_entry.pack(fill=tk.X, padx=5, pady=5)

    select_button = ttk.Button(file_frame, text="Selecionar arquivo", command=lambda: select_file(file_entry))
    select_button.pack(pady=5)

    progress_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="5")
    progress_frame.pack(fill=tk.X, pady=(0, 10))

    status_label = ttk.Label(progress_frame, text="Aguardando início...", wraplength=350)
    status_label.pack(fill=tk.X, padx=5, pady=5)

    progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
    progress_bar.pack(fill=tk.X, padx=5, pady=5)

    translate_button = ttk.Button(main_frame, text=f"Traduzir {tipo}", 
                              command=lambda: threading.Thread(
                                  target=lambda: asyncio.run(translate_file_async(api_key_entry.get(), selected_file, progress_bar, status_label, base_url)),
                                  args=(api_key_entry.get(), selected_file, progress_bar, status_label, base_url)
                              ).start())
    translate_button.pack(pady=10)

    return main_frame

def traduzir_com_retry(mensagem, max_retries=3):
    """Tenta traduzir com retry em caso de falha"""
    for attempt in range(max_retries):
        try:
            resposta = Client().chat.completions.create(
                model="llama-3.1-70b",
                messages=[{"role": "user", "content": mensagem}]
            )
            if resposta and isinstance(resposta, str) and len(resposta.strip()) > 0:
                return resposta
            time.sleep(1)  # Pequeno delay entre tentativas
        except Exception as e:
            logging.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Delay maior entre tentativas após falha
            continue
    
    raise Exception("Todas as tentativas de tradução falharam")

def traduzir_texto_llama(texto, idioma_origem, modelo_selecionado):
    """Função para tradução usando o modelo selecionado"""
    try:
        client = Client()
        
        if idioma_origem == "Inglês":
            mensagem = (
                "Traduza o seguinte conteúdo do inglês para o português, "
                "preservando a estrutura, variáveis, identificadores e formatação, "
                "e mantendo termos de programação (como if, for, while, else, etc.) em inglês:\n" + texto
            )
        else:
            mensagem = (
                "Traduza o seguinte conteúdo para o português, "
                "preservando a estrutura, variáveis, identificadores e formatação, "
                "e mantendo termos técnicos e de programação no idioma original:\n" + texto
            )

        resposta = client.chat.completions.create(
            model=modelo_selecionado,
            messages=[{"role": "user", "content": mensagem}]
        )

        return resposta.choices[0].message.content
    except Exception as e:
        print("Erro ao traduzir:", e)
        return "Erro ao traduzir."

def create_text_translation_tab(tab):
    main_frame = ttk.Frame(tab, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Configuração
    config_frame = ttk.LabelFrame(main_frame, text="Configuração da Tradução", padding="5")
    config_frame.pack(fill=tk.X, pady=(0, 10))

    # Lista de modelos disponíveis (sem duplicatas)
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

    def select_text_file():
        global selected_file
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
                    root.after(0, lambda: messagebox.showwarning("Aviso", "O arquivo está vazio!"))
                    root.after(0, lambda: translate_button.config(state="normal"))
                    return

                # Atualizar interface na thread principal
                root.after(0, lambda: status_label.config(text="Iniciando tradução..."))
                root.after(0, lambda: progress_bar.configure(value=10))

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

                # Atualizar interface na thread principal
                root.after(0, lambda: progress_bar.configure(value=100))
                root.after(0, lambda: status_label.config(text=f"Tradução concluída! Arquivo salvo em: {nome_traduzido}"))
                root.after(0, lambda: messagebox.showinfo("Sucesso", "Tradução concluída com sucesso!"))

            except Exception as e:
                logging.error(f"Erro durante a tradução: {e}")
                root.after(0, lambda: messagebox.showerror("Erro", f"Erro durante a tradução: {str(e)}"))
                root.after(0, lambda: status_label.config(text="Erro durante a tradução"))
                root.after(0, lambda: progress_bar.configure(value=0))
            finally:
                # Reabilitar o botão após a tradução
                root.after(0, lambda: translate_button.config(state="normal"))

        # Iniciar thread de tradução
        threading.Thread(target=processo_traducao, daemon=True).start()

    # Botão de tradução
    translate_button = ttk.Button(main_frame, text="Traduzir arquivo", command=traduzir_arquivo, state="disabled")
    translate_button.pack(pady=10)

    return main_frame

def create_gui():
    global root
    root = tk.Tk()
    root.geometry("400x500")  # Ajustado para o novo layout
    root.title("Tradutor RO")
    root.resizable(False, False)

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    monster_tab = ttk.Frame(notebook)
    notebook.add(monster_tab, text='Monstros')
    create_tab_content(monster_tab, MONSTER_BASE_URL, "Monstros")

    item_tab = ttk.Frame(notebook)
    notebook.add(item_tab, text='Itens')
    create_tab_content(item_tab, ITEM_BASE_URL, "Itens")

    text_tab = ttk.Frame(notebook)
    notebook.add(text_tab, text='Tradução de NPC')
    create_text_translation_tab(text_tab)

    credits_frame = ttk.Frame(root)
    credits_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    creditos_label = ttk.Label(credits_frame, text="Criado por: Lumen", anchor="center")
    creditos_label.pack()

    root.mainloop()

selected_file = None
create_gui()