# SAVIC - Sistema de Análise de Empresas

Aplicação web desenvolvida com Streamlit para cadastro e análise de empresas através do CNPJ.

## 🚀 Funcionalidades

- **Sistema de Autenticação**: Login e registro de usuários
- **Consulta de Dados Cadastrais**: Consulta automática de dados de empresas via API CNPJA
- **Cadastro de Empresas**: Formulário para cadastro de empresas por CNPJ
- **Preenchimento Automático**: Preenchimento automático do formulário com dados consultados
- **Banco de Dados SQLite**: Armazenamento local de dados
- **Interface Moderna**: Interface limpa e intuitiva

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

1. Clone o repositório ou navegue até o diretório do projeto:
```bash
cd poc-savic
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure a chave da API CNPJA:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione sua chave da API:
   ```
   CNPJA_API_KEY=sua_chave_api_aqui
   ```
   - Obtenha sua chave em: https://cnpja.com/api

## 🎯 Como Executar

Execute o aplicativo Streamlit:
```bash
streamlit run app.py
```

O aplicativo será aberto automaticamente no seu navegador em `http://localhost:8501`.

## 📖 Como Usar

1. **Primeiro Acesso**: 
   - Na tela de login, vá para a aba "Registrar"
   - Crie uma conta com username e senha
   - Retorne para a aba "Login" e faça login

2. **Consultar Dados Cadastrais**:
   - Na homepage, use a seção "🔍 Consultar Dados Cadastrais"
   - Digite o CNPJ da empresa e clique em "Consultar CNPJ"
   - Os dados cadastrais serão exibidos (razão social, endereço, situação, etc.)
   - Use o botão "💾 Usar estes dados no cadastro" para preencher automaticamente o formulário

3. **Cadastrar Empresa**:
   - Após fazer login, você verá a homepage
   - Preencha o formulário com o CNPJ da empresa (com ou sem formatação)
   - Opcionalmente, informe a razão social e email
   - Os campos podem ser preenchidos automaticamente após uma consulta
   - Clique em "Cadastrar Empresa"

4. **Visualizar Empresas**:
   - Todas as empresas cadastradas aparecerão na lista abaixo do formulário
   - As empresas são organizadas por data de cadastro (mais recentes primeiro)

## 🗂️ Estrutura do Projeto

```
poc-savic/
├── app.py              # Arquivo principal da aplicação
├── database.py          # Módulo de gerenciamento do banco de dados
├── auth.py             # Módulo de autenticação
├── cnpja_api.py        # Módulo de integração com API CNPJA
├── pages/
│   ├── login.py        # Página de login e registro
│   └── homepage.py     # Homepage com formulário de CNPJ
├── requirements.txt    # Dependências do projeto
├── .env                # Variáveis de ambiente (não versionado)
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Este arquivo
```

## 🗄️ Banco de Dados

O banco de dados SQLite (`savic.db`) é criado automaticamente na primeira execução e contém:

- **Tabela `users`**: Armazena informações dos usuários
- **Tabela `empresas`**: Armazena CNPJs e informações das empresas cadastradas

## 🔒 Segurança

- Senhas são armazenadas com hash SHA-256
- Cada usuário só visualiza suas próprias empresas cadastradas
- Validação de formato de CNPJ antes do cadastro

## 🔌 Integração com API CNPJA

O sistema utiliza a API CNPJA para consultar dados cadastrais de empresas na Receita Federal. A consulta retorna informações como:

- Razão Social e Nome Fantasia
- CNPJ formatado
- Status e Situação Cadastral
- Data de Abertura
- Endereço completo
- Email e Telefone
- Atividade Principal (CNAE)

**Documentação da API**: https://cnpja.com/api/reference#tag/cadastro-de-contribuintes

## 📝 Notas

- O banco de dados SQLite é criado localmente no diretório do projeto
- O arquivo `savic.db` é ignorado pelo Git (não será versionado)
- O arquivo `.env` com a chave da API também não é versionado por segurança
- Para produção, considere usar um banco de dados mais robusto e implementar validação de dígitos verificadores do CNPJ
- A API CNPJA possui limites de requisições conforme seu plano de assinatura