import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from database import get_consulta_cnpj, save_consulta_cnpj

# Carrega as variáveis de ambiente do arquivo .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()


def get_api_key() -> Optional[str]:
    """Retorna a chave da API CNPJA do arquivo .env."""
    api_key = os.getenv("CNPJA_API_KEY")
    
    # Remove espaços em branco e quebras de linha
    if api_key:
        api_key = api_key.strip()
    
    return api_key


def consultar_cnpj(cnpj: str, usar_cache: bool = True, forcar_atualizacao: bool = False) -> Dict[str, Any]:
    """
    Consulta dados cadastrais de uma empresa pelo CNPJ usando a API CNPJA.
    Verifica primeiro no cache local antes de fazer requisição à API.
    
    Args:
        cnpj: CNPJ da empresa (com ou sem formatação)
        usar_cache: Se True, verifica cache antes de consultar API
        forcar_atualizacao: Se True, força nova consulta mesmo se existir no cache
    
    Returns:
        Dicionário com os dados cadastrais da empresa
    
    Raises:
        ValueError: Se a chave da API não estiver configurada
        requests.RequestException: Se houver erro na requisição
    """
    # Remove formatação do CNPJ
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    
    if len(cnpj_clean) != 14:
        raise ValueError("CNPJ inválido. Deve conter 14 dígitos.")
    
    # Verifica cache primeiro (se não forçar atualização)
    if usar_cache and not forcar_atualizacao:
        dados_cached = get_consulta_cnpj(cnpj_clean)
        if dados_cached:
            return dados_cached
    
    # Se não encontrou no cache ou forçou atualização, consulta API
    api_key = get_api_key()
    
    if not api_key:
        env_file = Path(__file__).parent / ".env"
        if not env_file.exists():
            raise ValueError(
                f"Arquivo .env não encontrado. Crie o arquivo .env na raiz do projeto com: CNPJA_API_KEY=sua_chave_aqui"
            )
        raise ValueError(
            "A chave da API CNPJA não está configurada. Verifique o arquivo .env e a variável CNPJA_API_KEY."
        )
    
    # URL da API CNPJA - endpoint para consulta de empresa
    url = f"https://api.cnpja.com/office/{cnpj_clean}"
    
    # A API CNPJA usa token direto (sem Bearer)
    headers = {
        "Authorization": api_key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            # Remove metadados de cache se existirem antes de salvar
            dados_clean = {k: v for k, v in dados.items() if not k.startswith("_")}
            # Salva no cache
            save_consulta_cnpj(cnpj_clean, dados_clean)
            return dados
        elif response.status_code == 404:
            raise ValueError("CNPJ não encontrado na base de dados.")
        elif response.status_code == 401:
            error_msg = "Chave de API inválida ou expirada."
            try:
                error_data = response.json()
                if error_data.get("message"):
                    error_msg += f" Detalhes: {error_data['message']}"
            except:
                pass
            raise ValueError(error_msg)
        elif response.status_code == 429:
            raise ValueError("Limite de requisições excedido. Tente novamente mais tarde.")
        else:
            # Tenta obter mais informações do erro
            try:
                error_data = response.json()
                error_msg = error_data.get("message", f"Erro HTTP {response.status_code}")
            except:
                error_msg = f"Erro HTTP {response.status_code}"
            raise ValueError(f"Erro na requisição: {error_msg}")
            
    except requests.exceptions.Timeout:
        raise ValueError("Tempo de espera excedido. Tente novamente mais tarde.")
    except requests.exceptions.ConnectionError:
        raise ValueError("Erro de conexão. Verifique sua conexão com a internet.")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Erro ao consultar CNPJ: {str(e)}")
