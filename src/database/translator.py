import asyncio
import aiohttp
from pathlib import Path
from ruamel.yaml import YAML
import logging
from ..api.divine_pride import process_batch
from ..api.translation import traduzir_com_retry

# Inicializar o objeto YAML
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

BATCH_SIZE = 10  # Número de requisições simultâneas

async def translate_file_async(api_key, input_file, progress_bar, status_label, base_url=None):
    """Versão assíncrona da função de tradução."""
    try:
        # Carregar o arquivo YAML
        with open(input_file, 'r', encoding='utf-8') as f:
            data = yaml.load(f)

        if not data:
            status_label.config(text="Arquivo vazio ou inválido")
            return

        # Configurar a barra de progresso
        total_items = len(data)
        progress_bar['maximum'] = total_items
        progress_bar['value'] = 0
        
        # Processar os itens
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with aiohttp.ClientSession() as session:
            for i in range(0, total_items, BATCH_SIZE):
                batch = list(data.items())[i:i + BATCH_SIZE]
                batch_ids = [item_id for item_id, _ in batch]
                
                if base_url:
                    # Buscar dados da API
                    results = await process_batch(session, base_url, batch_ids, api_key, headers)
                    
                    # Atualizar dados com informações da API
                    for item_id, api_data in results:
                        if api_data and str(item_id) in data:
                            item = data[str(item_id)]
                            if 'name' in api_data:
                                translated_name = await traduzir_com_retry(api_data['name'])
                                if translated_name:
                                    item['name'] = translated_name
                else:
                    # Traduzir diretamente do arquivo
                    for item_id, item in batch:
                        if 'name' in item:
                            translated_name = await traduzir_com_retry(item['name'])
                            if translated_name:
                                item['name'] = translated_name
                
                # Atualizar progresso
                progress_bar['value'] = min(i + BATCH_SIZE, total_items)
                status_label.config(text=f"Processando... {progress_bar['value']}/{total_items}")
                
        # Salvar o arquivo traduzido
        output_file = str(Path(input_file).with_suffix('')) + '_traduzido.yml'
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        
        status_label.config(text="Tradução concluída!")
        
    except Exception as e:
        logging.error(f"Erro durante a tradução: {e}")
        status_label.config(text=f"Erro: {str(e)}")
        progress_bar['value'] = 0

def translate_file(api_key, input_file, progress_bar, status_label, base_url=None):
    """Wrapper para executar a função assíncrona em uma thread."""
    if asyncio.get_event_loop().is_closed():
        asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(
        translate_file_async(api_key, input_file, progress_bar, status_label, base_url)
    )
