#!/bin/bash
set -e

# Garantir que o banco de dados está inicializado e o usuário padrão existe
python3 -c "
import sys
sys.path.insert(0, '/app')

from database import init_database, verify_user, hash_password
import sqlite3

# Inicializar banco (cria tabelas se não existirem)
init_database()

# Garantir que o usuário 'savic' existe
from database import DB_PATH
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

username = 'savic'
password = 'serendipe@123'
password_hash = hash_password(password)

# Verificar se o usuário existe
cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
result = cursor.fetchone()

if result:
    user_id, existing_hash = result
    if existing_hash != password_hash:
        # Atualizar senha
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, username))
        conn.commit()
        print(f'✓ Senha do usuário {username} atualizada (ID: {user_id})')
    else:
        print(f'✓ Usuário {username} já existe com senha correta (ID: {user_id})')
else:
    # Criar usuário
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    user_id = cursor.lastrowid
    print(f'✓ Usuário {username} criado (ID: {user_id})')

# Testar login
if verify_user(username, password):
    print(f'✓ Login testado com sucesso!')
else:
    print(f'✗ ERRO: Login não funcionou!')

conn.close()
"

# Executar Streamlit
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

