import streamlit as st
from database import init_database
from auth import check_authentication
from pages.login import show_login_page
from pages.homepage import show_homepage

# Configuração da página
st.set_page_config(
    page_title="SAVIC",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar banco de dados
init_database()

# Verificar autenticação e exibir página apropriada
if not check_authentication():
    show_login_page()
else:
    show_homepage()
