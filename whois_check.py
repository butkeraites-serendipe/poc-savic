"""
Módulo para verificação de idade de domínios de email usando WHOIS.
"""

import re
import whois
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any

EMAIL_REGEX = re.compile(r"[^@]+@([^@]+\.[^@]+)")


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extrai o domínio de um email.
    
    Args:
        email: Email completo
    
    Returns:
        Domínio extraído ou None se inválido
    """
    if not email:
        return None
    
    match = EMAIL_REGEX.match(email.strip())
    if not match:
        return None
    
    domain = match.group(1).lower()
    return domain


def get_domain_creation_date(domain: str) -> Optional[datetime]:
    """
    Obtém a data de criação de um domínio usando WHOIS.
    
    Args:
        domain: Domínio a ser consultado
    
    Returns:
        Data de criação do domínio ou None se não conseguir obter
    """
    try:
        w = whois.whois(domain)
    except Exception as e:
        # Tratar erros de WHOIS (timeout, domínio inexistente, etc.)
        print(f"Erro consultando WHOIS para {domain}: {e}")
        return None
    
    created = w.creation_date
    
    # Algumas libs retornam lista se o domínio teve múltiplos registros
    if isinstance(created, list):
        if created:
            created = min(created)  # pegar a mais antiga
        else:
            return None
    
    if created is None:
        return None
    
    return created


def check_domain_age(email: str, min_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Verifica a idade do domínio de um email.
    
    Args:
        email: Email completo
        min_days: Limite mínimo de dias (se None, busca do banco de dados)
    
    Returns:
        Dicionário com informações sobre a idade do domínio
    """
    if not email:
        return {
            "email": email,
            "domain": None,
            "creation_date": None,
            "age_days": None,
            "is_recent": None,
            "warning": "Email não fornecido",
            "error": True
        }
    
    domain = extract_domain_from_email(email)
    if not domain:
        return {
            "email": email,
            "domain": None,
            "creation_date": None,
            "age_days": None,
            "is_recent": None,
            "warning": "Email inválido",
            "error": True
        }
    
    # Obter limite de dias do banco se não fornecido
    if min_days is None:
        try:
            from database import get_config_whois_min_days
            min_days = get_config_whois_min_days()
        except:
            min_days = 180  # Padrão se não conseguir importar
    
    created_at = get_domain_creation_date(domain)
    
    if not created_at:
        return {
            "email": email,
            "domain": domain,
            "creation_date": None,
            "age_days": None,
            "is_recent": None,
            "threshold_days": min_days,
            "warning": "Não foi possível obter data de criação do domínio",
            "error": True
        }
    
    # Garantir timezone-aware e comparação com agora
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    age_days = (now - created_at).days
    
    is_recent = age_days < min_days if age_days is not None else None
    
    return {
        "email": email,
        "domain": domain,
        "creation_date": created_at.isoformat(),
        "age_days": age_days,
        "threshold_days": min_days,
        "is_recent": is_recent,
        "warning": None,
        "error": False
    }

