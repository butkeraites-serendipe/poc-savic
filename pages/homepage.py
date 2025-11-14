import streamlit as st
import re
import base64
import pandas as pd
from datetime import datetime
from io import BytesIO
from database import (
    save_empresa, get_empresas_by_user, save_endereco_geocoding, get_endereco_geocoding,
    save_avaliacao_cnae, get_avaliacao_cnae, save_consulta_cnpj, get_analise_risco_endereco,
    get_dominios_nao_corporativos, adicionar_dominio_nao_corporativo, remover_dominio_nao_corporativo,
    get_config_whois_min_days, set_config_whois_min_days
)
from auth import logout_user
from cnpja_api import consultar_cnpj
from google_maps_api import processar_endereco_completo, formatar_endereco_para_geocode
from gemini_api import avaliar_compatibilidade_cnaes
from address_risk_service import analisar_endereco_completo
from relatorio_excel import gerar_relatorio_para_cnpj


def validate_cnpj(cnpj: str) -> bool:
    """Valida o formato do CNPJ (apenas formato, não dígitos verificadores)."""
    # Remove caracteres não numéricos
    cnpj_clean = re.sub(r'\D', '', cnpj)
    
    # CNPJ deve ter 14 dígitos
    return len(cnpj_clean) == 14


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ para o padrão XX.XXX.XXX/XXXX-XX."""
    cnpj_clean = re.sub(r'\D', '', cnpj)
    
    if len(cnpj_clean) == 14:
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    
    return cnpj


def validate_email(email: str) -> bool:
    """Valida o formato básico do email."""
    if not email:
        return True  # Email é opcional
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def show_homepage():
    """Exibe a homepage focada em cadastro e análise."""
    st.title("🏢 SAVIC - Sistema de Análise de Empresas")
    
    # Barra de logout
    col1, col2 = st.columns([6, 1])
    with col1:
        st.write(f"Bem-vindo, **{st.session_state.username}**!")
    with col2:
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.divider()
    
    # Formulário de Cadastro
    st.subheader("📝 Cadastrar Nova Empresa")
    
    with st.form("cnpj_form", clear_on_submit=True):
        cnpj = st.text_input(
            "CNPJ",
            placeholder="00.000.000/0000-00 ou 00000000000000",
            help="Digite o CNPJ da empresa (com ou sem formatação)"
        )
        razao_social = st.text_input(
            "Razão Social (opcional)",
            placeholder="Nome da empresa",
            help="Nome completo da empresa"
        )
        email = st.text_input(
            "Email (opcional)",
            placeholder="contato@empresa.com.br",
            help="Email de contato da empresa"
        )
        data_abertura = st.text_input(
            "Data de Abertura (opcional)",
            placeholder="YYYY-MM-DD (ex: 2005-03-03)",
            help="Data de abertura da empresa no formato YYYY-MM-DD"
        )
        
        st.divider()
        st.write("**⚠️ Sinalizações de Risco:**")
        
        col1, col2 = st.columns(2)
        with col1:
            telefone_suspeito = st.checkbox("📞 Telefone suspeito")
            pressa_aprovacao = st.checkbox("⏰ Pressa em aprovar")
        with col2:
            entrega_marcada = st.checkbox("📅 Entrega marcada")
            endereco_entrega_diferente = st.checkbox("📍 Endereço entrega diferente")
        
        submit_button = st.form_submit_button("Cadastrar Empresa", use_container_width=True)
        
        if submit_button:
            if not cnpj:
                st.error("Por favor, informe o CNPJ")
            elif not validate_cnpj(cnpj):
                st.error("CNPJ inválido. O CNPJ deve conter 14 dígitos.")
            elif email and not validate_email(email):
                st.error("Email inválido. Por favor, verifique o formato do email.")
            else:
                cnpj_formatted = format_cnpj(cnpj)
                user_id = st.session_state.user_id
                
                success = save_empresa(
                    cnpj_formatted,
                    razao_social if razao_social else None,
                    email if email else None,
                    user_id,
                    data_abertura=data_abertura if data_abertura else None,
                    telefone_suspeito=telefone_suspeito,
                    pressa_aprovacao=pressa_aprovacao,
                    entrega_marcada=entrega_marcada,
                    endereco_entrega_diferente=endereco_entrega_diferente
                )
                
                if success:
                    st.success(f"✅ Empresa cadastrada com sucesso! CNPJ: {cnpj_formatted}")
                    st.rerun()
                else:
                    st.error("Este CNPJ já foi cadastrado anteriormente.")
    
    st.divider()
    
    # Lista de Empresas Cadastradas
    st.subheader("📊 Empresas Cadastradas")
    
    empresas = get_empresas_by_user(st.session_state.user_id)
    
    if empresas:
        
        # Preparar dados para tabela
        dados_tabela = []
        for empresa in empresas:
            # Contar sinalizações
            sinalizacoes_count = sum([
                empresa.get('email_nao_corporativo', False),
                empresa.get('email_dominio_diferente', False),
                empresa.get('email_dominio_recente', False),
                empresa.get('telefone_suspeito', False),
                empresa.get('pressa_aprovacao', False),
                empresa.get('entrega_marcada', False),
                empresa.get('endereco_entrega_diferente', False)
            ])
            
            # Verificar se tem análise
            cnpj_clean = "".join(filter(str.isdigit, empresa['cnpj']))
            analise = get_analise_risco_endereco(cnpj_clean)
            tem_analise = analise is not None
            
            risco_status = "N/A"
            score = 0
            if tem_analise:
                risco_status = analise.get("risco_final", "N/A")
                score = analise.get("score_risco", 0)
            
            dados_tabela.append({
                "CNPJ": empresa['cnpj'],
                "Razão Social": empresa.get('razao_social', 'N/A')[:50] + "..." if empresa.get('razao_social') and len(empresa.get('razao_social', '')) > 50 else empresa.get('razao_social', 'N/A'),
                "Email": empresa.get('email', 'N/A'),
                "Sinalizações": sinalizacoes_count,
                "Análise": "✅ Sim" if tem_analise else "❌ Não",
                "Risco": risco_status,
                "Score": f"{score}/100" if tem_analise else "N/A"
            })
        
        # Exibir tabela
        df = pd.DataFrame(dados_tabela)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Detalhes e ações por empresa
        for empresa in empresas:
            cnpj_clean = "".join(filter(str.isdigit, empresa['cnpj']))
            razao_social_display = empresa.get('razao_social', 'Sem razão social')
            if len(razao_social_display) > 40:
                razao_social_display = razao_social_display[:40] + "..."
            
            with st.expander(f"🔍 {empresa['cnpj']} - {razao_social_display}", expanded=False):
                # Informações básicas
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**CNPJ:** {empresa['cnpj']}")
                    if empresa.get('email'):
                        st.write(f"**Email:** {empresa['email']}")
                    if empresa.get('data_abertura'):
                        st.write(f"**Data de Abertura:** {empresa['data_abertura']}")
                with col2:
                    if empresa.get('razao_social'):
                        st.write(f"**Razão Social:** {empresa['razao_social']}")
                    st.caption(f"Cadastrado em: {empresa['created_at']}")
                
                # Sinalizações
                sinalizacoes = []
                if empresa.get('email_nao_corporativo'):
                    sinalizacoes.append("📧 Email não corporativo")
                if empresa.get('email_dominio_diferente'):
                    sinalizacoes.append("📧 Email com domínio diferente do CNPJA")
                if empresa.get('email_dominio_recente'):
                    sinalizacoes.append("🆕 Domínio do email recente")
                if empresa.get('telefone_suspeito'):
                    sinalizacoes.append("📞 Telefone suspeito")
                if empresa.get('pressa_aprovacao'):
                    sinalizacoes.append("⏰ Pressa em aprovar")
                if empresa.get('entrega_marcada'):
                    sinalizacoes.append("📅 Entrega marcada")
                if empresa.get('endereco_entrega_diferente'):
                    sinalizacoes.append("📍 Endereço entrega diferente")
                
                if sinalizacoes:
                    st.warning(f"⚠️ **{len(sinalizacoes)} sinalização(ões) de risco:**")
                    for sinalizacao in sinalizacoes:
                        st.write(f"- {sinalizacao}")
                
                st.divider()
                
                # Botão de Gerar Análise
                if st.button(f"🤖 Gerar Análise Completa", key=f"btn_analise_{cnpj_clean}", use_container_width=True):
                    # Processar análise completa
                    sucesso = False
                    with st.spinner("Processando análise completa (isso pode levar alguns minutos)..."):
                        # 1. Consultar CNPJ
                        try:
                            dados_cnpj = consultar_cnpj(cnpj_clean, usar_cache=True)
                            if not dados_cnpj:
                                st.error("Erro ao consultar CNPJ")
                            else:
                                save_consulta_cnpj(cnpj_clean, dados_cnpj)
                                
                                # 2. Processar endereço
                                address = dados_cnpj.get("address", {})
                                if not address:
                                    st.error("Endereço não encontrado")
                                else:
                                    try:
                                        dados_geocoding = processar_endereco_completo(address)
                                        endereco_formatado = formatar_endereco_para_geocode(address)
                                        save_endereco_geocoding(cnpj_clean, endereco_formatado, dados_geocoding)
                                        
                                        # 3. Buscar imagem
                                        dados_endereco = get_endereco_geocoding(cnpj_clean)
                                        if not dados_endereco:
                                            st.error("Erro ao recuperar dados de endereço")
                                        else:
                                            image_bytes = None
                                            if dados_endereco.get("street_view_image_bytes"):
                                                image_bytes = dados_endereco["street_view_image_bytes"]
                                            elif dados_endereco.get("place_photos"):
                                                place_photos = dados_endereco.get("place_photos", [])
                                                if place_photos and len(place_photos) > 0:
                                                    image_bytes = place_photos[0].get("image_bytes")
                                            
                                            if not image_bytes:
                                                st.warning("Nenhuma imagem disponível para análise")
                                            else:
                                                # 4. Preparar CNAEs
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
                                                
                                                if not cnaes:
                                                    st.error("Nenhum CNAE encontrado")
                                                else:
                                                    # 5. Analisar risco
                                                    try:
                                                        company = dados_cnpj.get("company", {})
                                                        resultado = analisar_endereco_completo(
                                                            cnpj=cnpj_clean,
                                                            image_bytes=image_bytes,
                                                            cnaes=cnaes,
                                                            razao_social=company.get("name"),
                                                            nome_fantasia=dados_cnpj.get("alias")
                                                        )
                                                        
                                                        if resultado.get("erro"):
                                                            st.error(f"Erro na análise: {resultado['erro']}")
                                                        else:
                                                            sucesso = True
                                                    except Exception as e:
                                                        st.error(f"Erro ao analisar risco: {str(e)}")
                                    except Exception as e:
                                        st.error(f"Erro ao processar endereço: {str(e)}")
                        except Exception as e:
                            st.error(f"Erro ao consultar CNPJ: {str(e)}")
                    
                    if sucesso:
                        st.success("✅ Análise completa gerada com sucesso!")
                        st.rerun()
                
                # Verificar se tem análise
                analise = get_analise_risco_endereco(cnpj_clean)
                if analise:
                    st.divider()
                    
                    # Exibir resultado da análise
                    risco_final = analise.get("risco_final", "INDEFINIDO")
                    score_risco = analise.get("score_risco", 0)
                    
                    if risco_final == "ALTO":
                        st.error(f"🚨 **Risco ALTO** (Score: {score_risco}/100)")
                    elif risco_final == "MEDIO":
                        st.warning(f"⚠️ **Risco MÉDIO** (Score: {score_risco}/100)")
                    elif risco_final == "BAIXO":
                        st.success(f"✅ **Risco BAIXO** (Score: {score_risco}/100)")
                    else:
                        st.info(f"❓ **Risco INDEFINIDO** (Score: {score_risco}/100)")
                    
                    # Botão de Download Excel
                    try:
                        relatorio_bytes = gerar_relatorio_para_cnpj(cnpj_clean)
                        if relatorio_bytes:
                            nome_arquivo = f"relatorio_risco_{cnpj_clean}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            st.download_button(
                                label="📥 Baixar Relatório Excel",
                                data=relatorio_bytes,
                                file_name=nome_arquivo,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"btn_excel_{cnpj_clean}",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Erro ao gerar relatório: {str(e)}")
                    
                    # Detalhes da análise
                    with st.expander("📊 Detalhes da Análise"):
                        analise_visual = analise.get("analise_visual", {})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Zona Aparente:** {analise_visual.get('zona_aparente', 'N/A')}")
                            st.write(f"**Tipo de Via:** {analise_visual.get('tipo_via', 'N/A')}")
                            st.write(f"**Tipo Local Esperado:** {analise.get('tipo_local_esperado', 'N/A')}")
                        with col2:
                            st.write(f"**Placas Comerciais:** {'Sim' if analise_visual.get('presenca_placas_comerciais') else 'Não'}")
                            st.write(f"**Vitrines/Lojas:** {'Sim' if analise_visual.get('presenca_vitrines_ou_lojas') else 'Não'}")
                            st.write(f"**Compatibilidade CNAE:** {analise_visual.get('compatibilidade_cnae', 'N/A')}")
                        
                        flags = analise.get("flags_risco", [])
                        if flags:
                            st.write("**Flags de Risco:**")
                            for flag in flags:
                                st.write(f"- {flag}")
                        
                        if analise.get("analisado_em"):
                            st.caption(f"Análise realizada em: {analise['analisado_em']}")
                else:
                    st.info("ℹ️ Nenhuma análise disponível. Clique em 'Gerar Análise Completa' para iniciar.")
    else:
        st.info("Nenhuma empresa cadastrada ainda. Use o formulário acima para cadastrar.")
