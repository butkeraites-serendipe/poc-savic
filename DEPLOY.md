# Guia de Deploy - SAVIC

Este documento descreve as melhores opções para fazer deploy da aplicação SAVIC.

## Opções de Deploy

### 1. Streamlit Cloud (Recomendado - Mais Fácil)

**Vantagens:**
- Gratuito para projetos públicos
- Deploy automático via GitHub
- HTTPS incluído
- Escalável automaticamente
- Sem necessidade de servidor próprio

**Passos:**

1. **Criar repositório no GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/seu-usuario/poc-savic.git
   git push -u origin main
   ```

2. **Acessar Streamlit Cloud:**
   - Vá para https://share.streamlit.io/
   - Faça login com sua conta GitHub
   - Clique em "New app"
   - Selecione o repositório e branch
   - Configure:
     - **Main file path:** `app.py`
     - **App URL:** (opcional, será gerado automaticamente)

3. **Configurar variáveis de ambiente:**
   - No painel do Streamlit Cloud, vá em "Settings" → "Secrets"
   - Adicione as variáveis do arquivo `.env`:
     ```toml
     GEMINI_API_KEY=seu_gemini_key
     GOOGLE_MAPS_API_KEY=seu_google_maps_key
     CNPJA_API_KEY=seu_cnpja_key
     ```

4. **Deploy:**
   - O deploy é automático a cada push no GitHub
   - A URL será: `https://seu-app.streamlit.app`

**Limitações:**
- Aplicações públicas são gratuitas
- Aplicações privadas requerem plano pago
- Limite de uso de recursos (CPU/RAM)

---

### 2. Docker + Servidor Cloud (AWS, GCP, Azure, DigitalOcean)

**Vantagens:**
- Controle total sobre o ambiente
- Pode ser privado
- Escalável conforme necessidade
- Mais flexível

**Passos:**

1. **Criar Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Instalar dependências do sistema
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Copiar requirements e instalar dependências Python
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copiar código da aplicação
   COPY . .
   
   # Expor porta
   EXPOSE 8501
   
   # Comando para rodar Streamlit
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Criar docker-compose.yml (opcional):**
   ```yaml
   version: '3.8'
   
   services:
     savic:
       build: .
       ports:
         - "8501:8501"
       environment:
         - GEMINI_API_KEY=${GEMINI_API_KEY}
         - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
         - CNPJA_API_KEY=${CNPJA_API_KEY}
       volumes:
         - ./savic.db:/app/savic.db
       restart: unless-stopped
   ```

3. **Deploy no servidor:**
   
   **Opção A - Usando docker compose (recomendado):**
   ```bash
   # No servidor, crie um arquivo .env com as variáveis:
   # GEMINI_API_KEY=seu_key
   # GOOGLE_MAPS_API_KEY=seu_key
   # CNPJA_API_KEY=seu_key
   
   docker compose up -d
   ```
   
   **Acessar a aplicação:**
   - Se estiver rodando localmente: http://localhost:8501
   - Se estiver em um servidor remoto: http://IP_DO_SERVIDOR:8501
   - Para verificar se está rodando: `docker compose ps`
   - Para ver os logs: `docker compose logs -f`
   
   **Credenciais padrão:**
   - Username: `savic`
   - Senha: `serendipe@123`
   
   > **Nota:** O usuário padrão é criado automaticamente na primeira inicialização do container. Se você já tinha um banco de dados antigo, pode ser necessário fazer rebuild:
   > ```bash
   > docker compose down
   > docker compose build --no-cache
   > docker compose up -d
   > ```
   
   **Opção B - Usando docker build/run diretamente:**
   ```bash
   # No servidor
   docker build -t savic-app .
   docker run -d \
     -p 8501:8501 \
     -e GEMINI_API_KEY=seu_key \
     -e GOOGLE_MAPS_API_KEY=seu_key \
     -e CNPJA_API_KEY=seu_key \
     -v $(pwd)/savic.db:/app/savic.db \
     --name savic \
     --restart unless-stopped \
     savic-app
   ```

4. **Configurar Nginx como reverse proxy (recomendado):**
   ```nginx
   server {
       listen 80;
       server_name seu-dominio.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 86400;
       }
   }
   ```

5. **Configurar SSL com Let's Encrypt:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d seu-dominio.com
   ```

---

### 3. Railway.app

**Vantagens:**
- Deploy simples via GitHub
- HTTPS automático
- Variáveis de ambiente fáceis
- Plano gratuito disponível

**Passos:**

1. Acesse https://railway.app
2. Conecte seu repositório GitHub
3. Configure as variáveis de ambiente
4. Railway detecta automaticamente que é uma aplicação Python
5. Configure o comando de start: `streamlit run app.py --server.port=$PORT`

---

### 4. Render.com

**Vantagens:**
- Gratuito para projetos pessoais
- Deploy via GitHub
- HTTPS automático

**Passos:**

1. Acesse https://render.com
2. Crie um novo "Web Service"
3. Conecte o repositório GitHub
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Adicione as variáveis de ambiente

---

## Configurações Importantes

### Variáveis de Ambiente Necessárias

Certifique-se de configurar todas as variáveis no ambiente de produção:

```bash
GEMINI_API_KEY=sua_chave_gemini
GOOGLE_MAPS_API_KEY=sua_chave_google_maps
CNPJA_API_KEY=sua_chave_cnpja
```

### Banco de Dados

O banco de dados SQLite (`savic.db`) é criado automaticamente. Para produção, considere:

1. **Backup regular** do arquivo `savic.db`
2. **Migração para PostgreSQL** (se necessário escalar):
   - Substituir SQLite por PostgreSQL
   - Atualizar `database.py` para usar `psycopg2` ou `asyncpg`

### Segurança

1. **Nunca commite o arquivo `.env`** no Git
2. **Use variáveis de ambiente** no servidor
3. **Configure firewall** para limitar acesso
4. **Use HTTPS** sempre (Let's Encrypt gratuito)
5. **Limite acesso** por IP se necessário (via Nginx)

---

## Recomendação Final

Para começar rapidamente: **Streamlit Cloud** (opção 1)
Para produção com mais controle: **Docker + Servidor Cloud** (opção 2)

---

## Troubleshooting

### Erro: "Port already in use"
- Verifique se outra instância está rodando: `lsof -i :8501`
- Pare o processo ou use outra porta

### Erro: "Module not found"
- Verifique se todas as dependências estão no `requirements.txt`
- Execute: `pip install -r requirements.txt`

### Banco de dados não persiste
- Certifique-se de que o volume está montado corretamente no Docker
- Verifique permissões de escrita no diretório

### API Keys não funcionam
- Verifique se as variáveis de ambiente estão configuradas
- Teste localmente com `.env` antes de fazer deploy

