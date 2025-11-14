"""
Módulo para verificação de idade de domínios de email usando WHOIS.
"""

import re
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any

# Tentar importar diferentes bibliotecas WHOIS
try:
    import whois
    WHOIS_AVAILABLE = True
    WHOIS_LIB = 'whois'
except ImportError:
    try:
        from pythonwhois import get_whois
        WHOIS_AVAILABLE = True
        WHOIS_LIB = 'pythonwhois'
    except ImportError:
        WHOIS_AVAILABLE = False
        WHOIS_LIB = None

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
    if not WHOIS_AVAILABLE:
        # Biblioteca WHOIS não disponível - retornar silenciosamente
        return None
    
    try:
        if WHOIS_LIB == 'whois':
            # Verificar qual método está disponível
            w = None
            try:
                # Suprimir stderr temporariamente para evitar mensagens de stdbuf
                import sys
                import os
                import contextlib
                
                # Criar um contexto para suprimir stderr completamente
                @contextlib.contextmanager
                def suppress_stderr():
                    with open(os.devnull, 'w') as devnull:
                        old_stderr = sys.stderr
                        sys.stderr = devnull
                        try:
                            yield
                        finally:
                            sys.stderr = old_stderr
                
                # Tentar chamar whois com stderr suprimido
                with suppress_stderr():
                    if hasattr(whois, 'whois'):
                        # Forma 1: whois.whois() (versão antiga)
                        w = whois.whois(domain)
                    elif hasattr(whois, 'query'):
                        # Forma 2: whois.query() (versão nova)
                        w = whois.query(domain)
                    elif callable(whois):
                        # Forma 3: whois() diretamente
                        w = whois(domain)
                    else:
                        # Tentar importar a função correta
                        try:
                            from whois import whois as whois_func
                            w = whois_func(domain)
                        except ImportError:
                            pass
            except (FileNotFoundError, OSError) as e:
                # Erro relacionado a comandos do sistema (stdbuf, whois command, etc.)
                error_msg = str(e)
                if 'stdbuf' in error_msg or 'No such file' in error_msg:
                    # Tentar usar subprocess diretamente como fallback
                    # Suprimir stderr do subprocess também
                    try:
                        import subprocess
                        import os
                        with open(os.devnull, 'w') as devnull:
                            result = subprocess.run(
                                ['whois', domain],
                                capture_output=True,
                                text=True,
                                timeout=10,
                                stderr=devnull  # Suprimir stderr do comando whois
                            )
                        if result.returncode == 0:
                            # Tentar parsear a saída do whois manualmente
                            # Buscar por padrões comuns de data de criação
                            output = result.stdout.lower()
                            # Padrões comuns: "creation date:", "created:", "registered:", etc.
                            import re
                            date_patterns = [
                                r'creation date[:\s]+(\d{4}-\d{2}-\d{2})',
                                r'created[:\s]+(\d{4}-\d{2}-\d{2})',
                                r'registered[:\s]+(\d{4}-\d{2}-\d{2})',
                                r'data de criação[:\s]+(\d{2}/\d{2}/\d{4})',
                            ]
                            for pattern in date_patterns:
                                match = re.search(pattern, output)
                                if match:
                                    date_str = match.group(1)
                                    try:
                                        if '/' in date_str:
                                            # Formato brasileiro DD/MM/YYYY
                                            created = datetime.strptime(date_str, "%d/%m/%Y")
                                        else:
                                            # Formato ISO YYYY-MM-DD
                                            created = datetime.strptime(date_str, "%Y-%m-%d")
                                        return created.replace(tzinfo=timezone.utc)
                                    except ValueError:
                                        continue
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                        pass
                
                # Não logar erros de stdbuf - são esperados em alguns sistemas
                # Apenas retornar None silenciosamente
                return None
            except Exception as e:
                # Outros erros (timeout, domínio inexistente, etc.)
                # Não logar nenhum erro - silenciar completamente para não poluir o terminal
                return None
            
            if w is None:
                return None
                
        elif WHOIS_LIB == 'pythonwhois':
            w = get_whois(domain)
        else:
            return None
    except Exception as e:
        # Tratar erros de WHOIS (timeout, domínio inexistente, etc.)
        error_msg = str(e)
        # Não logar erros comuns (stdbuf, no match, etc.)
        # Esses erros são esperados e não devem poluir o log
        if ('stdbuf' not in error_msg.lower() and 
            'no match' not in error_msg.lower() and
            'not found' not in error_msg.lower()):
            # Apenas logar erros realmente inesperados
            pass  # Silenciar todos os erros de WHOIS para não poluir o terminal
        return None
    
    # Extrair data de criação dependendo da biblioteca
    if WHOIS_LIB == 'whois':
        # Tentar diferentes atributos possíveis
        created = None
        if hasattr(w, 'creation_date'):
            created = w.creation_date
        elif hasattr(w, 'created'):
            created = w.created
        elif hasattr(w, 'creation'):
            created = w.creation
        elif isinstance(w, dict):
            created = w.get('creation_date') or w.get('created') or w.get('creation')
    elif WHOIS_LIB == 'pythonwhois':
        created = w.get('creation_date', [None])[0] if isinstance(w.get('creation_date'), list) else w.get('creation_date')
    else:
        return None
    
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

