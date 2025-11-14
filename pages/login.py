import streamlit as st
from auth import login_user


def show_login_page():
    """Exibe a página de login."""
    st.title("🔐 Login - SAVIC")
    
    st.subheader("Faça login na sua conta")
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        submit_button = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("Por favor, preencha todos os campos")
            else:
                if login_user(username, password):
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Username ou senha incorretos")
