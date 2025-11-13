#!/usr/bin/env python3
"""Script para testar a avaliação de CNAEs com Gemini API."""

import sqlite3
import json
from gemini_api import avaliar_compatibilidade_cnaes
from database import save_avaliacao_cnae, get_avaliacao_cnae

# Conectar ao banco e buscar dados
conn = sqlite3.connect("savic.db")
cursor = conn.cursor()

# Buscar CNPJ e dados da última consulta
cursor.execute("SELECT cnpj, dados_json FROM consultas_cnpj ORDER BY atualizado_em DESC LIMIT 1")
result = cursor.fetchone()
conn.close()

if not result:
    print("Nenhuma consulta encontrada no banco de dados.")
    exit(1)

cnpj = result[0]
dados_json = result[1]
dados = json.loads(dados_json)

print("=" * 70)
print("TESTE DE AVALIACAO DE CNAEs COM GEMINI AI")
print("=" * 70)
print()
print(f"CNPJ: {cnpj}")
print(f"Empresa: {dados.get('company', {}).get('name', 'N/A')}")
print()

# Extrair CNAEs (usar camelCase como na API CNPJA)
main_activity = dados.get("mainActivity", {})
side_activities = dados.get("sideActivities", [])

if not main_activity:
    print("Nenhum CNAE principal encontrado nos dados.")
    exit(1)

print("CNAEs encontrados:")
print(f"   Principal: {main_activity.get('id', '')} - {main_activity.get('text', '')}")
print(f"   Secundarios: {len(side_activities)}")
if side_activities:
    for i, sec in enumerate(side_activities[:5], 1):
        print(f"      {i}. {sec.get('id', '')} - {sec.get('text', '')}")
    if len(side_activities) > 5:
        print(f"      ... e mais {len(side_activities) - 5}")
print()

# Verificar se já existe avaliação
avaliacao_existente = get_avaliacao_cnae(cnpj)
if avaliacao_existente:
    print("Ja existe avaliacao para este CNPJ:")
    print(f"   Score: {avaliacao_existente.get('score', 'N/A')}")
    print(f"   Compativel: {avaliacao_existente.get('compativel', 'N/A')}")
    print(f"   Avaliado em: {avaliacao_existente.get('avaliado_em', 'N/A')}")
    print()
    resposta = input("Deseja avaliar novamente? (s/N): ")
    if resposta.lower() != 's':
        print("Operacao cancelada.")
        exit(0)

print("Iniciando avaliacao com Gemini AI...")
print("(Isso pode levar alguns segundos...)")
print()

try:
    avaliacao = avaliar_compatibilidade_cnaes(
        main_activity,
        side_activities,  # Todos os CNAEs secundários
        dados.get('company', {}).get('name'),
        dados.get('company', {}).get('alias')
    )
    
    if avaliacao.get("erro"):
        print("=" * 70)
        print("ERRO NA AVALIACAO")
        print("=" * 70)
        print(f"{avaliacao['erro']}")
        exit(1)
    
    print("=" * 70)
    print("AVALIACAO CONCLUIDA COM SUCESSO!")
    print("=" * 70)
    print()
    
    # Exibir resultados
    compativel = avaliacao.get("compativel")
    score = avaliacao.get("score")
    
    print("RESULTADO DA AVALIACAO:")
    print("-" * 70)
    if compativel is not None:
        if compativel:
            print(f"   ✅ COMPATIVEL (Score: {score:.0f}/100)")
        else:
            print(f"   ❌ INCOMPATIVEL (Score: {score:.0f}/100)")
    elif score is not None:
        if score >= 70:
            print(f"   ✅ Score: {score:.0f}/100")
        elif score >= 50:
            print(f"   ⚠️  Score: {score:.0f}/100")
        else:
            print(f"   ❌ Score: {score:.0f}/100")
    print()
    
    if avaliacao.get("analise"):
        print("ANALISE DETALHADA:")
        print("-" * 70)
        print(avaliacao['analise'])
        print("-" * 70)
        print()
    
    if avaliacao.get("observacoes"):
        print("OBSERVACOES:")
        for obs in avaliacao["observacoes"]:
            print(f"   • {obs}")
        print()
    
    # Salvar no banco
    print("Salvando avaliacao no banco de dados...")
    sucesso = save_avaliacao_cnae(cnpj, avaliacao)
    
    if sucesso:
        print("✅ Avaliacao salva com sucesso!")
        
        # Verificar se foi salva corretamente
        avaliacao_salva = get_avaliacao_cnae(cnpj)
        if avaliacao_salva:
            print()
            print("✅ Verificacao: Avaliacao recuperada do banco com sucesso!")
            print(f"   Score: {avaliacao_salva.get('score', 'N/A')}")
            print(f"   Compativel: {avaliacao_salva.get('compativel', 'N/A')}")
            print(f"   Avaliado em: {avaliacao_salva.get('avaliado_em', 'N/A')}")
    else:
        print("❌ Erro ao salvar avaliacao.")
    
    print()
    print("=" * 70)
    print("TESTE CONCLUIDO!")
    print("=" * 70)
        
except Exception as e:
    print("=" * 70)
    print("ERRO DURANTE A AVALIACAO")
    print("=" * 70)
    print(f"{str(e)}")
    import traceback
    traceback.print_exc()

