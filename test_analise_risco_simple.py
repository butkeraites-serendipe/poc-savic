"""
Script de teste simplificado para análise de risco de endereço.
Carrega .env manualmente sem depender do módulo dotenv.
"""

import os
import sys
from pathlib import Path

# Carregar .env manualmente
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Agora importar os módulos
from database import get_endereco_geocoding, get_consulta_cnpj, get_analise_risco_endereco
import requests
import json
import re
import base64


def get_api_key():
    """Obtém a chave da API."""
    return os.getenv("VERTEX_AI_API_KEY") or os.getenv("GEMINI_API_KEY")


def analisar_imagem_endereco(image_bytes, cnaes, razao_social=None, nome_fantasia=None):
    """Analisa imagem com Gemini Vision."""
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
            "erro": "Chave da API Gemini não configurada"
        }
    
    # Preparar CNAEs
    cnaes_texto = "\n".join([
        f"- {cnae.get('codigo', '')} - {cnae.get('descricao', '')}"
        for cnae in cnaes
    ])
    
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
- Detectar sinais de local possivelmente suspeito para sede da empresa.

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
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    mime_type = "image/jpeg"
    
    # Fazer chamada à API
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
    
    try:
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", str(response.text))
            except:
                error_detail = response.text[:200]
            
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
                "erro": f"Erro na API Gemini ({response.status_code}): {error_detail}"
            }
        
        result = response.json()
        
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
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
                        "erro": "Resposta vazia do Gemini"
                    }
                
                # Parsear JSON
                json_match = re.search(r'\{[\s\S]*\}', resposta_texto)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = resposta_texto
                
                resultado = json.loads(json_str)
                
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
            "erro": f"Resposta inesperada: {result}"
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


def testar_analise_risco(cnpj: str):
    """Testa a análise de risco."""
    print("="*70)
    print(f"TESTE DE ANÁLISE DE RISCO - CNPJ: {cnpj}")
    print("="*70)
    
    # Verificar dados do CNPJ
    print("\n📋 1. Verificando dados do CNPJ...")
    dados_cnpj = get_consulta_cnpj(cnpj)
    
    if not dados_cnpj:
        print("❌ CNPJ não encontrado no banco.")
        return
    
    print(f"✅ CNPJ encontrado")
    print(f"   - Razão Social: {dados_cnpj.get('name', 'N/A')}")
    
    # Preparar CNAEs (estrutura da API CNPJA)
    cnaes = []
    if dados_cnpj.get("mainActivity"):
        cnae_principal = dados_cnpj["mainActivity"]
        # Converter ID para código CNAE (formato: XXXX-X/XX)
        cnae_id = str(cnae_principal.get("id", ""))
        # O ID da CNPJA é o código CNAE completo, mas pode precisar formatação
        cnae_codigo = cnae_id if len(cnae_id) <= 7 else cnae_id[:7]  # Ajustar conforme necessário
        cnaes.append({
            "codigo": cnae_codigo,
            "descricao": cnae_principal.get("text", "")
        })
        print(f"   - CNAE Principal: {cnae_codigo} - {cnae_principal.get('text')}")
    
    if dados_cnpj.get("sideActivities"):
        for sec in dados_cnpj["sideActivities"]:
            cnae_id = str(sec.get("id", ""))
            cnae_codigo = cnae_id if len(cnae_id) <= 7 else cnae_id[:7]
            cnaes.append({
                "codigo": cnae_codigo,
                "descricao": sec.get("text", "")
            })
        print(f"   - CNAEs Secundários: {len(dados_cnpj['sideActivities'])} atividades")
    
    if not cnaes:
        print("❌ Nenhum CNAE encontrado")
        return
    
    # Verificar dados de endereço
    print("\n🗺️  2. Verificando dados de endereço...")
    dados_endereco = get_endereco_geocoding(cnpj)
    
    if not dados_endereco:
        print("❌ Endereço não processado.")
        return
    
    print(f"✅ Endereço encontrado: {dados_endereco.get('endereco_completo', 'N/A')}")
    
    # Verificar imagens
    image_bytes = None
    if dados_endereco.get("street_view_image_bytes"):
        image_bytes = dados_endereco["street_view_image_bytes"]
        print(f"   ✅ Imagem Street View disponível ({len(image_bytes)} bytes)")
    elif dados_endereco.get("place_photos"):
        place_photos = dados_endereco.get("place_photos", [])
        if place_photos and len(place_photos) > 0:
            image_bytes = place_photos[0].get("image_bytes")
            print(f"   ✅ Imagem do Places disponível")
    
    if not image_bytes:
        print("❌ Nenhuma imagem disponível")
        return
    
    # Verificar API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ Chave da API Gemini não configurada no .env")
        return
    
    print(f"\n🔑 API Key configurada: {api_key[:10]}...")
    
    # Executar análise
    print("\n🤖 3. Executando análise com Gemini Vision...")
    print("   (Isso pode levar alguns segundos...)")
    
    try:
        analise_visual = analisar_imagem_endereco(
            image_bytes=image_bytes,
            cnaes=cnaes,
            razao_social=dados_cnpj.get("name"),
            nome_fantasia=dados_cnpj.get("fantasy")
        )
        
        if analise_visual.get("erro"):
            print(f"\n❌ Erro: {analise_visual['erro']}")
            return
        
        # Exibir resultados
        print("\n✅ Análise concluída!")
        print("\n" + "="*70)
        print("RESULTADOS DA ANÁLISE")
        print("="*70)
        
        print(f"\n📊 ANÁLISE VISUAL:")
        print(f"   - Zona Aparente: {analise_visual.get('zona_aparente', 'N/A')}")
        print(f"   - Tipo de Via: {analise_visual.get('tipo_via', 'N/A')}")
        print(f"   - Placas Comerciais: {'Sim' if analise_visual.get('presenca_placas_comerciais') else 'Não'}")
        print(f"   - Vitrines/Lojas: {'Sim' if analise_visual.get('presenca_vitrines_ou_lojas') else 'Não'}")
        print(f"   - Casas Residenciais: {'Sim' if analise_visual.get('presenca_casas_residenciais') else 'Não'}")
        print(f"   - Compatibilidade CNAE: {analise_visual.get('compatibilidade_cnae', 'N/A')}")
        print(f"   - Sugestão de Risco: {analise_visual.get('sugestao_nivel_risco', 'N/A')}")
        
        motivos = analise_visual.get("motivos_incompatibilidade", [])
        if motivos:
            print(f"\n⚠️  MOTIVOS DE INCOMPATIBILIDADE:")
            for motivo in motivos:
                print(f"   - {motivo}")
        
        analise_detalhada = analise_visual.get("analise_detalhada", "")
        if analise_detalhada:
            print(f"\n📝 ANÁLISE DETALHADA:")
            print(f"   {analise_detalhada}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    cnpj_teste = "07275920000161"
    print("\n🧪 TESTE DO SERVIÇO DE ANÁLISE DE RISCO")
    print(f"CNPJ: {cnpj_teste}\n")
    testar_analise_risco(cnpj_teste)

