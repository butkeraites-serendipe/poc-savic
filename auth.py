import streamlit as st
from typing import Tuple
from database import verify_user, create_user, get_user_id


def check_authentication():
    """Verifica se o usuário está autenticado."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
    
    return st.session_state.authenticated


def login_user(username: str, password: str) -> bool:
    """Autentica um usuário."""
    user_id = verify_user(username, password)
    
    if user_id:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_id = user_id
        return True
    
    return False


def logout_user():
    """Faz logout do usuário."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None


def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Registra um novo usuário."""
    if not username or not password:
        return False, "Username e senha são obrigatórios"
    
    if len(password) < 4:
        return False, "A senha deve ter pelo menos 4 caracteres"
    
    success = create_user(username, password)
    
    if success:
        return True, "Usuário criado com sucesso!"
    else:
        return False, "Username já existe. Escolha outro."
