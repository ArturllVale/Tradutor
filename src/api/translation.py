from g4f.client import Client
import logging

async def traduzir_com_retry(mensagem, max_retries=3):
    """Tenta traduzir com retry em caso de falha"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            client = Client()
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Traduza para o português do Brasil: {mensagem}"}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Erro na tentativa {retry_count + 1}: {e}")
            retry_count += 1
            if retry_count == max_retries:
                return None
    return None

async def traduzir_texto_llama(texto, idioma_origem, modelo_selecionado):
    """Função para tradução usando o modelo selecionado"""
    try:
        client = Client()
        if idioma_origem == "Inglês":
            prompt = f"Traduza o seguinte texto do inglês para o português do Brasil, mantendo o significado original: {texto}"
        else:
            prompt = f"Traduza o seguinte texto para o português do Brasil, mantendo o significado original: {texto}"

        response = await client.chat.completions.create(
            model=modelo_selecionado,
            messages=[{"role": "user", "content": prompt}]
        )
        
        traducao = response.choices[0].message.content
        
        # Limpar a tradução
        traducao = traducao.replace('"', '').strip()
        if traducao.lower().startswith("tradução:"):
            traducao = traducao[9:].strip()
        
        return traducao
    except Exception as e:
        logging.error(f"Erro na tradução: {e}")
        return None
