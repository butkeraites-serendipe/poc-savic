"""
Módulo para detecção de typosquatting em domínios de email.
Detecta quando um domínio é similar a outro (possível tentativa de fraude).
"""

from typing import Optional, Dict, Any
import re


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcula a distância de Levenshtein entre duas strings.
    Retorna o número mínimo de edições necessárias para transformar s1 em s2.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def normalize_domain(domain: str) -> str:
    """
    Normaliza um domínio para comparação (remove www, converte para minúsculas).
    """
    if not domain:
        return ""
    
    domain = domain.lower().strip()
    # Remove www. se presente
    if domain.startswith("www."):
        domain = domain[4:]
    
    return domain


def detect_common_typos(domain1: str, domain2: str) -> list:
    """
    Detecta substituições comuns usadas em typosquatting.
    Retorna lista de substituições encontradas.
    """
    common_replacements = {
        'o': '0', '0': 'o',
        'i': '1', '1': 'i', 'l': '1',
        'e': '3', '3': 'e',
        'a': '4', '4': 'a',
        's': '5', '5': 's',
        'g': '6', '6': 'g',
        't': '7', '7': 't',
        'b': '8', '8': 'b',
        'g': '9', '9': 'g',
    }
    
    typos = []
    if len(domain1) == len(domain2):
        for i, (c1, c2) in enumerate(zip(domain1, domain2)):
            if c1 != c2:
                # Verificar se é uma substituição comum
                if c1 in common_replacements and common_replacements[c1] == c2:
                    typos.append(f"Posição {i}: '{c1}' -> '{c2}'")
                elif c2 in common_replacements and common_replacements[c2] == c1:
                    typos.append(f"Posição {i}: '{c2}' -> '{c1}'")
    
    return typos


def detect_typosquatting(
    dominio_cadastro: Optional[str],
    dominio_cnpja: Optional[str],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Detecta se o domínio cadastrado é similar ao domínio do CNPJA (possível typosquatting).
    
    Args:
        dominio_cadastro: Domínio do email cadastrado
        dominio_cnpja: Domínio do email do CNPJA
        threshold: Limiar de similaridade (0-1). Domínios com similaridade >= threshold são considerados suspeitos.
    
    Returns:
        Dicionário com resultado da análise:
        {
            "suspeito": bool,
            "similaridade": float (0-1),
            "distancia_levenshtein": int,
            "typos_detectados": list,
            "dominio_cadastro": str,
            "dominio_cnpja": str,
            "mensagem": str
        }
    """
    if not dominio_cadastro or not dominio_cnpja:
        return {
            "suspeito": False,
            "similaridade": 0.0,
            "distancia_levenshtein": None,
            "typos_detectados": [],
            "dominio_cadastro": dominio_cadastro or "",
            "dominio_cnpja": dominio_cnpja or "",
            "mensagem": "Domínios não fornecidos para comparação"
        }
    
    # Normalizar domínios
    dom1 = normalize_domain(dominio_cadastro)
    dom2 = normalize_domain(dominio_cnpja)
    
    # Se são idênticos, não é typosquatting
    if dom1 == dom2:
        return {
            "suspeito": False,
            "similaridade": 1.0,
            "distancia_levenshtein": 0,
            "typos_detectados": [],
            "dominio_cadastro": dom1,
            "dominio_cnpja": dom2,
            "mensagem": "Domínios idênticos"
        }
    
    # Calcular distância de Levenshtein
    distancia = levenshtein_distance(dom1, dom2)
    
    # Calcular similaridade (0-1)
    max_len = max(len(dom1), len(dom2))
    if max_len == 0:
        similaridade = 0.0
    else:
        similaridade = 1.0 - (distancia / max_len)
    
    # Detectar typos comuns
    typos = detect_common_typos(dom1, dom2)
    
    # Considerar suspeito se similaridade >= threshold
    suspeito = similaridade >= threshold
    
    # Gerar mensagem
    if suspeito:
        if typos:
            mensagem = f"⚠️ Domínio similar detectado (similaridade: {similaridade:.1%}). Possíveis typos: {', '.join(typos)}"
        else:
            mensagem = f"⚠️ Domínio similar detectado (similaridade: {similaridade:.1%}, distância: {distancia} caracteres)"
    else:
        mensagem = f"✅ Domínios diferentes (similaridade: {similaridade:.1%})"
    
    return {
        "suspeito": suspeito,
        "similaridade": similaridade,
        "distancia_levenshtein": distancia,
        "typos_detectados": typos,
        "dominio_cadastro": dom1,
        "dominio_cnpja": dom2,
        "mensagem": mensagem
    }

