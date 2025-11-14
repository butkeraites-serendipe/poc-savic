"""
Script de teste para geração de relatórios Excel.
"""

import sys

# Verificar se openpyxl está instalado
try:
    import openpyxl
    print("✅ openpyxl instalado")
except ImportError:
    print("❌ openpyxl não está instalado")
    print("   Instale com: pip install openpyxl")
    print("   Ou: pip install -r requirements.txt")
    sys.exit(1)

# Testar geração de relatório
try:
    from relatorio_excel import gerar_relatorio_para_cnpj
    
    print("\n🧪 Testando geração de relatório Excel...")
    cnpj_teste = "07275920000161"
    
    relatorio = gerar_relatorio_para_cnpj(cnpj_teste, caminho_saida="teste_relatorio.xlsx")
    
    print(f"✅ Relatório gerado com sucesso!")
    print(f"   Arquivo: teste_relatorio.xlsx")
    print(f"   CNPJ: {cnpj_teste}")
    
except Exception as e:
    print(f"❌ Erro ao gerar relatório: {e}")
    import traceback
    traceback.print_exc()

