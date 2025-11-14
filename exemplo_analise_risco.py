"""
Exemplo de uso do serviço de análise de risco de endereço com Gemini Vision.

Este script demonstra como usar o address_risk_service para analisar
imagens de endereços e avaliar compatibilidade com CNAEs.
"""

from address_risk_service import analisar_endereco_completo
from database import get_endereco_geocoding, get_consulta_cnpj


def exemplo_analise_cnpj(cnpj: str):
    """
    Exemplo de análise completa de risco para um CNPJ.
    
    Args:
        cnpj: CNPJ da empresa (com ou sem formatação)
    """
    print(f"\n{'='*60}")
    print(f"Análise de Risco de Endereço - CNPJ: {cnpj}")
    print(f"{'='*60}\n")
    
    # Buscar dados do CNPJ
    dados_cnpj = get_consulta_cnpj(cnpj)
    if not dados_cnpj:
        print("❌ CNPJ não encontrado. Consulte primeiro usando a API CNPJA.")
        return
    
    # Buscar dados de endereço
    dados_endereco = get_endereco_geocoding(cnpj)
    if not dados_endereco:
        print("❌ Endereço não processado. Processe o endereço primeiro.")
        return
    
    # Verificar se há imagem disponível
    image_bytes = None
    if dados_endereco.get("street_view_image_bytes"):
        image_bytes = dados_endereco["street_view_image_bytes"]
        print("✅ Imagem Street View encontrada")
    elif dados_endereco.get("place_photos"):
        place_photos = dados_endereco.get("place_photos", [])
        if place_photos and len(place_photos) > 0:
            image_bytes = place_photos[0].get("image_bytes")
            print("✅ Imagem do Places encontrada")
    
    if not image_bytes:
        print("❌ Nenhuma imagem disponível para análise.")
        return
    
    # Preparar CNAEs
    cnaes = []
    if dados_cnpj.get("primary_activity"):
        cnae_principal = dados_cnpj["primary_activity"]
        cnaes.append({
            "codigo": cnae_principal.get("code", ""),
            "descricao": cnae_principal.get("text", "")
        })
        print(f"📋 CNAE Principal: {cnae_principal.get('code')} - {cnae_principal.get('text')}")
    
    if dados_cnpj.get("secondary_activities"):
        for sec in dados_cnpj["secondary_activities"]:
            cnaes.append({
                "codigo": sec.get("code", ""),
                "descricao": sec.get("text", "")
            })
            print(f"📋 CNAE Secundário: {sec.get('code')} - {sec.get('text')}")
    
    if not cnaes:
        print("❌ Nenhum CNAE encontrado.")
        return
    
    # Executar análise
    print("\n🔍 Executando análise com Gemini Vision...")
    resultado = analisar_endereco_completo(
        cnpj=cnpj,
        image_bytes=image_bytes,
        cnaes=cnaes,
        razao_social=dados_cnpj.get("name"),
        nome_fantasia=dados_cnpj.get("fantasy")
    )
    
    if resultado.get("erro"):
        print(f"❌ Erro na análise: {resultado['erro']}")
        return
    
    # Exibir resultados
    print("\n" + "="*60)
    print("RESULTADOS DA ANÁLISE")
    print("="*60)
    
    analise_visual = resultado.get("analise_visual", {})
    
    print(f"\n📍 Zona Aparente: {analise_visual.get('zona_aparente', 'N/A')}")
    print(f"🛣️  Tipo de Via: {analise_visual.get('tipo_via', 'N/A')}")
    print(f"🏪 Placas Comerciais: {'Sim' if analise_visual.get('presenca_placas_comerciais') else 'Não'}")
    print(f"🪟 Vitrines/Lojas: {'Sim' if analise_visual.get('presenca_vitrines_ou_lojas') else 'Não'}")
    print(f"🏠 Casas Residenciais: {'Sim' if analise_visual.get('presenca_casas_residenciais') else 'Não'}")
    
    print(f"\n🎯 Tipo Local Esperado (CNAE): {resultado.get('tipo_local_esperado', 'N/A')}")
    print(f"✅ Compatibilidade CNAE: {analise_visual.get('compatibilidade_cnae', 'N/A')}")
    
    motivos = analise_visual.get("motivos_incompatibilidade", [])
    if motivos:
        print(f"\n⚠️  Motivos de Incompatibilidade:")
        for motivo in motivos:
            print(f"   - {motivo}")
    
    print(f"\n🚨 Risco Final: {resultado.get('risco_final', 'N/A')}")
    print(f"📊 Score de Risco: {resultado.get('score_risco', 0)}/100")
    
    flags = resultado.get("flags_risco", [])
    if flags:
        print(f"\n🏷️  Flags de Risco:")
        for flag in flags:
            print(f"   - {flag}")
    
    analise_detalhada = analise_visual.get("analise_detalhada", "")
    if analise_detalhada:
        print(f"\n📝 Análise Detalhada:")
        print(f"   {analise_detalhada}")
    
    print("\n" + "="*60)
    print("✅ Análise concluída e salva no banco de dados!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Exemplo de uso
    # Substitua pelo CNPJ que você deseja analisar
    cnpj_exemplo = "12345678000190"  # Substitua por um CNPJ válido
    
    print("⚠️  ATENÇÃO: Este é um exemplo de uso.")
    print("Certifique-se de que:")
    print("1. O CNPJ já foi consultado na API CNPJA")
    print("2. O endereço já foi processado (geocoding + imagens)")
    print("3. A chave GEMINI_API_KEY está configurada no .env\n")
    
    # Descomente a linha abaixo para executar
    # exemplo_analise_cnpj(cnpj_exemplo)

