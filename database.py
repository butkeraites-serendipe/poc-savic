import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

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
    
    # Adicionar coluna email se não existir (para bancos de dados já criados)
    try:
        cursor.execute("ALTER TABLE empresas ADD COLUMN email TEXT")
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


def save_empresa(cnpj: str, razao_social: Optional[str], email: Optional[str], user_id: int) -> bool:
    """Salva uma empresa no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO empresas (cnpj, razao_social, email, created_by) VALUES (?, ?, ?, ?)",
            (cnpj, razao_social, email, user_id)
        )
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
    
    cursor.execute(
        "SELECT cnpj, razao_social, email, created_at FROM empresas WHERE created_by = ? ORDER BY created_at DESC",
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]


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
