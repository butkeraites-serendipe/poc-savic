FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    whois \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para banco de dados (se necessário)
RUN mkdir -p /app/data

# Copiar e tornar executável o script de entrada
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Expor porta
EXPOSE 8501

# Usar script de entrada que garante criação do usuário
ENTRYPOINT ["/app/docker-entrypoint.sh"]

