"""
Script de teste para análise de risco de endereço.
Testa o serviço usando CNPJ do banco SQLite.
"""

from address_risk_service import analisar_endereco_completo
from database import get_endereco_geocoding, get_consulta_cnpj, get_analise_risco_endereco
import json


def testar_analise_risco(cnpj: str):
    """
    Testa a análise de risco para um CNPJ.
    """
    print("="*70)
    print(f"TESTE DE ANÁLISE DE RISCO - CNPJ: {cnpj}")
    print("="*70)
    
    # 1. Verificar dados do CNPJ
    print("\n📋 1. Verificando dados do CNPJ...")
    dados_cnpj = get_consulta_cnpj(cnpj)
    
    if not dados_cnpj:
        print("❌ CNPJ não encontrado no banco. Execute a consulta primeiro.")
        return
    
    print(f"✅ CNPJ encontrado")
    print(f"   - Razão Social: {dados_cnpj.get('name', 'N/A')}")
    print(f"   - Nome Fantasia: {dados_cnpj.get('fantasy', 'N/A')}")
    
    # Preparar CNAEs
    cnaes = []
    if dados_cnpj.get("primary_activity"):
        cnae_principal = dados_cnpj["primary_activity"]
        cnaes.append({
            "codigo": cnae_principal.get("code", ""),
            "descricao": cnae_principal.get("text", "")
        })
        print(f"   - CNAE Principal: {cnae_principal.get('code')} - {cnae_principal.get('text')}")
    
    if dados_cnpj.get("secondary_activities"):
        for sec in dados_cnpj["secondary_activities"]:
            cnaes.append({
                "codigo": sec.get("code", ""),
                "descricao": sec.get("text", "")
            })
            print(f"   - CNAE Secundário: {sec.get('code')} - {sec.get('text')}")
    
    if not cnaes:
        print("❌ Nenhum CNAE encontrado")
        return
    
    # 2. Verificar dados de endereço
    print("\n🗺️  2. Verificando dados de endereço...")
    dados_endereco = get_endereco_geocoding(cnpj)
    
    if not dados_endereco:
        print("❌ Endereço não processado. Processe o endereço primeiro.")
        return
    
    print(f"✅ Endereço encontrado")
    print(f"   - Endereço: {dados_endereco.get('endereco_completo', 'N/A')}")
    
    # Verificar imagens
    image_bytes = None
    if dados_endereco.get("street_view_image_bytes"):
        image_bytes = dados_endereco["street_view_image_bytes"]
        print(f"   ✅ Imagem Street View disponível ({len(image_bytes)} bytes)")
    elif dados_endereco.get("place_photos"):
        place_photos = dados_endereco.get("place_photos", [])
        if place_photos and len(place_photos) > 0:
            image_bytes = place_photos[0].get("image_bytes")
            print(f"   ✅ Imagem do Places disponível ({len(image_bytes)} bytes)")
    
    if not image_bytes:
        print("❌ Nenhuma imagem disponível para análise")
        return
    
    # 3. Verificar se já existe análise
    print("\n🔍 3. Verificando análises existentes...")
    analise_existente = get_analise_risco_endereco(cnpj)
    if analise_existente:
        print(f"✅ Análise existente encontrada (de {analise_existente.get('analisado_em', 'N/A')})")
        print(f"   - Risco: {analise_existente.get('risco_final', 'N/A')}")
        print(f"   - Score: {analise_existente.get('score_risco', 0)}/100")
        resposta = input("\n   Deseja executar nova análise? (s/N): ").strip().lower()
        if resposta != 's':
            print("\n📊 Exibindo análise existente:")
            exibir_resultados(analise_existente)
            return
    
    # 4. Executar análise
    print("\n🤖 4. Executando análise com Gemini Vision...")
    print("   (Isso pode levar alguns segundos...)")
    
    try:
        resultado = analisar_endereco_completo(
            cnpj=cnpj,
            image_bytes=image_bytes,
            cnaes=cnaes,
            razao_social=dados_cnpj.get("name"),
            nome_fantasia=dados_cnpj.get("fantasy")
        )
        
        if resultado.get("erro"):
            print(f"\n❌ Erro na análise: {resultado['erro']}")
            return
        
        # 5. Exibir resultados
        print("\n✅ Análise concluída com sucesso!")
        print("\n" + "="*70)
        print("RESULTADOS DA ANÁLISE")
        print("="*70)
        
        exibir_resultados(resultado)
        
    except Exception as e:
        print(f"\n❌ Erro ao executar análise: {str(e)}")
        import traceback
        traceback.print_exc()


def exibir_resultados(resultado: dict):
    """Exibe os resultados da análise de forma formatada."""
    
    analise_visual = resultado.get("analise_visual", {})
    
    # Indicador de risco
    risco_final = resultado.get("risco_final", "INDEFINIDO")
    score_risco = resultado.get("score_risco", 0)
    
    print(f"\n🚨 RISCO FINAL: {risco_final} (Score: {score_risco}/100)")
    
    if risco_final == "ALTO":
        print("   ⚠️  ATENÇÃO: Risco alto detectado!")
    elif risco_final == "MEDIO":
        print("   ⚠️  Risco médio - requer atenção")
    elif risco_final == "BAIXO":
        print("   ✅ Risco baixo - aparenta ser seguro")
    
    # Análise visual
    print("\n📊 ANÁLISE VISUAL:")
    print(f"   - Zona Aparente: {analise_visual.get('zona_aparente', 'N/A')}")
    print(f"   - Tipo de Via: {analise_visual.get('tipo_via', 'N/A')}")
    print(f"   - Placas Comerciais: {'Sim' if analise_visual.get('presenca_placas_comerciais') else 'Não'}")
    print(f"   - Vitrines/Lojas: {'Sim' if analise_visual.get('presenca_vitrines_ou_lojas') else 'Não'}")
    print(f"   - Casas Residenciais: {'Sim' if analise_visual.get('presenca_casas_residenciais') else 'Não'}")
    
    # Compatibilidade
    print(f"\n🎯 COMPATIBILIDADE:")
    print(f"   - Tipo Local Esperado (CNAE): {resultado.get('tipo_local_esperado', 'N/A')}")
    print(f"   - Compatibilidade CNAE: {analise_visual.get('compatibilidade_cnae', 'N/A')}")
    
    # Motivos de incompatibilidade
    motivos = analise_visual.get("motivos_incompatibilidade", [])
    if motivos:
        print(f"\n⚠️  MOTIVOS DE INCOMPATIBILIDADE:")
        for motivo in motivos:
            print(f"   - {motivo}")
    
    # Flags de risco
    flags = resultado.get("flags_risco", [])
    if flags:
        print(f"\n🏷️  FLAGS DE RISCO ({len(flags)}):")
        for flag in flags:
            print(f"   - {flag}")
    
    # Análise detalhada
    analise_detalhada = analise_visual.get("analise_detalhada", "")
    if analise_detalhada:
        print(f"\n📝 ANÁLISE DETALHADA:")
        print(f"   {analise_detalhada}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    # CNPJ do banco
    cnpj_teste = "07275920000161"
    
    print("\n🧪 TESTE DO SERVIÇO DE ANÁLISE DE RISCO")
    print(f"CNPJ: {cnpj_teste}\n")
    
    testar_analise_risco(cnpj_teste)

