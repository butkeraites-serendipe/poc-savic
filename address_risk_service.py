"""
Módulo para análise de risco de endereço usando Gemini Vision.
Analisa imagens de endereços e verifica compatibilidade com CNAEs.
"""

import os
import json
import re
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

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


def analisar_imagem_endereco(
    image_bytes: bytes,
    cnaes: List[Dict[str, Any]],
    razao_social: Optional[str] = None,
    nome_fantasia: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analisa uma imagem de endereço usando Gemini Vision e avalia compatibilidade com CNAEs.
    
    Args:
        image_bytes: Bytes da imagem (JPEG, PNG, etc.)
        cnaes: Lista de dicionários com CNAEs da empresa
            [{"codigo": "6201-5/01", "descricao": "..."}, ...]
        razao_social: Razão social da empresa (opcional)
        nome_fantasia: Nome fantasia da empresa (opcional)
    
    Returns:
        Dicionário com resultado da análise:
        {
            "zona_aparente": "COMERCIAL | RESIDENCIAL | INDUSTRIAL | RURAL | INDEFINIDO",
            "tipo_via": "ASFALTADA | TERRA | NAO_VISIVEL",
            "presenca_placas_comerciais": bool,
            "presenca_vitrines_ou_lojas": bool,
            "presenca_casas_residenciais": bool,
            "compatibilidade_cnae": "ALTA | MEDIA | BAIXA | DESCONHECIDA",
            "motivos_incompatibilidade": List[str],
            "sugestao_nivel_risco": "ALTO | MEDIO | BAIXO",
            "analise_detalhada": str,
            "erro": Optional[str]
        }
    """
    api_key = get_api_key()
    
    if not api_key:
        return {
            "zona_aparente": "INDEFINIDO",
            "tipo_via": "NAO_VISIVEL",
            "presenca_placas_comerciais": False,
            "presenca_vitrines_ou_lojas": False,
            "presenca_casas_residenciais": False,
            "compatibilidade_cnae": "DESCONHECIDA",
            "motivos_incompatibilidade": [],
            "sugestao_nivel_risco": "MEDIO",
            "analise_detalhada": "",
            "erro": "Chave da API Gemini não configurada. Configure VERTEX_AI_API_KEY ou GEMINI_API_KEY no arquivo .env"
        }
    
    try:
        # Preparar informações dos CNAEs
        cnaes_texto = "\n".join([
            f"- {cnae.get('codigo', '')} - {cnae.get('descricao', '')}"
            for cnae in cnaes
        ])
        
        # Construir prompt
        empresa_info = ""
        if razao_social:
            empresa_info += f"Razão Social: {razao_social}\n"
        if nome_fantasia:
            empresa_info += f"Nome Fantasia: {nome_fantasia}\n"
        
        prompt = f"""Você é um assistente de análise de risco de cadastro de empresas.

Receber:
1) Uma imagem da fachada de um endereço.
2) Lista de CNAEs da empresa (abaixo).

Sua tarefa é:
- Descrever, de forma objetiva, o tipo de zona visível (residencial, comercial, industrial, rural).
- Avaliar se a fachada e o entorno aparentam ser compatíveis com os CNAEs.
- Detectar sinais de local possivelmente suspeito para sede da empresa, como:
  - Rua não asfaltada em área de casas simples.
  - Predominância de residências sem comércio.
  - Terreno vazio ou construção inacabada.
  - Ausência de placas comerciais ou identificação de empresa.

Responder APENAS em JSON com o seguinte formato:

{{
  "zona_aparente": "COMERCIAL | RESIDENCIAL | INDUSTRIAL | RURAL | INDEFINIDO",
  "tipo_via": "ASFALTADA | TERRA | NAO_VISIVEL",
  "presenca_placas_comerciais": true/false,
  "presenca_vitrines_ou_lojas": true/false,
  "presenca_casas_residenciais": true/false,
  "compatibilidade_cnae": "ALTA | MEDIA | BAIXA | DESCONHECIDA",
  "motivos_incompatibilidade": ["motivo1", "motivo2"],
  "sugestao_nivel_risco": "ALTO | MEDIO | BAIXO",
  "analise_detalhada": "análise textual detalhada em português (2-3 parágrafos)"
}}

INFORMAÇÕES DA EMPRESA:
{empresa_info}

CNAEs DA EMPRESA:
{cnaes_texto}

Responda APENAS com o JSON, sem texto adicional antes ou depois."""

        # Converter imagem para base64
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Determinar MIME type baseado no conteúdo (assumindo JPEG por padrão)
        mime_type = "image/jpeg"
        if image_bytes.startswith(b'\x89PNG'):
            mime_type = "image/png"
        elif image_bytes.startswith(b'GIF'):
            mime_type = "image/gif"
        elif image_bytes.startswith(b'WEBP'):
            mime_type = "image/webp"
        
        # Fazer chamada à API REST do Gemini com imagem
        model = "gemini-2.5-flash"
        api_version = "v1beta"
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096,
                "response_mime_type": "application/json"
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        
        # Verificar se houve erro na requisição
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", str(response.text))
            except:
                error_detail = response.text[:200]
            
            if response.status_code == 401:
                error_msg = f"Erro de autenticação (401): A API key fornecida não é válida. Detalhes: {error_detail}"
            else:
                error_msg = f"Erro na API Gemini ({response.status_code}): {error_detail}"
            
            return {
                "zona_aparente": "INDEFINIDO",
                "tipo_via": "NAO_VISIVEL",
                "presenca_placas_comerciais": False,
                "presenca_vitrines_ou_lojas": False,
                "presenca_casas_residenciais": False,
                "compatibilidade_cnae": "DESCONHECIDA",
                "motivos_incompatibilidade": [],
                "sugestao_nivel_risco": "MEDIO",
                "analise_detalhada": "",
                "erro": error_msg
            }
        
        result = response.json()
        
        # Extrair texto da resposta
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            
            finish_reason = candidate.get("finishReason", "")
            if finish_reason == "MAX_TOKENS":
                # Continuar mesmo se truncado
                pass
            
            if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
                resposta_texto = candidate["content"]["parts"][0].get("text", "")
                if not resposta_texto:
                    return {
                        "zona_aparente": "INDEFINIDO",
                        "tipo_via": "NAO_VISIVEL",
                        "presenca_placas_comerciais": False,
                        "presenca_vitrines_ou_lojas": False,
                        "presenca_casas_residenciais": False,
                        "compatibilidade_cnae": "DESCONHECIDA",
                        "motivos_incompatibilidade": [],
                        "sugestao_nivel_risco": "MEDIO",
                        "analise_detalhada": "",
                        "erro": f"Resposta vazia. Candidate: {candidate}"
                    }
            else:
                return {
                    "zona_aparente": "INDEFINIDO",
                    "tipo_via": "NAO_VISIVEL",
                    "presenca_placas_comerciais": False,
                    "presenca_vitrines_ou_lojas": False,
                    "presenca_casas_residenciais": False,
                    "compatibilidade_cnae": "DESCONHECIDA",
                    "motivos_incompatibilidade": [],
                    "sugestao_nivel_risco": "MEDIO",
                    "analise_detalhada": "",
                    "erro": f"Estrutura de resposta inesperada. Candidate: {candidate}"
                }
        else:
            return {
                "zona_aparente": "INDEFINIDO",
                "tipo_via": "NAO_VISIVEL",
                "presenca_placas_comerciais": False,
                "presenca_vitrines_ou_lojas": False,
                "presenca_casas_residenciais": False,
                "compatibilidade_cnae": "DESCONHECIDA",
                "motivos_incompatibilidade": [],
                "sugestao_nivel_risco": "MEDIO",
                "analise_detalhada": "",
                "erro": f"Resposta inesperada da API: {result}"
            }
        
        # Parsear resposta JSON
        json_match = re.search(r'\{[\s\S]*\}', resposta_texto)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = resposta_texto
        
        resultado = json.loads(json_str)
        
        # Normalizar valores
        return {
            "zona_aparente": resultado.get("zona_aparente", "INDEFINIDO"),
            "tipo_via": resultado.get("tipo_via", "NAO_VISIVEL"),
            "presenca_placas_comerciais": bool(resultado.get("presenca_placas_comerciais", False)),
            "presenca_vitrines_ou_lojas": bool(resultado.get("presenca_vitrines_ou_lojas", False)),
            "presenca_casas_residenciais": bool(resultado.get("presenca_casas_residenciais", False)),
            "compatibilidade_cnae": resultado.get("compatibilidade_cnae", "DESCONHECIDA"),
            "motivos_incompatibilidade": resultado.get("motivos_incompatibilidade", []),
            "sugestao_nivel_risco": resultado.get("sugestao_nivel_risco", "MEDIO"),
            "analise_detalhada": resultado.get("analise_detalhada", ""),
            "erro": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "zona_aparente": "INDEFINIDO",
            "tipo_via": "NAO_VISIVEL",
            "presenca_placas_comerciais": False,
            "presenca_vitrines_ou_lojas": False,
            "presenca_casas_residenciais": False,
            "compatibilidade_cnae": "DESCONHECIDA",
            "motivos_incompatibilidade": [],
            "sugestao_nivel_risco": "MEDIO",
            "analise_detalhada": "",
            "erro": f"Erro ao processar resposta do Gemini: {str(e)}. Resposta recebida: {resposta_texto[:200] if 'resposta_texto' in locals() else 'N/A'}"
        }
    except Exception as e:
        return {
            "zona_aparente": "INDEFINIDO",
            "tipo_via": "NAO_VISIVEL",
            "presenca_placas_comerciais": False,
            "presenca_vitrines_ou_lojas": False,
            "presenca_casas_residenciais": False,
            "compatibilidade_cnae": "DESCONHECIDA",
            "motivos_incompatibilidade": [],
            "sugestao_nivel_risco": "MEDIO",
            "analise_detalhada": "",
            "erro": f"Erro ao consultar Gemini: {str(e)}"
        }


def analisar_endereco_completo(
    cnpj: str,
    image_bytes: Optional[bytes] = None,
    cnaes: Optional[List[Dict[str, Any]]] = None,
    razao_social: Optional[str] = None,
    nome_fantasia: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analisa endereço completo: busca imagem se não fornecida, analisa com Gemini e aplica regras.
    
    Args:
        cnpj: CNPJ da empresa
        image_bytes: Bytes da imagem (opcional, busca do banco se não fornecido)
        cnaes: Lista de CNAEs (opcional, busca do CNPJA se não fornecido)
        razao_social: Razão social (opcional)
        nome_fantasia: Nome fantasia (opcional)
    
    Returns:
        Dicionário com análise completa incluindo flags de risco
    """
    from database import get_endereco_geocoding, get_consulta_cnpj
    from cnae_compatibility_rules import aplicar_regras_risco, obter_tipo_local_esperado_cnae
    
    # Buscar dados se não fornecidos
    if not image_bytes:
        dados_endereco = get_endereco_geocoding(cnpj)
        if dados_endereco and dados_endereco.get("street_view_image_bytes"):
            image_bytes = dados_endereco["street_view_image_bytes"]
        elif dados_endereco and dados_endereco.get("place_photos"):
            # Usar primeira foto do Places se Street View não disponível
            place_photos = dados_endereco.get("place_photos", [])
            if place_photos and len(place_photos) > 0:
                image_bytes = place_photos[0].get("image_bytes")
    
    if not image_bytes:
        return {
            "erro": "Nenhuma imagem disponível para análise. Processe o endereço primeiro.",
            "analise_visual": None,
            "risco_final": "INDEFINIDO",
            "flags_risco": []
        }
    
    # Buscar CNAEs se não fornecidos
    if not cnaes:
        dados_cnpj = get_consulta_cnpj(cnpj)
        if dados_cnpj:
            cnaes = []
            # CNAE principal (estrutura da API CNPJA: mainActivity)
            if dados_cnpj.get("mainActivity"):
                cnae_principal = dados_cnpj["mainActivity"]
                cnae_id = str(cnae_principal.get("id", ""))
                # O ID da CNPJA contém o código CNAE (formato numérico)
                cnae_codigo = cnae_id if len(cnae_id) <= 7 else cnae_id[:7]
                cnaes.append({
                    "codigo": cnae_codigo,
                    "descricao": cnae_principal.get("text", "")
                })
            # CNAEs secundários (estrutura da API CNPJA: sideActivities)
            if dados_cnpj.get("sideActivities"):
                for sec in dados_cnpj["sideActivities"]:
                    cnae_id = str(sec.get("id", ""))
                    cnae_codigo = cnae_id if len(cnae_id) <= 7 else cnae_id[:7]
                    cnaes.append({
                        "codigo": cnae_codigo,
                        "descricao": sec.get("text", "")
                    })
            
            if not razao_social:
                # A API CNPJA armazena em company.name
                razao_social = dados_cnpj.get("company", {}).get("name") or dados_cnpj.get("name")
            if not nome_fantasia:
                # A API CNPJA armazena em alias
                nome_fantasia = dados_cnpj.get("alias")
    
    if not cnaes:
        return {
            "erro": "Nenhum CNAE encontrado para análise.",
            "analise_visual": None,
            "risco_final": "INDEFINIDO",
            "flags_risco": []
        }
    
    # Analisar imagem com Gemini
    analise_visual = analisar_imagem_endereco(
        image_bytes=image_bytes,
        cnaes=cnaes,
        razao_social=razao_social,
        nome_fantasia=nome_fantasia
    )
    
    if analise_visual.get("erro"):
        return {
            "erro": analise_visual["erro"],
            "analise_visual": analise_visual,
            "risco_final": "INDEFINIDO",
            "flags_risco": []
        }
    
    # Aplicar regras de compatibilidade
    tipo_local_esperado = obter_tipo_local_esperado_cnae(cnaes[0].get("codigo", ""))
    
    resultado_risco = aplicar_regras_risco(
        analise_visual=analise_visual,
        tipo_local_esperado=tipo_local_esperado
    )
    
    # Adicionar peso de typosquatting ao score (PESO ALTO)
    score_risco = resultado_risco.get("score_risco", 0)
    flags_risco = resultado_risco.get("flags_risco", [])
    
    # Verificar typosquatting e adicionar ao score
    try:
        from database import get_email_cnpja, get_dominio_email
        from typosquatting_detector import detect_typosquatting
        
        cnpj_clean = "".join(filter(str.isdigit, cnpj))
        email_cnpja = get_email_cnpja(cnpj_clean)
        # Buscar email cadastrado da empresa
        cnpj_formatted = f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}" if len(cnpj_clean) == 14 else cnpj
        import sqlite3
        conn = sqlite3.connect("savic.db")
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM empresas WHERE cnpj = ? OR cnpj = ?", (cnpj_formatted, cnpj_clean))
        empresa_row = cursor.fetchone()
        conn.close()
        
        if empresa_row and empresa_row[0]:
            email_cadastrado = empresa_row[0]
            dominio_cadastro = get_dominio_email(email_cadastrado)
            dominio_cnpja = get_dominio_email(email_cnpja) if email_cnpja else None
            
            if dominio_cadastro and dominio_cnpja and dominio_cadastro != dominio_cnpja:
                typosquatting_result = detect_typosquatting(dominio_cadastro, dominio_cnpja)
                if typosquatting_result.get("suspeito"):
                    flags_risco.append("TYPOSQUATTING_DETECTADO")
                    # Peso alto para typosquatting: adiciona 50 pontos ao score
                    score_risco += 50
    except Exception as e:
        # Se houver erro, não bloquear a análise
        print(f"Erro ao verificar typosquatting para score: {e}")
        pass
    
    # Limitar score entre 0 e 100
    score_risco = min(100, max(0, score_risco))
    
    # Recalcular risco final baseado no score atualizado
    if score_risco >= 60:
        risco_final = "ALTO"
    elif score_risco >= 30:
        risco_final = "MEDIO"
    else:
        risco_final = "BAIXO"
    
    # Montar resultado completo
    resultado_completo = {
        "erro": None,
        "analise_visual": analise_visual,
        "tipo_local_esperado": tipo_local_esperado,
        "risco_final": risco_final,
        "flags_risco": flags_risco,
        "score_risco": score_risco
    }
    
    # Salvar no banco de dados
    from database import save_analise_risco_endereco
    save_analise_risco_endereco(cnpj, resultado_completo)
    
    return resultado_completo

