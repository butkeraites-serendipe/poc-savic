import streamlit as st
import re
from database import save_empresa, get_empresas_by_user
from auth import logout_user
from cnpja_api import consultar_cnpj


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
    """Exibe a homepage com formulário de CNPJ."""
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
    
    # Seção de consulta de dados cadastrais
    st.subheader("🔍 Consultar Dados Cadastrais")
    
    with st.form("consulta_form", clear_on_submit=False):
        cnpj_consulta = st.text_input(
            "CNPJ para Consulta",
            placeholder="00.000.000/0000-00 ou 00000000000000",
            help="Digite o CNPJ da empresa para consultar dados cadastrais na Receita Federal",
            key="cnpj_consulta"
        )
        consultar_button = st.form_submit_button("Consultar CNPJ", use_container_width=True)
        
        if consultar_button:
            if not cnpj_consulta:
                st.error("Por favor, informe o CNPJ para consulta")
            elif not validate_cnpj(cnpj_consulta):
                st.error("CNPJ inválido. O CNPJ deve conter 14 dígitos.")
            else:
                # Verifica se deve forçar atualização
                forcar_atualizacao = st.session_state.get("forcar_atualizacao", False)
                
                with st.spinner("Consultando dados cadastrais..."):
                    try:
                        dados = consultar_cnpj(cnpj_consulta, usar_cache=True, forcar_atualizacao=forcar_atualizacao)
                        
                        if dados:
                            # Armazenar dados no session_state para exibição fora do form
                            st.session_state.consulta_dados = dados
                            st.session_state.consulta_cnpj = cnpj_consulta
                            st.session_state.forcar_atualizacao = False
                            st.rerun()
                    
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro inesperado ao consultar CNPJ: {str(e)}")
    
    # Exibir resultados da consulta (fora do formulário)
    if "consulta_dados" in st.session_state and st.session_state.consulta_dados:
        dados = st.session_state.consulta_dados
        cnpj_consulta = st.session_state.get("consulta_cnpj", "")
        
        # Verifica se veio do cache
        is_cached = dados.get("_cached", False)
        cached_at = dados.get("_cached_at", "")
        
        if is_cached:
            st.success(f"✅ Dados encontrados no cache (consultado em: {cached_at})")
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("🔄 Atualizar da API", use_container_width=True, key="btn_atualizar"):
                    # Força atualização e mantém o CNPJ para nova consulta
                    st.session_state.forcar_atualizacao = True
                    # Remove dados do cache para forçar nova consulta
                    if "consulta_dados" in st.session_state:
                        del st.session_state.consulta_dados
                    # Faz nova consulta automaticamente
                    try:
                        dados = consultar_cnpj(cnpj_consulta, usar_cache=True, forcar_atualizacao=True)
                        if dados:
                            st.session_state.consulta_dados = dados
                            st.session_state.consulta_cnpj = cnpj_consulta
                            st.session_state.forcar_atualizacao = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {str(e)}")
        else:
            st.success("✅ Dados encontrados!")
        
        # Extrair dados da estrutura da API CNPJA
        company = dados.get("company", {})
        tax_id = dados.get("taxId", "")
        company_name = company.get("name", "")
        alias = dados.get("alias")
        status = dados.get("status", {})
        founded = dados.get("founded", "")
        address = dados.get("address", {})
        emails = dados.get("emails", [])
        phones = dados.get("phones", [])
        main_activity = dados.get("mainActivity", {})
        side_activities = dados.get("sideActivities", [])
        
        # Exibir dados principais
        with st.expander("📋 Dados Cadastrais Completos", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if company_name:
                    st.write(f"**Razão Social:** {company_name}")
                if alias:
                    st.write(f"**Nome Fantasia:** {alias}")
                if tax_id:
                    cnpj_formatted = format_cnpj(tax_id)
                    st.write(f"**CNPJ:** {cnpj_formatted}")
                if status:
                    status_text = status.get("text", "N/A") if isinstance(status, dict) else str(status)
                    st.write(f"**Status:** {status_text}")
                if founded:
                    st.write(f"**Data de Abertura:** {founded}")
            
            with col2:
                if emails:
                    email_str = ", ".join([e.get("address", "") for e in emails if isinstance(e, dict)])
                    if email_str:
                        st.write(f"**Email:** {email_str}")
                if phones:
                    phone_str = ", ".join([
                        f"({p.get('area', '')}) {p.get('number', '')}" 
                        for p in phones if isinstance(p, dict)
                    ])
                    if phone_str:
                        st.write(f"**Telefone:** {phone_str}")
            
            # Endereço
            if address and isinstance(address, dict):
                st.divider()
                st.write("**Endereço:**")
                endereco_parts = []
                if address.get("street"):
                    endereco_parts.append(address["street"])
                if address.get("number"):
                    endereco_parts.append(f"nº {address['number']}")
                if address.get("details"):
                    endereco_parts.append(address["details"])
                if address.get("district"):
                    endereco_parts.append(address["district"])
                if address.get("city"):
                    endereco_parts.append(address["city"])
                if address.get("state"):
                    endereco_parts.append(address["state"])
                if address.get("zip"):
                    endereco_parts.append(f"CEP: {address['zip']}")
                
                if endereco_parts:
                    st.write(", ".join(endereco_parts))
            
            # Todas as atividades CNAE (Principal + Secundárias)
            st.divider()
            st.write("**📊 Atividades CNAE:**")
            
            # Criar tabela com todas as atividades
            atividades_data = []
            
            # Adiciona atividade principal
            if main_activity and isinstance(main_activity, dict):
                atividades_data.append({
                    "Tipo": "Principal",
                    "Código CNAE": str(main_activity.get("id", "")),
                    "Descrição": main_activity.get("text", "")
                })
            
            # Adiciona atividades secundárias
            if side_activities and isinstance(side_activities, list):
                for atividade in side_activities:
                    if isinstance(atividade, dict):
                        atividades_data.append({
                            "Tipo": "Secundária",
                            "Código CNAE": str(atividade.get("id", "")),
                            "Descrição": atividade.get("text", "")
                        })
            
            # Exibe tabela com todas as atividades
            if atividades_data:
                total = len(atividades_data)
                principal_count = sum(1 for a in atividades_data if a["Tipo"] == "Principal")
                secundarias_count = total - principal_count
                
                if secundarias_count > 0:
                    st.write(f"**Total:** {total} atividades ({principal_count} principal, {secundarias_count} secundárias)")
                else:
                    st.write(f"**Total:** {total} atividade principal")
                
                st.dataframe(atividades_data, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma atividade CNAE encontrada.")
            
            # Botão para preencher formulário com dados consultados (fora do form)
            if st.button("💾 Usar estes dados no cadastro", use_container_width=True, key="btn_preencher"):
                cnpj_formatted = format_cnpj(tax_id) if tax_id else format_cnpj(cnpj_consulta)
                email_value = emails[0].get("address", "") if emails and isinstance(emails[0], dict) else ""
                
                st.session_state.prefill_cnpj = cnpj_formatted
                st.session_state.prefill_razao_social = company_name
                st.session_state.prefill_email = email_value
                
                # Limpar dados da consulta
                if "consulta_dados" in st.session_state:
                    del st.session_state.consulta_dados
                if "consulta_cnpj" in st.session_state:
                    del st.session_state.consulta_cnpj
                
                st.rerun()
        
        # Exibir JSON completo em expander (para debug)
        with st.expander("🔧 Dados JSON Completos (Debug)"):
            st.json(dados)
    
    st.divider()
    
    # Formulário de CNPJ
    st.subheader("Cadastrar Nova Empresa")
    
    with st.form("cnpj_form", clear_on_submit=True):
        # Preencher campos se houver dados da consulta
        cnpj_prefill = st.session_state.get("prefill_cnpj", "")
        razao_social_prefill = st.session_state.get("prefill_razao_social", "")
        email_prefill = st.session_state.get("prefill_email", "")
        
        cnpj = st.text_input(
            "CNPJ",
            value=cnpj_prefill,
            placeholder="00.000.000/0000-00 ou 00000000000000",
            help="Digite o CNPJ da empresa (com ou sem formatação)"
        )
        razao_social = st.text_input(
            "Razão Social (opcional)",
            value=razao_social_prefill,
            placeholder="Nome da empresa",
            help="Nome completo da empresa"
        )
        email = st.text_input(
            "Email (opcional)",
            value=email_prefill,
            placeholder="contato@empresa.com.br",
            help="Email de contato da empresa"
        )
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
                    user_id
                )
                
                if success:
                    st.success(f"Empresa cadastrada com sucesso! CNPJ: {cnpj_formatted}")
                    # Limpar dados de preenchimento após cadastro bem-sucedido
                    if "prefill_cnpj" in st.session_state:
                        del st.session_state.prefill_cnpj
                    if "prefill_razao_social" in st.session_state:
                        del st.session_state.prefill_razao_social
                    if "prefill_email" in st.session_state:
                        del st.session_state.prefill_email
                else:
                    st.error("Este CNPJ já foi cadastrado anteriormente.")
    
    st.divider()
    
    # Lista de empresas cadastradas
    st.subheader("Empresas Cadastradas")
    
    empresas = get_empresas_by_user(st.session_state.user_id)
    
    if empresas:
        for empresa in empresas:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**CNPJ:** {empresa['cnpj']}")
                    if empresa['email']:
                        st.write(f"**Email:** {empresa['email']}")
                with col2:
                    if empresa['razao_social']:
                        st.write(f"**Razão Social:** {empresa['razao_social']}")
                    else:
                        st.write("*Razão social não informada*")
                with col3:
                    st.caption(f"Cadastrado em: {empresa['created_at']}")
                st.divider()
    else:
        st.info("Nenhuma empresa cadastrada ainda. Use o formulário acima para cadastrar.")
