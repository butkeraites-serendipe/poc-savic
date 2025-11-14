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
    page_title="Login",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Esconder completamente o sidebar e menu de navegação
st.markdown("""
    <style>
        /* Esconder o sidebar completamente */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"],
        aside[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        
        /* Esconder o botão de toggle do sidebar */
        button[data-testid="baseButton-header"],
        button[kind="header"],
        .stApp > header button {
            display: none !important;
        }
        
        /* Esconder o menu de navegação lateral (drawer) */
        div[data-testid="stSidebarNav"],
        nav[data-testid="stSidebarNav"],
        ul[data-testid="stSidebarNav"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Esconder o container do sidebar */
        .css-1d391kg,
        .css-1lcbmhc,
        .css-1y4p8pa {
            display: none !important;
        }
        
        /* Garantir que o conteúdo principal ocupe toda a largura */
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        
        /* Ajustar o layout principal para não ter espaço do sidebar */
        .main {
            margin-left: 0 !important;
        }
        
        /* Esconder qualquer link ou elemento de navegação do sidebar */
        a[href*="app"],
        a[href*="homepage"],
        a[href*="login"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Inicializar banco de dados
init_database()

# Verificar autenticação e exibir página apropriada
if not check_authentication():
    show_login_page()
else:
    show_homepage()
