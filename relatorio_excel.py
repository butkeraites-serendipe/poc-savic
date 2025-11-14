"""
Módulo para geração de relatórios Excel de análise de risco de endereço.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ para XX.XXX.XXX/XXXX-XX."""
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    if len(cnpj_clean) == 14:
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    return cnpj_clean


def gerar_relatorio_excel(
    cnpj: str,
    dados_empresa: Dict[str, Any],
    dados_endereco: Optional[Dict[str, Any]],
    analise_risco: Dict[str, Any],
    cnaes: list,
    caminho_saida: Optional[str] = None
) -> bytes:
    """
    Gera relatório Excel completo de análise de risco.
    
    Args:
        cnpj: CNPJ da empresa
        dados_empresa: Dados da empresa (razão social, nome fantasia, etc.)
        dados_endereco: Dados de geocoding e endereço
        analise_risco: Resultado completo da análise de risco
        cnaes: Lista de CNAEs da empresa
        caminho_saida: Caminho para salvar o arquivo (opcional, retorna bytes se None)
    
    Returns:
        Bytes do arquivo Excel ou None se caminho_saida fornecido
    """
    # Criar workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Análise de Risco"
    
    # Estilos
    estilo_titulo = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    estilo_cabecalho = Font(name="Arial", size=11, bold=True)
    estilo_normal = Font(name="Arial", size=10)
    estilo_risco_alto = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    estilo_risco_medio = Font(name="Arial", size=11, bold=True, color="000000")
    estilo_risco_baixo = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    
    fill_titulo = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    fill_cabecalho = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    fill_risco_alto = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    fill_risco_medio = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    fill_risco_baixo = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
    fill_cinza = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    
    alinhamento_centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
    alinhamento_esquerda = Alignment(horizontal="left", vertical="top", wrap_text=True)
    
    linha_atual = 1
    
    # TÍTULO
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_titulo = ws[f"A{linha_atual}"]
    celula_titulo.value = "RELATÓRIO DE ANÁLISE DE RISCO DE ENDEREÇO"
    celula_titulo.font = estilo_titulo
    celula_titulo.fill = fill_titulo
    celula_titulo.alignment = alinhamento_centro
    linha_atual += 1
    
    # Data de geração
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_data = ws[f"A{linha_atual}"]
    celula_data.value = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    celula_data.font = Font(name="Arial", size=9, italic=True)
    celula_data.alignment = alinhamento_centro
    linha_atual += 2
    
    # SEÇÃO 1: DADOS DA EMPRESA
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_sec1 = ws[f"A{linha_atual}"]
    celula_sec1.value = "1. DADOS DA EMPRESA"
    celula_sec1.font = estilo_cabecalho
    celula_sec1.fill = fill_cabecalho
    celula_sec1.alignment = alinhamento_esquerda
    linha_atual += 1
    
    # Dados da empresa
    dados_empresa_lista = [
        ("CNPJ", formatar_cnpj(cnpj)),
        ("Razão Social", dados_empresa.get("razao_social", "N/A")),
        ("Nome Fantasia", dados_empresa.get("nome_fantasia", "N/A")),
        ("Data de Abertura", dados_empresa.get("data_abertura", "N/A")),
    ]
    
    for rotulo, valor in dados_empresa_lista:
        ws[f"A{linha_atual}"] = rotulo
        ws[f"A{linha_atual}"].font = estilo_cabecalho
        ws[f"A{linha_atual}"].fill = fill_cinza
        ws[f"A{linha_atual}"].border = border
        ws[f"A{linha_atual}"].alignment = alinhamento_esquerda
        
        ws.merge_cells(f"B{linha_atual}:D{linha_atual}")
        ws[f"B{linha_atual}"] = valor
        ws[f"B{linha_atual}"].font = estilo_normal
        ws[f"B{linha_atual}"].border = border
        ws[f"B{linha_atual}"].alignment = alinhamento_esquerda
        linha_atual += 1
    
    linha_atual += 1
    
    # SEÇÃO 2: ENDEREÇO
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_sec2 = ws[f"A{linha_atual}"]
    celula_sec2.value = "2. ENDEREÇO"
    celula_sec2.font = estilo_cabecalho
    celula_sec2.fill = fill_cabecalho
    celula_sec2.alignment = alinhamento_esquerda
    linha_atual += 1
    
    if dados_endereco:
        endereco_formatado = dados_endereco.get("formatted_address") or dados_endereco.get("endereco_completo", "N/A")
        lat = dados_endereco.get("lat")
        lng = dados_endereco.get("lng")
        
        dados_endereco_lista = [
            ("Endereço Completo", endereco_formatado),
            ("Coordenadas", f"{lat}, {lng}" if lat and lng else "N/A"),
            ("Place ID", dados_endereco.get("place_id", "N/A")),
        ]
        
        for rotulo, valor in dados_endereco_lista:
            ws[f"A{linha_atual}"] = rotulo
            ws[f"A{linha_atual}"].font = estilo_cabecalho
            ws[f"A{linha_atual}"].fill = fill_cinza
            ws[f"A{linha_atual}"].border = border
            ws[f"A{linha_atual}"].alignment = alinhamento_esquerda
            
            ws.merge_cells(f"B{linha_atual}:D{linha_atual}")
            ws[f"B{linha_atual}"] = valor
            ws[f"B{linha_atual}"].font = estilo_normal
            ws[f"B{linha_atual}"].border = border
            ws[f"B{linha_atual}"].alignment = alinhamento_esquerda
            linha_atual += 1
    else:
        ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
        ws[f"A{linha_atual}"] = "Endereço não processado"
        ws[f"A{linha_atual}"].font = estilo_normal
        ws[f"A{linha_atual}"].border = border
        linha_atual += 1
    
    linha_atual += 1
    
    # SEÇÃO 3: CNAEs
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_sec3 = ws[f"A{linha_atual}"]
    celula_sec3.value = "3. ATIVIDADES CNAE"
    celula_sec3.font = estilo_cabecalho
    celula_sec3.fill = fill_cabecalho
    celula_sec3.alignment = alinhamento_esquerda
    linha_atual += 1
    
    # Cabeçalho da tabela CNAE
    ws[f"A{linha_atual}"] = "Tipo"
    ws[f"B{linha_atual}"] = "Código CNAE"
    ws.merge_cells(f"C{linha_atual}:D{linha_atual}")
    ws[f"C{linha_atual}"] = "Descrição"
    
    for col in ["A", "B", "C", "D"]:
        celula = ws[f"{col}{linha_atual}"]
        celula.font = estilo_cabecalho
        celula.fill = fill_cabecalho
        celula.border = border
        celula.alignment = alinhamento_centro
    
    linha_atual += 1
    
    # CNAE Principal
    if cnaes and len(cnaes) > 0:
        cnae_principal = cnaes[0]
        ws[f"A{linha_atual}"] = "Principal"
        ws[f"B{linha_atual}"] = cnae_principal.get("codigo", "N/A")
        ws.merge_cells(f"C{linha_atual}:D{linha_atual}")
        ws[f"C{linha_atual}"] = cnae_principal.get("descricao", "N/A")
        
        for col in ["A", "B", "C", "D"]:
            celula = ws[f"{col}{linha_atual}"]
            celula.font = estilo_normal
            celula.border = border
            celula.alignment = alinhamento_esquerda if col != "A" else alinhamento_centro
        
        linha_atual += 1
        
        # CNAEs Secundários
        if len(cnaes) > 1:
            for cnae_sec in cnaes[1:]:
                ws[f"A{linha_atual}"] = "Secundária"
                ws[f"B{linha_atual}"] = cnae_sec.get("codigo", "N/A")
                ws.merge_cells(f"C{linha_atual}:D{linha_atual}")
                ws[f"C{linha_atual}"] = cnae_sec.get("descricao", "N/A")
                
                for col in ["A", "B", "C", "D"]:
                    celula = ws[f"{col}{linha_atual}"]
                    celula.font = estilo_normal
                    celula.border = border
                    celula.alignment = alinhamento_esquerda if col != "A" else alinhamento_centro
                
                linha_atual += 1
    
    linha_atual += 1
    
    # SEÇÃO 4: RESULTADO DA ANÁLISE DE RISCO
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_sec4 = ws[f"A{linha_atual}"]
    celula_sec4.value = "4. RESULTADO DA ANÁLISE DE RISCO"
    celula_sec4.font = estilo_cabecalho
    celula_sec4.fill = fill_cabecalho
    celula_sec4.alignment = alinhamento_esquerda
    linha_atual += 1
    
    # Risco Final (destaque)
    risco_final = analise_risco.get("risco_final", "INDEFINIDO")
    score_risco = analise_risco.get("score_risco", 0)
    
    ws.merge_cells(f"A{linha_atual}:B{linha_atual}")
    ws[f"A{linha_atual}"] = "RISCO FINAL:"
    ws[f"A{linha_atual}"].font = estilo_cabecalho
    ws[f"A{linha_atual}"].fill = fill_cinza
    ws[f"A{linha_atual}"].border = border
    ws[f"A{linha_atual}"].alignment = alinhamento_esquerda
    
    ws.merge_cells(f"C{linha_atual}:D{linha_atual}")
    celula_risco = ws[f"C{linha_atual}"]
    celula_risco.value = f"{risco_final} (Score: {score_risco}/100)"
    
    if risco_final == "ALTO":
        celula_risco.font = estilo_risco_alto
        celula_risco.fill = fill_risco_alto
    elif risco_final == "MEDIO":
        celula_risco.font = estilo_risco_medio
        celula_risco.fill = fill_risco_medio
    elif risco_final == "BAIXO":
        celula_risco.font = estilo_risco_baixo
        celula_risco.fill = fill_risco_baixo
    else:
        celula_risco.font = estilo_normal
    
    celula_risco.border = border
    celula_risco.alignment = alinhamento_centro
    linha_atual += 1
    
    # Tipo Local Esperado
    tipo_local_esperado = analise_risco.get("tipo_local_esperado", "N/A")
    ws[f"A{linha_atual}"] = "Tipo Local Esperado (CNAE):"
    ws[f"A{linha_atual}"].font = estilo_cabecalho
    ws[f"A{linha_atual}"].fill = fill_cinza
    ws[f"A{linha_atual}"].border = border
    
    ws.merge_cells(f"B{linha_atual}:D{linha_atual}")
    ws[f"B{linha_atual}"] = tipo_local_esperado
    ws[f"B{linha_atual}"].font = estilo_normal
    ws[f"B{linha_atual}"].border = border
    linha_atual += 1
    
    linha_atual += 1
    
    # SEÇÃO 5: ANÁLISE VISUAL
    ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
    celula_sec5 = ws[f"A{linha_atual}"]
    celula_sec5.value = "5. ANÁLISE VISUAL (GEMINI VISION)"
    celula_sec5.font = estilo_cabecalho
    celula_sec5.fill = fill_cabecalho
    celula_sec5.alignment = alinhamento_esquerda
    linha_atual += 1
    
    analise_visual = analise_risco.get("analise_visual", {})
    
    dados_analise_visual = [
        ("Zona Aparente", analise_visual.get("zona_aparente", "N/A")),
        ("Tipo de Via", analise_visual.get("tipo_via", "N/A")),
        ("Placas Comerciais", "Sim" if analise_visual.get("presenca_placas_comerciais") else "Não"),
        ("Vitrines/Lojas", "Sim" if analise_visual.get("presenca_vitrines_ou_lojas") else "Não"),
        ("Casas Residenciais", "Sim" if analise_visual.get("presenca_casas_residenciais") else "Não"),
        ("Compatibilidade CNAE", analise_visual.get("compatibilidade_cnae", "N/A")),
        ("Sugestão de Risco", analise_visual.get("sugestao_nivel_risco", "N/A")),
    ]
    
    for rotulo, valor in dados_analise_visual:
        ws[f"A{linha_atual}"] = rotulo
        ws[f"A{linha_atual}"].font = estilo_cabecalho
        ws[f"A{linha_atual}"].fill = fill_cinza
        ws[f"A{linha_atual}"].border = border
        ws[f"A{linha_atual}"].alignment = alinhamento_esquerda
        
        ws.merge_cells(f"B{linha_atual}:D{linha_atual}")
        ws[f"B{linha_atual}"] = valor
        ws[f"B{linha_atual}"].font = estilo_normal
        ws[f"B{linha_atual}"].border = border
        ws[f"B{linha_atual}"].alignment = alinhamento_esquerda
        linha_atual += 1
    
    # Motivos de Incompatibilidade
    motivos = analise_visual.get("motivos_incompatibilidade", [])
    if motivos:
        linha_atual += 1
        ws[f"A{linha_atual}"] = "Motivos de Incompatibilidade:"
        ws[f"A{linha_atual}"].font = estilo_cabecalho
        ws[f"A{linha_atual}"].fill = fill_cinza
        ws[f"A{linha_atual}"].border = border
        linha_atual += 1
        
        for i, motivo in enumerate(motivos, 1):
            ws[f"B{linha_atual}"] = f"{i}. {motivo}"
            ws.merge_cells(f"B{linha_atual}:D{linha_atual}")
            ws[f"B{linha_atual}"].font = estilo_normal
            ws[f"B{linha_atual}"].border = border
            ws[f"B{linha_atual}"].alignment = alinhamento_esquerda
            linha_atual += 1
    
    linha_atual += 1
    
    # SEÇÃO 6: FLAGS DE RISCO
    flags = analise_risco.get("flags_risco", [])
    if flags:
        ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
        celula_sec6 = ws[f"A{linha_atual}"]
        celula_sec6.value = "6. FLAGS DE RISCO"
        celula_sec6.font = estilo_cabecalho
        celula_sec6.fill = fill_cabecalho
        celula_sec6.alignment = alinhamento_esquerda
        linha_atual += 1
        
        for i, flag in enumerate(flags, 1):
            ws[f"A{linha_atual}"] = f"{i}."
            ws[f"A{linha_atual}"].font = estilo_normal
            ws[f"A{linha_atual}"].border = border
            ws[f"A{linha_atual}"].alignment = alinhamento_centro
            
            ws.merge_cells(f"B{linha_atual}:D{linha_atual}")
            ws[f"B{linha_atual}"] = flag
            ws[f"B{linha_atual}"].font = estilo_normal
            ws[f"B{linha_atual}"].border = border
            ws[f"B{linha_atual}"].alignment = alinhamento_esquerda
            linha_atual += 1
        
        linha_atual += 1
    
    # SEÇÃO 7: ANÁLISE DETALHADA
    analise_detalhada = analise_visual.get("analise_detalhada", "")
    if analise_detalhada:
        ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
        celula_sec7 = ws[f"A{linha_atual}"]
        celula_sec7.value = "7. ANÁLISE DETALHADA"
        celula_sec7.font = estilo_cabecalho
        celula_sec7.fill = fill_cabecalho
        celula_sec7.alignment = alinhamento_esquerda
        linha_atual += 1
        
        ws.merge_cells(f"A{linha_atual}:D{linha_atual}")
        celula_detalhada = ws[f"A{linha_atual}"]
        celula_detalhada.value = analise_detalhada
        celula_detalhada.font = estilo_normal
        celula_detalhada.border = border
        celula_detalhada.alignment = alinhamento_esquerda
        celula_detalhada.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        linha_atual += 1
    
    # Ajustar largura das colunas
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 25
    ws.column_dimensions["D"].width = 25
    
    # Salvar ou retornar bytes
    if caminho_saida:
        wb.save(caminho_saida)
        return None
    else:
        from io import BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()


def gerar_relatorio_para_cnpj(cnpj: str, caminho_saida: Optional[str] = None) -> Optional[bytes]:
    """
    Gera relatório Excel completo para um CNPJ, buscando todos os dados necessários.
    
    Args:
        cnpj: CNPJ da empresa
        caminho_saida: Caminho para salvar o arquivo (opcional)
    
    Returns:
        Bytes do arquivo Excel ou None se caminho_saida fornecido
    """
    from database import get_consulta_cnpj, get_endereco_geocoding, get_analise_risco_endereco
    
    # Buscar dados
    dados_cnpj = get_consulta_cnpj(cnpj)
    dados_endereco = get_endereco_geocoding(cnpj)
    analise_risco = get_analise_risco_endereco(cnpj)
    
    if not dados_cnpj:
        raise ValueError("CNPJ não encontrado no banco de dados")
    
    if not analise_risco:
        raise ValueError("Análise de risco não encontrada. Execute a análise primeiro.")
    
    # Preparar dados da empresa
    dados_empresa = {
        "razao_social": dados_cnpj.get("company", {}).get("name") or dados_cnpj.get("name", "N/A"),
        "nome_fantasia": dados_cnpj.get("alias", "N/A"),
        "data_abertura": dados_cnpj.get("founded", "N/A")
    }
    
    # Preparar CNAEs
    cnaes = []
    if dados_cnpj.get("mainActivity"):
        cnae_principal = dados_cnpj["mainActivity"]
        cnae_id = str(cnae_principal.get("id", ""))
        cnae_codigo = cnae_id if len(cnae_id) <= 7 else cnae_id[:7]
        cnaes.append({
            "codigo": cnae_codigo,
            "descricao": cnae_principal.get("text", "")
        })
    
    if dados_cnpj.get("sideActivities"):
        for sec in dados_cnpj["sideActivities"]:
            cnae_id = str(sec.get("id", ""))
            cnae_codigo = cnae_id if len(cnae_id) <= 7 else cnae_id[:7]
            cnaes.append({
                "codigo": cnae_codigo,
                "descricao": sec.get("text", "")
            })
    
    # Gerar relatório
    return gerar_relatorio_excel(
        cnpj=cnpj,
        dados_empresa=dados_empresa,
        dados_endereco=dados_endereco,
        analise_risco=analise_risco,
        cnaes=cnaes,
        caminho_saida=caminho_saida
    )

