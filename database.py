import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

DB_PATH = Path("savic.db")


def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Inicializa o banco de dados criando as tabelas necessárias."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de empresas (para armazenar CNPJs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT UNIQUE NOT NULL,
            razao_social TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    
    # Adicionar colunas se não existirem (para bancos de dados já criados)
    colunas_para_adicionar = [
        ("email", "TEXT"),
        ("data_abertura", "TEXT"),
        ("email_dominio_diferente", "INTEGER DEFAULT 0"),
        ("email_nao_corporativo", "INTEGER DEFAULT 0"),
        ("email_dominio_recente", "INTEGER DEFAULT 0"),
        ("telefone_suspeito", "INTEGER DEFAULT 0"),
        ("pressa_aprovacao", "INTEGER DEFAULT 0"),
        ("entrega_marcada", "INTEGER DEFAULT 0"),
        ("endereco_entrega_diferente", "INTEGER DEFAULT 0")
    ]
    
    for coluna, tipo in colunas_para_adicionar:
        try:
            cursor.execute(f"ALTER TABLE empresas ADD COLUMN {coluna} {tipo}")
        except sqlite3.OperationalError:
            # Coluna já existe, não precisa fazer nada
            pass
    
    # Tabela para armazenar dados completos das consultas CNPJA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas_cnpj (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT UNIQUE NOT NULL,
            dados_json TEXT NOT NULL,
            consultado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar índice para busca rápida por CNPJ
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultas_cnpj ON consultas_cnpj(cnpj)")
    except sqlite3.OperationalError:
        pass
    
    # Tabela para armazenar avaliações de compatibilidade de CNAEs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes_cnae (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT NOT NULL,
            compativel INTEGER,
            score REAL,
            analise TEXT,
            observacoes_json TEXT,
            avaliado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar índice para busca por CNPJ
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_avaliacoes_cnpj ON avaliacoes_cnae(cnpj)")
    except sqlite3.OperationalError:
        pass
    
    # Tabela para armazenar domínios de email não corporativos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dominios_nao_corporativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dominio TEXT NOT NULL UNIQUE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela para configurações do sistema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracao (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir configuração padrão de limite de dias para WHOIS se não existir
    cursor.execute("SELECT COUNT(*) FROM configuracao WHERE chave = 'whois_min_days'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO configuracao (chave, valor) VALUES ('whois_min_days', '180')")
    
    # Inserir domínios padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM dominios_nao_corporativos")
    if cursor.fetchone()[0] == 0:
        dominios_padrao = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "live.com", "msn.com", "icloud.com", "aol.com",
            "mail.com", "protonmail.com", "yandex.com", "zoho.com"
        ]
        for dominio in dominios_padrao:
            try:
                cursor.execute("INSERT INTO dominios_nao_corporativos (dominio) VALUES (?)", (dominio,))
            except sqlite3.IntegrityError:
                pass
    
    # Tabela para armazenar dados de geocoding e imagens de endereços
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enderecos_geocoding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT NOT NULL,
            endereco_completo TEXT NOT NULL,
            lat REAL,
            lng REAL,
            formatted_address TEXT,
            place_id TEXT,
            street_view_status TEXT,
            street_view_image BLOB,
            street_view_heading INTEGER,
            place_photos_json TEXT,
            place_photos_images TEXT,
            dados_completos_json TEXT,
            processado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Adicionar coluna place_photos_images se não existir
    try:
        cursor.execute("ALTER TABLE enderecos_geocoding ADD COLUMN place_photos_images TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Criar índice para busca por CNPJ
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enderecos_cnpj ON enderecos_geocoding(cnpj)")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Gera hash SHA-256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str) -> bool:
    """Cria um novo usuário no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str) -> Optional[int]:
    """Verifica credenciais do usuário e retorna o ID se válido."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None


def get_user_id(username: str) -> Optional[int]:
    """Retorna o ID do usuário pelo username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None


def get_dominio_email(email: Optional[str]) -> Optional[str]:
    """
    Extrai o domínio de um email.
    
    Args:
        email: Email completo
    
    Returns:
        Domínio do email ou None se inválido
    """
    if not email:
        return None
    
    email = email.strip().lower()
    if "@" in email:
        return email.split("@")[1]
    
    return None


def get_email_cnpja(cnpj: str) -> Optional[str]:
    """
    Busca o email cadastrado no CNPJA para um CNPJ.
    
    Args:
        cnpj: CNPJ da empresa (com ou sem formatação)
    
    Returns:
        Email do CNPJA ou None se não encontrado
    """
    consulta = get_consulta_cnpj(cnpj)
    if not consulta:
        return None
    
    emails = consulta.get("emails", [])
    if emails and isinstance(emails, list) and len(emails) > 0:
        primeiro_email = emails[0]
        if isinstance(primeiro_email, dict):
            return primeiro_email.get("address", "")
        elif isinstance(primeiro_email, str):
            return primeiro_email
    
    return None


def is_dominio_nao_corporativo(dominio: Optional[str]) -> bool:
    """
    Verifica se um domínio está na lista de domínios não corporativos.
    
    Args:
        dominio: Domínio do email (ex: gmail.com)
    
    Returns:
        True se o domínio for não corporativo, False caso contrário
    """
    if not dominio:
        return False
    
    dominio = dominio.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM dominios_nao_corporativos WHERE dominio = ?", (dominio,))
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0


def get_dominios_nao_corporativos() -> List[str]:
    """
    Retorna a lista de domínios não corporativos.
    
    Returns:
        Lista de domínios não corporativos
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT dominio FROM dominios_nao_corporativos ORDER BY dominio")
    resultados = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in resultados]


def adicionar_dominio_nao_corporativo(dominio: str) -> bool:
    """
    Adiciona um domínio à lista de domínios não corporativos.
    
    Args:
        dominio: Domínio a ser adicionado (ex: gmail.com)
    
    Returns:
        True se adicionado com sucesso, False se já existir
    """
    dominio = dominio.strip().lower()
    if not dominio:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO dominios_nao_corporativos (dominio) VALUES (?)", (dominio,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remover_dominio_nao_corporativo(dominio: str) -> bool:
    """
    Remove um domínio da lista de domínios não corporativos.
    
    Args:
        dominio: Domínio a ser removido
    
    Returns:
        True se removido com sucesso, False caso contrário
    """
    dominio = dominio.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM dominios_nao_corporativos WHERE dominio = ?", (dominio,))
    conn.commit()
    removido = cursor.rowcount > 0
    conn.close()
    
    return removido


def get_config_whois_min_days() -> int:
    """
    Retorna o limite mínimo de dias para considerar um domínio como recente.
    
    Returns:
        Número de dias (padrão: 180)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT valor FROM configuracao WHERE chave = 'whois_min_days'")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        try:
            return int(result[0])
        except (ValueError, TypeError):
            pass
    
    return 180  # Padrão


def set_config_whois_min_days(days: int) -> bool:
    """
    Define o limite mínimo de dias para considerar um domínio como recente.
    
    Args:
        days: Número de dias
    
    Returns:
        True se atualizado com sucesso
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO configuracao (chave, valor, atualizado_em)
            VALUES ('whois_min_days', ?, CURRENT_TIMESTAMP)
        """, (str(days),))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao atualizar configuração: {e}")
        return False
    finally:
        conn.close()


def save_empresa(
    cnpj: str,
    razao_social: Optional[str],
    email: Optional[str],
    user_id: int,
    data_abertura: Optional[str] = None,
    telefone_suspeito: bool = False,
    pressa_aprovacao: bool = False,
    entrega_marcada: bool = False,
    endereco_entrega_diferente: bool = False
) -> bool:
    """
    Salva uma empresa no banco de dados.
    
    Args:
        cnpj: CNPJ da empresa
        razao_social: Razão social da empresa
        email: Email de contato fornecido no cadastro
        user_id: ID do usuário que está cadastrando
        data_abertura: Data de abertura da empresa (formato YYYY-MM-DD)
        telefone_suspeito: Flag indicando telefone suspeito
        pressa_aprovacao: Flag indicando pressa em aprovar compra
        entrega_marcada: Flag indicando solicitação de entrega com hora/dia marcados
        endereco_entrega_diferente: Flag indicando endereço de entrega diferente do cadastro
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se o domínio do email é diferente do email do CNPJA
        email_dominio_diferente = False
        email_nao_corporativo = False
        email_dominio_recente = False
        
        if email:
            dominio_cadastro = get_dominio_email(email)
            
            # Verificar se o email é não corporativo
            if dominio_cadastro:
                email_nao_corporativo = is_dominio_nao_corporativo(dominio_cadastro)
            
            # Verificar se o domínio é diferente do email do CNPJA
            email_cnpja = get_email_cnpja(cnpj)
            if dominio_cadastro and email_cnpja:
                dominio_cnpja = get_dominio_email(email_cnpja)
                if dominio_cnpja and dominio_cadastro != dominio_cnpja:
                    email_dominio_diferente = True
            
            # Verificar idade do domínio usando WHOIS
            try:
                from whois_check import check_domain_age
                domain_check = check_domain_age(email)
                if not domain_check.get("error") and domain_check.get("is_recent"):
                    email_dominio_recente = True
            except Exception as e:
                # Se houver erro na verificação WHOIS, não bloquear o cadastro
                print(f"Erro ao verificar idade do domínio: {e}")
                pass
        
        cursor.execute("""
            INSERT INTO empresas 
            (cnpj, razao_social, email, data_abertura, created_by, email_dominio_diferente,
             email_nao_corporativo, email_dominio_recente, telefone_suspeito, pressa_aprovacao, 
             entrega_marcada, endereco_entrega_diferente) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cnpj, razao_social, email, data_abertura, user_id,
            int(email_dominio_diferente), int(email_nao_corporativo), int(email_dominio_recente),
            int(telefone_suspeito), int(pressa_aprovacao),
            int(entrega_marcada), int(endereco_entrega_diferente)
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_empresas_by_user(user_id: int) -> list:
    """Retorna todas as empresas cadastradas por um usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cnpj, razao_social, email, data_abertura, email_dominio_diferente,
               email_nao_corporativo, email_dominio_recente, telefone_suspeito, pressa_aprovacao, 
               entrega_marcada, endereco_entrega_diferente, created_at
        FROM empresas 
        WHERE created_by = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    results = cursor.fetchall()
    conn.close()
    
    empresas = []
    for row in results:
        empresas.append({
            "cnpj": row[0],
            "razao_social": row[1],
            "email": row[2],
            "data_abertura": row[3],
            "email_dominio_diferente": bool(row[4]) if row[4] is not None else False,
            "email_nao_corporativo": bool(row[5]) if row[5] is not None else False,
            "email_dominio_recente": bool(row[6]) if row[6] is not None else False,
            "telefone_suspeito": bool(row[7]) if row[7] is not None else False,
            "pressa_aprovacao": bool(row[8]) if row[8] is not None else False,
            "entrega_marcada": bool(row[9]) if row[9] is not None else False,
            "endereco_entrega_diferente": bool(row[10]) if row[10] is not None else False,
            "created_at": row[11]
        })
    
    return empresas


def get_consulta_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    """
    Busca dados de uma consulta CNPJ no banco de dados.
    Retorna None se não encontrar.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove formatação do CNPJ para busca
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    
    cursor.execute(
        "SELECT dados_json, atualizado_em FROM consultas_cnpj WHERE cnpj = ?",
        (cnpj_clean,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        try:
            dados = json.loads(result[0])
            dados["_cached"] = True
            dados["_cached_at"] = result[1]
            return dados
        except json.JSONDecodeError:
            return None
    
    return None


def save_consulta_cnpj(cnpj: str, dados: Dict[str, Any]) -> bool:
    """
    Salva ou atualiza dados de uma consulta CNPJ no banco de dados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove formatação do CNPJ
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    
    try:
        dados_json = json.dumps(dados, ensure_ascii=False)
        
        # Usa INSERT OR REPLACE para atualizar se já existir
        cursor.execute("""
            INSERT OR REPLACE INTO consultas_cnpj (cnpj, dados_json, atualizado_em)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (cnpj_clean, dados_json))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao salvar consulta: {e}")
        return False
    finally:
        conn.close()


def save_endereco_geocoding(cnpj: str, endereco_completo: str, dados_geocoding: Dict[str, Any]) -> bool:
    """
    Salva ou atualiza dados de geocoding e imagens de um endereço.
    
    Args:
        cnpj: CNPJ da empresa
        endereco_completo: Endereço completo formatado
        dados_geocoding: Dicionário com todos os dados de geocoding, Street View e imagens
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove formatação do CNPJ
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    
    try:
        geocoding = dados_geocoding.get("geocoding", {})
        street_view = dados_geocoding.get("street_view", {})
        street_view_image = dados_geocoding.get("street_view_image", {})
        place_photos = dados_geocoding.get("place_photos", [])
        
        # Preparar dados para salvar
        lat = geocoding.get("lat") if geocoding else None
        lng = geocoding.get("lng") if geocoding else None
        formatted_address = geocoding.get("formatted_address", "")
        place_id = geocoding.get("place_id", "")
        street_view_status = street_view.get("status", "")
        
        # Imagem Street View (apenas bytes, sem metadados)
        street_view_image_bytes = None
        street_view_heading = None
        if street_view_image and street_view_image.get("image_bytes"):
            street_view_image_bytes = street_view_image["image_bytes"]
            street_view_heading = street_view_image.get("heading")
        
        # Place photos (salvar metadados como JSON, imagens como JSON de base64)
        place_photos_metadata = []
        place_photos_base64 = []
        for photo in place_photos:
            place_photos_metadata.append({
                "photo_reference": photo.get("photo_reference", ""),
                "width": photo.get("width", 0),
                "height": photo.get("height", 0)
            })
            # Converter imagem para base64 para armazenar
            if photo.get("image_bytes"):
                import base64
                img_base64 = base64.b64encode(photo["image_bytes"]).decode('utf-8')
                place_photos_base64.append(img_base64)
        place_photos_json = json.dumps(place_photos_metadata, ensure_ascii=False) if place_photos_metadata else None
        place_photos_images_json = json.dumps(place_photos_base64, ensure_ascii=False) if place_photos_base64 else None
        
        # Dados completos como JSON (sem imagens para economizar espaço)
        dados_sem_imagens = dados_geocoding.copy()
        if "street_view_image" in dados_sem_imagens:
            dados_sem_imagens["street_view_image"] = {
                "heading": street_view_heading,
                "lat": lat,
                "lng": lng,
                "has_image": street_view_image_bytes is not None
            }
        if "place_photos" in dados_sem_imagens:
            dados_sem_imagens["place_photos"] = place_photos_metadata
        dados_completos_json = json.dumps(dados_sem_imagens, ensure_ascii=False)
        
        # Salvar ou atualizar
        cursor.execute("""
            INSERT OR REPLACE INTO enderecos_geocoding 
            (cnpj, endereco_completo, lat, lng, formatted_address, place_id, 
             street_view_status, street_view_image, street_view_heading, 
             place_photos_json, place_photos_images, dados_completos_json, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (cnpj_clean, endereco_completo, lat, lng, formatted_address, place_id,
              street_view_status, street_view_image_bytes, street_view_heading,
              place_photos_json, place_photos_images_json, dados_completos_json))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao salvar geocoding: {e}")
        return False
    finally:
        conn.close()


def get_endereco_geocoding(cnpj: str) -> Optional[Dict[str, Any]]:
    """
    Busca dados de geocoding e imagens de um endereço pelo CNPJ.
    
    Args:
        cnpj: CNPJ da empresa
    
    Returns:
        Dicionário com dados de geocoding e imagens, ou None se não encontrar
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove formatação do CNPJ
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    
    cursor.execute("""
        SELECT endereco_completo, lat, lng, formatted_address, place_id,
               street_view_status, street_view_image, street_view_heading,
               place_photos_json, place_photos_images, dados_completos_json, processado_em
        FROM enderecos_geocoding
        WHERE cnpj = ?
        ORDER BY atualizado_em DESC
        LIMIT 1
    """, (cnpj_clean,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        dados = {
            "endereco_completo": result[0],
            "lat": result[1],
            "lng": result[2],
            "formatted_address": result[3],
            "place_id": result[4],
            "street_view_status": result[5],
            "street_view_image_bytes": result[6],
            "street_view_heading": result[7],
            "place_photos_json": result[8],
            "place_photos_images": result[9],
            "dados_completos_json": result[10],
            "processado_em": result[11]
        }
        
        # Parse JSONs
        if dados["place_photos_json"]:
            try:
                place_photos_metadata = json.loads(dados["place_photos_json"])
                place_photos_images = []
                if dados["place_photos_images"]:
                    try:
                        place_photos_base64 = json.loads(dados["place_photos_images"])
                        import base64
                        for i, img_base64 in enumerate(place_photos_base64):
                            if i < len(place_photos_metadata):
                                img_bytes = base64.b64decode(img_base64)
                                place_photos_images.append({
                                    **place_photos_metadata[i],
                                    "image_bytes": img_bytes
                                })
                    except:
                        pass
                
                dados["place_photos"] = place_photos_images if place_photos_images else place_photos_metadata
            except:
                dados["place_photos"] = []
        else:
            dados["place_photos"] = []
        
        if dados["dados_completos_json"]:
            try:
                dados_completos = json.loads(dados["dados_completos_json"])
                dados.update(dados_completos)
            except:
                pass
        
        return dados
    
    return None


def save_avaliacao_cnae(cnpj: str, avaliacao: Dict[str, Any]) -> bool:
    """
    Salva ou atualiza uma avaliação de compatibilidade de CNAEs.
    
    Args:
        cnpj: CNPJ da empresa (sem formatação)
        avaliacao: Dicionário com resultado da avaliação
            {
                "compativel": bool,
                "score": float,
                "analise": str,
                "observacoes": List[str]
            }
    
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Remove formatação do CNPJ
        cnpj_clean = "".join(filter(str.isdigit, cnpj))
        
        compativel = int(avaliacao.get("compativel", False)) if avaliacao.get("compativel") is not None else None
        score = avaliacao.get("score")
        analise = avaliacao.get("analise", "")
        observacoes_json = json.dumps(avaliacao.get("observacoes", []), ensure_ascii=False)
        
        cursor.execute("""
            INSERT OR REPLACE INTO avaliacoes_cnae 
            (cnpj, compativel, score, analise, observacoes_json, avaliado_em)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (cnpj_clean, compativel, score, analise, observacoes_json))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao salvar avaliação CNAE: {e}")
        return False
    finally:
        conn.close()


def get_avaliacao_cnae(cnpj: str) -> Optional[Dict[str, Any]]:
    """
    Busca avaliação de compatibilidade de CNAEs para um CNPJ.
    
    Args:
        cnpj: CNPJ da empresa
    
    Returns:
        Dicionário com dados da avaliação ou None se não encontrado
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove formatação do CNPJ
    cnpj_clean = "".join(filter(str.isdigit, cnpj))
    
    cursor.execute("""
        SELECT compativel, score, analise, observacoes_json, avaliado_em
        FROM avaliacoes_cnae
        WHERE cnpj = ?
        ORDER BY avaliado_em DESC
        LIMIT 1
    """, (cnpj_clean,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        observacoes = []
        if result[3]:
            try:
                observacoes = json.loads(result[3])
            except:
                pass
        
        return {
            "compativel": bool(result[0]) if result[0] is not None else None,
            "score": result[1],
            "analise": result[2],
            "observacoes": observacoes,
            "avaliado_em": result[4]
        }
    
    return None
