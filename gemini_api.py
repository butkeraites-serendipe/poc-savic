"""
Módulo para integração com Google Gemini API via REST.
Avalia compatibilidade de CNAEs de empresas.
"""

import os
import json
import re
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


def get_api_key() -> Optional[str]:
    """
    Obtém a chave da API do arquivo .env.
    Tenta VERTEX_AI_API_KEY primeiro, depois GEMINI_API_KEY.
    """
    api_key = os.getenv("VERTEX_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    return api_key


def avaliar_compatibilidade_cnaes(
    cnaes_principal: Dict[str, Any],
    cnaes_secundarias: List[Dict[str, Any]],
    razao_social: Optional[str] = None,
    nome_fantasia: Optional[str] = None
) -> Dict[str, Any]:
    """
    Avalia a compatibilidade dos CNAEs de uma empresa usando Gemini.
    
    Args:
        cnaes_principal: Dicionário com CNAE principal (id, text)
        cnaes_secundarias: Lista de dicionários com CNAEs secundários
        razao_social: Razão social da empresa (opcional)
        nome_fantasia: Nome fantasia da empresa (opcional)
    
    Returns:
        Dicionário com resultado da avaliação:
        {
            "compativel": bool,
            "score": float (0-100),
            "analise": str,
            "observacoes": List[str],
            "erro": Optional[str]
        }
    """
    api_key = get_api_key()
    
    if not api_key:
        return {
            "compativel": None,
            "score": None,
            "analise": "",
            "observacoes": [],
            "erro": "Chave da API Gemini não configurada. Configure VERTEX_AI_API_KEY ou GEMINI_API_KEY no arquivo .env"
        }
    
    try:
        # Usar API REST do Gemini diretamente
        model = "gemini-2.5-flash"
        api_version = "v1beta"
        
        # Preparar informações dos CNAEs
        cnae_principal_texto = f"{cnaes_principal.get('id', '')} - {cnaes_principal.get('text', '')}"
        
        # Incluir todos os CNAEs secundários sem limitação
        cnaes_secundarios_texto = ""
        if cnaes_secundarias:
            cnaes_secundarios_texto = "\n".join([
                f"- {cnae.get('id', '')} - {cnae.get('text', '')}"
                for cnae in cnaes_secundarias
            ])
        
        # Construir prompt
        empresa_info = ""
        if razao_social:
            empresa_info += f"Razão Social: {razao_social}\n"
        if nome_fantasia:
            empresa_info += f"Nome Fantasia: {nome_fantasia}\n"
        
        prompt = f"""Você é um especialista em análise de empresas e CNAEs (Classificação Nacional de Atividades Econômicas).

Analise a compatibilidade entre os CNAEs da empresa abaixo e forneça uma avaliação detalhada.

INFORMAÇÕES DA EMPRESA:
{empresa_info}

CNAE PRINCIPAL:
{cnae_principal_texto}

CNAEs SECUNDÁRIOS:
{cnaes_secundarios_texto if cnaes_secundarios_texto else "Nenhum CNAE secundário informado."}

TAREFA:
1. Avalie se os CNAEs secundários são compatíveis e coerentes com o CNAE principal
2. Verifique se há alguma inconsistência ou atividade incompatível
3. Identifique possíveis riscos ou observações importantes
4. Atribua uma pontuação de 0 a 100, onde:
   - 90-100: Totalmente compatível e coerente
   - 70-89: Compatível com pequenas observações
   - 50-69: Compatível mas com algumas inconsistências
   - 30-49: Pouco compatível, requer atenção
   - 0-29: Incompatível ou suspeito

FORMATO DA RESPOSTA (JSON):
{{
    "compativel": true/false,
    "score": número de 0 a 100,
    "analise": "análise detalhada em português (2-3 parágrafos)",
    "observacoes": ["observação 1", "observação 2", ...]
}}

Responda APENAS com o JSON, sem texto adicional antes ou depois."""

        # Fazer chamada à API REST do Gemini
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
        
        data = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192
            }
        }
        
        response = requests.post(url, json=data, timeout=30)
        
        # Verificar se houve erro na requisição
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", str(response.text))
            except:
                error_detail = response.text[:200]
            
            # Mensagem mais clara para erro 401
            if response.status_code == 401:
                error_msg = f"Erro de autenticação (401): A API key fornecida não é válida para esta API. "
                error_msg += "A API REST do Gemini requer uma API key do Google AI Studio (não Vertex AI). "
                error_msg += f"Detalhes: {error_detail}"
            else:
                error_msg = f"Erro na API Gemini ({response.status_code}): {error_detail}"
            
            return {
                "compativel": None,
                "score": None,
                "analise": "",
                "observacoes": [],
                "erro": error_msg
            }
        
        result = response.json()
        
        # Extrair texto da resposta
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            
            # Verificar se foi truncado (apenas avisar, não bloquear)
            finish_reason = candidate.get("finishReason", "")
            if finish_reason == "MAX_TOKENS":
                # Continuar mesmo se truncado, pode ter informação útil
                pass
            
            if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
                resposta_texto = candidate["content"]["parts"][0].get("text", "")
                if not resposta_texto:
                    return {
                        "compativel": None,
                        "score": None,
                        "analise": "",
                        "observacoes": [],
                        "erro": f"Resposta vazia. Candidate: {candidate}"
                    }
            else:
                return {
                    "compativel": None,
                    "score": None,
                    "analise": "",
                    "observacoes": [],
                    "erro": f"Estrutura de resposta inesperada. Candidate: {candidate}"
                }
        else:
            return {
                "compativel": None,
                "score": None,
                "analise": "",
                "observacoes": [],
                "erro": f"Resposta inesperada da API: {result}"
            }
        
        # Parsear resposta JSON
        # Extrair JSON da resposta (pode ter markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', resposta_texto)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = resposta_texto
        
        resultado = json.loads(json_str)
        
        return {
            "compativel": resultado.get("compativel", False),
            "score": resultado.get("score", 0),
            "analise": resultado.get("analise", ""),
            "observacoes": resultado.get("observacoes", []),
            "erro": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "compativel": None,
            "score": None,
            "analise": "",
            "observacoes": [],
            "erro": f"Erro ao processar resposta do Gemini: {str(e)}. Resposta recebida: {resposta_texto[:200]}"
        }
    except Exception as e:
        return {
            "compativel": None,
            "score": None,
            "analise": "",
            "observacoes": [],
            "erro": f"Erro ao consultar Gemini: {str(e)}"
        }

