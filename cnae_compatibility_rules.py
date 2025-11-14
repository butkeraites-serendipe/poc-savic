"""
Módulo para regras de compatibilidade entre CNAEs e tipos de local.
Define mapeamento de CNAEs para tipos de local esperados e regras de risco.
"""

from typing import Dict, List, Any, Optional
from database import get_tipo_local_esperado_cnae


# Mapeamento de códigos CNAE para tipos de local esperados
# Baseado em padrões comuns de atividades econômicas
CNAE_TIPO_LOCAL_MAP = {
    # Comércio varejista - espera loja/comércio
    "4711": "COMERCIAL",  # Comércio varejista de mercadorias em geral
    "4719": "COMERCIAL",  # Comércio varejista de mercadorias em geral, com predominância de produtos alimentícios
    "4721": "COMERCIAL",  # Comércio varejista de produtos alimentícios em geral
    "4731": "COMERCIAL",  # Comércio varejista de combustíveis para veículos automotores
    "4741": "COMERCIAL",  # Comércio varejista de equipamentos de informática e comunicação
    "4751": "COMERCIAL",  # Comércio varejista de equipamentos e artigos de uso doméstico
    "4761": "COMERCIAL",  # Comércio varejista de produtos culturais, recreativos e esportivos
    "4771": "COMERCIAL",  # Comércio varejista de produtos farmacêuticos
    "4781": "COMERCIAL",  # Comércio varejista de artigos do vestuário e acessórios
    
    # Serviços e escritórios - pode ser escritório ou home office
    "6201": "ESCRITORIO",  # Desenvolvimento de programas de computador
    "6202": "ESCRITORIO",  # Desenvolvimento e licenciamento de programas de computador customizáveis
    "6203": "ESCRITORIO",  # Desenvolvimento e licenciamento de programas de computador não-customizáveis
    "6204": "ESCRITORIO",  # Consultoria em tecnologia da informação
    "6209": "ESCRITORIO",  # Suporte técnico, manutenção e outros serviços de tecnologia da informação
    "6311": "ESCRITORIO",  # Processamento de dados, hospedagem na internet e serviços relacionados
    "6319": "ESCRITORIO",  # Outras atividades de serviços de informação
    "7020": "ESCRITORIO",  # Atividades de consultoria em gestão empresarial
    "7111": "ESCRITORIO",  # Serviços de arquitetura
    "7112": "ESCRITORIO",  # Serviços de engenharia
    "7210": "ESCRITORIO",  # Pesquisa e desenvolvimento experimental em ciências físicas e naturais
    "7319": "ESCRITORIO",  # Outras atividades de publicidade
    "7410": "ESCRITORIO",  # Atividades de design
    "7420": "ESCRITORIO",  # Atividades de fotografia
    "7490": "ESCRITORIO",  # Outras atividades profissionais, científicas e técnicas não especificadas
    
    # Indústria - espera zona industrial/galpão
    "1011": "INDUSTRIAL",  # Abate de suínos, aves e outros pequenos animais
    "1012": "INDUSTRIAL",  # Fabricação de produtos de carne
    "1020": "INDUSTRIAL",  # Preservação do pescado e fabricação de produtos do pescado
    "1031": "INDUSTRIAL",  # Fabricação de conservas de frutas
    "1041": "INDUSTRIAL",  # Fabricação de óleos vegetais em bruto
    "1051": "INDUSTRIAL",  # Fabricação de laticínios
    "1061": "INDUSTRIAL",  # Moagem de trigo e fabricação de derivados
    "1071": "INDUSTRIAL",  # Fabricação de açúcar
    "1081": "INDUSTRIAL",  # Beneficiamento de café
    "1091": "INDUSTRIAL",  # Fabricação de produtos de panificação
    "2511": "INDUSTRIAL",  # Fabricação de estruturas metálicas
    "2521": "INDUSTRIAL",  # Fabricação de tanques, reservatórios metálicos e caldeiras
    "2539": "INDUSTRIAL",  # Fabricação de outros produtos de metal não especificados
    "2591": "INDUSTRIAL",  # Tratamento e revestimento de metais
    "2599": "INDUSTRIAL",  # Fabricação de outros produtos de metal não especificados
    "2610": "INDUSTRIAL",  # Fabricação de componentes eletrônicos
    "2621": "INDUSTRIAL",  # Fabricação de equipamentos de informática
    "2631": "INDUSTRIAL",  # Fabricação de equipamentos de comunicação
    "2640": "INDUSTRIAL",  # Fabricação de aparelhos de recepção, reprodução, gravação e amplificação de áudio e vídeo
    "2711": "INDUSTRIAL",  # Fabricação de geradores, transformadores e motores elétricos
    "2721": "INDUSTRIAL",  # Fabricação de pilhas, baterias e acumuladores elétricos
    "2731": "INDUSTRIAL",  # Fabricação de aparelhos e equipamentos para distribuição e controle de energia elétrica
    "2740": "INDUSTRIAL",  # Fabricação de material elétrico para instalações
    "2751": "INDUSTRIAL",  # Fabricação de eletrodomésticos
    "2790": "INDUSTRIAL",  # Fabricação de outros equipamentos elétricos não especificados
    "2811": "INDUSTRIAL",  # Fabricação de motores e turbinas, exceto para aviões e veículos rodoviários
    "2821": "INDUSTRIAL",  # Fabricação de equipamentos de transmissão para fins industriais
    "2829": "INDUSTRIAL",  # Fabricação de outras máquinas e equipamentos de uso geral
    "2910": "INDUSTRIAL",  # Fabricação de automóveis, camionetas e utilitários
    "2920": "INDUSTRIAL",  # Fabricação de carrocerias para veículos automotores
    "2930": "INDUSTRIAL",  # Fabricação de peças e acessórios para o sistema motor de veículos automotores
    "3011": "INDUSTRIAL",  # Construção de embarcações
    "3012": "INDUSTRIAL",  # Construção de embarcações para esporte e lazer
    "3021": "INDUSTRIAL",  # Fabricação de locomotivas, vagões e outros materiais rodoviários
    "3031": "INDUSTRIAL",  # Fabricação de aeronaves
    "3032": "INDUSTRIAL",  # Fabricação de motores, turbinas e outros componentes e peças para aeronaves
    "3091": "INDUSTRIAL",  # Fabricação de motocicletas
    "3092": "INDUSTRIAL",  # Fabricação de bicicletas e triciclos não-motorizados
    "3099": "INDUSTRIAL",  # Fabricação de outros equipamentos de transporte não especificados
    
    # Logística e armazenagem
    "5211": "INDUSTRIAL",  # Armazenamento e guarda-móveis
    "5221": "INDUSTRIAL",  # Atividades de apoio ao transporte terrestre
    "5222": "INDUSTRIAL",  # Atividades de apoio ao transporte marítimo
    "5223": "INDUSTRIAL",  # Atividades de apoio ao transporte aéreo
    "5224": "INDUSTRIAL",  # Atividades de apoio ao transporte por navegação interior
    "5229": "INDUSTRIAL",  # Outras atividades de apoio ao transporte
    
    # Construção
    "4110": "INDUSTRIAL",  # Incorporação de empreendimentos imobiliários
    "4211": "INDUSTRIAL",  # Construção de edifícios
    "4212": "INDUSTRIAL",  # Construção de rodovias e ferrovias
    "4213": "INDUSTRIAL",  # Construção de obras de arte especiais
    "4221": "INDUSTRIAL",  # Obras de infraestrutura para geração e distribuição de energia elétrica
    "4222": "INDUSTRIAL",  # Obras de infraestrutura para telecomunicações
    "4223": "INDUSTRIAL",  # Obras de infraestrutura para água, esgoto e outras obras de infraestrutura urbana
    "4291": "INDUSTRIAL",  # Obras de acabamento
    "4299": "INDUSTRIAL",  # Outras obras de engenharia civil não especificadas
    
    # Serviços que podem ser home office (e-commerce, consultoria, etc.)
    "4791": "ECOMMERCE_DOMICILIAR_OK",  # Comércio varejista de mercadorias em geral, por internet
    "4799": "ECOMMERCE_DOMICILIAR_OK",  # Outras atividades de comércio varejista não especificadas
    "6201": "ECOMMERCE_DOMICILIAR_OK",  # Desenvolvimento de programas de computador (pode ser home office)
    "6204": "ECOMMERCE_DOMICILIAR_OK",  # Consultoria em tecnologia da informação (pode ser home office)
    "7020": "ECOMMERCE_DOMICILIAR_OK",  # Atividades de consultoria em gestão empresarial (pode ser home office)
    "7319": "ECOMMERCE_DOMICILIAR_OK",  # Outras atividades de publicidade (pode ser home office)
    "7410": "ECOMMERCE_DOMICILIAR_OK",  # Atividades de design (pode ser home office)
    "7420": "ECOMMERCE_DOMICILIAR_OK",  # Atividades de fotografia (pode ser home office)
}


def obter_tipo_local_esperado_cnae(cnae_codigo: str) -> str:
    """
    Obtém o tipo de local esperado para um CNAE.
    Primeiro verifica no banco de dados, depois no mapeamento estático.
    
    Args:
        cnae_codigo: Código do CNAE (ex: "6201-5/01" ou "6201")
    
    Returns:
        Tipo de local esperado: COMERCIAL, ESCRITORIO, INDUSTRIAL, ECOMMERCE_DOMICILIAR_OK, ou INDEFINIDO
    """
    # Limpar código CNAE (remover formatação)
    cnae_clean = cnae_codigo.replace("-", "").replace("/", "").replace(".", "").strip()
    
    # Tentar buscar no banco primeiro
    tipo_banco = get_tipo_local_esperado_cnae(cnae_clean)
    if tipo_banco:
        return tipo_banco
    
    # Buscar no mapeamento estático (usar primeiros 4 dígitos)
    if len(cnae_clean) >= 4:
        prefixo = cnae_clean[:4]
        return CNAE_TIPO_LOCAL_MAP.get(prefixo, "INDEFINIDO")
    
    return "INDEFINIDO"


def aplicar_regras_risco(
    analise_visual: Dict[str, Any],
    tipo_local_esperado: str
) -> Dict[str, Any]:
    """
    Aplica regras de risco baseadas na análise visual e tipo de local esperado.
    
    Args:
        analise_visual: Resultado da análise do Gemini
        tipo_local_esperado: Tipo de local esperado para o CNAE
    
    Returns:
        Dicionário com:
        {
            "risco_final": "ALTO | MEDIO | BAIXO",
            "flags_risco": List[str],
            "score_risco": int (0-100, onde 100 é maior risco)
        }
    """
    flags_risco = []
    score_risco = 0
    
    zona_aparente = analise_visual.get("zona_aparente", "INDEFINIDO")
    tipo_via = analise_visual.get("tipo_via", "NAO_VISIVEL")
    presenca_placas = analise_visual.get("presenca_placas_comerciais", False)
    presenca_vitrines = analise_visual.get("presenca_vitrines_ou_lojas", False)
    presenca_casas = analise_visual.get("presenca_casas_residenciais", False)
    compatibilidade = analise_visual.get("compatibilidade_cnae", "DESCONHECIDA")
    
    # Regras de ALTO RISCO
    
    # 1. CNAE comercial/industrial em zona residencial (PESO REDUZIDO - análise visual)
    if tipo_local_esperado in ["COMERCIAL", "INDUSTRIAL"] and zona_aparente == "RESIDENCIAL":
        flags_risco.append("INCOMPATIBILIDADE_ZONA_COMERCIAL_RESIDENCIAL")
        score_risco += 30  # Reduzido pela metade (era 60)
    
    # 2. Rua de terra em área residencial com CNAE comercial (PESO REDUZIDO - análise visual)
    if tipo_local_esperado == "COMERCIAL" and zona_aparente == "RESIDENCIAL" and tipo_via == "TERRA":
        flags_risco.append("RUA_TERRA_COM_CNae_COMERCIAL")
        score_risco += 25  # Reduzido pela metade (era 50)
    
    # 3. Ausência de placas comerciais em CNAE comercial (PESO REDUZIDO - análise visual)
    if tipo_local_esperado == "COMERCIAL" and not presenca_placas and not presenca_vitrines:
        flags_risco.append("AUSENCIA_SINAIS_COMERCIAIS")
        score_risco += 22  # Reduzido pela metade (era 45)
    
    # 4. Predominância de casas residenciais sem comércio (PESO REDUZIDO - análise visual)
    if tipo_local_esperado == "COMERCIAL" and presenca_casas and not presenca_vitrines:
        flags_risco.append("AREA_RESIDENCIAL_SEM_COMERCIO")
        score_risco += 20  # Reduzido pela metade (era 40)
    
    # 5. Compatibilidade baixa reportada pelo Gemini (PESO REDUZIDO - análise visual)
    if compatibilidade == "BAIXA":
        flags_risco.append("COMPATIBILIDADE_BAIXA_IA")
        score_risco += 35  # Reduzido pela metade (era 70)
    
    # 6. CNAE industrial em zona residencial ou comercial (sem galpões) (PESO REDUZIDO - análise visual)
    if tipo_local_esperado == "INDUSTRIAL" and zona_aparente in ["RESIDENCIAL", "COMERCIAL"]:
        flags_risco.append("INDUSTRIA_EM_ZONA_NAO_INDUSTRIAL")
        score_risco += 32  # Reduzido pela metade (era 65)
    
    # Regras de MÉDIO RISCO
    
    # 7. CNAE de escritório em zona residencial (pode ser home office, mas suspeito)
    if tipo_local_esperado == "ESCRITORIO" and zona_aparente == "RESIDENCIAL":
        if tipo_via == "TERRA" or not presenca_placas:
            flags_risco.append("ESCRITORIO_EM_RESIDENCIAL_SUSPEITO")
            score_risco += 15
        else:
            flags_risco.append("ESCRITORIO_EM_RESIDENCIAL_POSSIVEL_HOME_OFFICE")
            score_risco += 5
    
    # 8. Compatibilidade média (PESO REDUZIDO - análise visual)
    if compatibilidade == "MEDIA":
        flags_risco.append("COMPATIBILIDADE_MEDIA_IA")
        score_risco += 17  # Reduzido pela metade (era 35)
    
    # 9. Zona indefinida
    if zona_aparente == "INDEFINIDO":
        flags_risco.append("ZONA_INDEFINIDA")
        score_risco += 10
    
    # Regras de BAIXO RISCO (compatibilidade)
    
    # 10. CNAE compatível com e-commerce/home office em residencial
    if tipo_local_esperado == "ECOMMERCE_DOMICILIAR_OK" and zona_aparente == "RESIDENCIAL":
        flags_risco.append("COMPATIVEL_HOME_OFFICE")
        # Não adiciona score negativo, apenas marca como compatível
    
    # 11. Compatibilidade alta
    if compatibilidade == "ALTA":
        flags_risco.append("COMPATIBILIDADE_ALTA_IA")
        score_risco = max(0, score_risco - 10)  # Reduz score se compatibilidade alta
    
    # Determinar risco final baseado no score
    if score_risco >= 60:
        risco_final = "ALTO"
    elif score_risco >= 30:
        risco_final = "MEDIO"
    else:
        risco_final = "BAIXO"
    
    # Limitar score entre 0 e 100
    score_risco = min(100, max(0, score_risco))
    
    return {
        "risco_final": risco_final,
        "flags_risco": flags_risco,
        "score_risco": score_risco
    }

