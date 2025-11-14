#!/usr/bin/env python3
"""
Script para garantir que o usuário padrão 'savic' existe no banco de dados.
Execute este script após o deploy para garantir que o usuário está criado.
"""
from database import init_database, verify_user, hash_password
import sqlite3
from pathlib import Path

DB_PATH = Path("savic.db")

def garantir_usuario_savic():
    """Garante que o usuário 'savic' existe com a senha correta."""
    # Inicializar banco (cria tabelas se não existirem)
    init_database()
    
    # Conectar ao banco
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    username = "savic"
    password = "serendipe@123"
    password_hash = hash_password(password)
    
    # Verificar se o usuário existe
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        user_id, existing_hash = result
        # Verificar se a senha está correta
        if existing_hash == password_hash:
            print(f"✓ Usuário '{username}' já existe com a senha correta (ID: {user_id})")
        else:
            # Atualizar senha
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (password_hash, username)
            )
            conn.commit()
            print(f"✓ Senha do usuário '{username}' atualizada (ID: {user_id})")
    else:
        # Criar usuário
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"✓ Usuário '{username}' criado com sucesso (ID: {user_id})")
    
    # Verificar se funciona
    if verify_user(username, password):
        print(f"✓ Login testado com sucesso!")
    else:
        print(f"✗ ERRO: Login não funcionou após criar/atualizar usuário!")
    
    conn.close()

if __name__ == "__main__":
    garantir_usuario_savic()

