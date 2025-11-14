import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from database import init_database
from auth import check_authentication
from pages.login import show_login_page
from pages.homepage import show_homepage

# Carregar variáveis de ambiente
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="SAVIC",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Inicializar banco de dados
init_database()

# Verificar autenticação e exibir página apropriada
if not check_authentication():
    show_login_page()
else:
    show_homepage()
