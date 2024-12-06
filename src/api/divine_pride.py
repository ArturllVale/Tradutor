import logging
import aiohttp
import json
from pathlib import Path

# Configuração do cache
CACHE_DIR = Path.home() / '.mobdb_cache'
CACHE_DIR.mkdir(exist_ok=True)
MAX_RETRIES = 3  # Número máximo de tentativas para cada requisição

# URLs base para cada tipo
MONSTER_BASE_URL = 'https://www.divine-pride.net/api/database/Monster/'
ITEM_BASE_URL = 'https://www.divine-pride.net/api/database/Item/'

def get_cached_data(data_id, api_key, data_type):
    """Recupera dados do cache local."""
    cache_file = CACHE_DIR / f"{data_type}_{data_id}.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_to_cache(data_id, data, data_type):
    """Salva dados no cache local."""
    cache_file = CACHE_DIR / f"{data_type}_{data_id}.json"
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

async def fetch_data(session, base_url, data_id, api_key, headers, retries=0):
    """Função assíncrona para buscar dados específicos."""
    url = f"{base_url}{data_id}?apiKey={api_key}"
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                save_to_cache(data_id, data, 'monster' if 'Monster' in base_url else 'item')
                return data_id, data
            elif response.status == 429 and retries < MAX_RETRIES:  # Rate limit
                await asyncio.sleep(1 * (retries + 1))
                return await fetch_data(session, base_url, data_id, api_key, headers, retries + 1)
            else:
                return data_id, None
    except Exception as e:
        logging.error(f"Erro ao buscar ID {data_id}: {e}")
        if retries < MAX_RETRIES:
            await asyncio.sleep(1 * (retries + 1))
            return await fetch_data(session, base_url, data_id, api_key, headers, retries + 1)
        return data_id, None

async def process_batch(session, base_url, batch_ids, api_key, headers):
    """Processa um lote de IDs."""
    tasks = []
    data_type = 'monster' if 'Monster' in base_url else 'item'
    for data_id in batch_ids:
        cached_data = get_cached_data(data_id, api_key, data_type)
        if cached_data:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
        else:
            tasks.append(asyncio.create_task(
                fetch_data(session, base_url, data_id, api_key, headers)
            ))
    
    return await asyncio.gather(*tasks)

def test_api_connection(api_key, base_url):
    """Testa a conexão com a API."""
    try:
        test_url = f"{base_url}1?apiKey={api_key}"
        response = aiohttp.ClientSession().head(test_url)
        if response.status == 200:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Erro ao testar conexão com API: {e}")
        return False
