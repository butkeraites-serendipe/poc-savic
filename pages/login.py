import streamlit as st
from auth import login_user, register_user


def show_login_page():
    """Exibe a página de login."""
    st.title("🔐 Login - SAVIC")
    
    tab1, tab2 = st.tabs(["Login", "Registrar"])
    
    with tab1:
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
    
    with tab2:
        st.subheader("Crie uma nova conta")
        
        with st.form("register_form"):
            new_username = st.text_input("Username", key="register_username")
            new_password = st.text_input("Senha", type="password", key="register_password")
            confirm_password = st.text_input("Confirmar Senha", type="password", key="confirm_password")
            submit_register = st.form_submit_button("Registrar", use_container_width=True)
            
            if submit_register:
                if not new_username or not new_password or not confirm_password:
                    st.error("Por favor, preencha todos os campos")
                elif new_password != confirm_password:
                    st.error("As senhas não coincidem")
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success(message)
                        st.info("Agora você pode fazer login na aba 'Login'")
                    else:
                        st.error(message)
