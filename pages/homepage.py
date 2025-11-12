import streamlit as st
import re
from database import save_empresa, get_empresas_by_user
from auth import logout_user


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
    
    # Formulário de CNPJ
    st.subheader("Cadastrar Nova Empresa")
    
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
        submit_button = st.form_submit_button("Cadastrar Empresa", use_container_width=True)
        
        if submit_button:
            if not cnpj:
                st.error("Por favor, informe o CNPJ")
            elif not validate_cnpj(cnpj):
                st.error("CNPJ inválido. O CNPJ deve conter 14 dígitos.")
            else:
                cnpj_formatted = format_cnpj(cnpj)
                user_id = st.session_state.user_id
                
                success = save_empresa(cnpj_formatted, razao_social if razao_social else None, user_id)
                
                if success:
                    st.success(f"Empresa cadastrada com sucesso! CNPJ: {cnpj_formatted}")
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
