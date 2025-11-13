# SAVIC - Sistema de Análise de Empresas

Aplicação web desenvolvida com Streamlit para cadastro e análise de empresas através do CNPJ.

## 🚀 Funcionalidades

- **Sistema de Autenticação**: Login e registro de usuários
- **Consulta de Dados Cadastrais**: Consulta automática de dados de empresas via API CNPJA
- **Cache Inteligente**: Armazenamento de consultas para evitar requisições desnecessárias
- **Geocoding e Imagens**: Conversão de endereços em coordenadas e obtenção de imagens da fachada
- **Street View**: Visualização de imagens Street View quando disponível
- **Places Photos**: Acesso a fotos do Google Places quando disponíveis
- **Cadastro de Empresas**: Formulário para cadastro de empresas por CNPJ
- **Preenchimento Automático**: Preenchimento automático do formulário com dados consultados
- **Todos os CNAEs**: Exibição completa de todas as atividades (principal + secundárias)
- **Banco de Dados SQLite**: Armazenamento local de dados e imagens
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

4. Configure as chaves das APIs:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione suas chaves:
   ```
   CNPJA_API_KEY=sua_chave_cnpja_aqui
   GOOGLE_MAPS_API_KEY=sua_chave_google_maps_aqui
   ```
   - Obtenha a chave CNPJA em: https://cnpja.com/api
   - Obtenha a chave Google Maps em: https://console.cloud.google.com/google/maps-apis

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
   - Se o CNPJ já foi consultado antes, os dados virão do cache (mais rápido)
   - Use o botão "🔄 Atualizar da API" para forçar uma nova consulta
   - Todos os CNAEs (principal + secundárias) são exibidos em uma tabela

3. **Processar Endereço e Obter Imagens**:
   - Após consultar um CNPJ, clique no botão "🗺️ Processar Endereço"
   - O sistema irá:
     - Converter o endereço em coordenadas (lat/lng)
     - Verificar disponibilidade de Street View
     - Obter imagem da fachada via Street View
     - Buscar fotos do Google Places (se disponível)
   - Todas as informações e imagens são armazenadas e relacionadas ao CNPJ
   - As imagens podem ser visualizadas diretamente na interface

4. **Cadastrar Empresa**:
   - Após fazer login, você verá a homepage
   - Preencha o formulário com o CNPJ da empresa (com ou sem formatação)
   - Opcionalmente, informe a razão social e email
   - Os campos podem ser preenchidos automaticamente após uma consulta
   - Clique em "Cadastrar Empresa"

5. **Visualizar Empresas**:
   - Todas as empresas cadastradas aparecerão na lista abaixo do formulário
   - As empresas são organizadas por data de cadastro (mais recentes primeiro)

## 🗂️ Estrutura do Projeto

```
poc-savic/
├── app.py              # Arquivo principal da aplicação
├── database.py          # Módulo de gerenciamento do banco de dados
├── auth.py             # Módulo de autenticação
├── cnpja_api.py        # Módulo de integração com API CNPJA
├── google_maps_api.py  # Módulo de integração com Google Maps API
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
- **Tabela `consultas_cnpj`**: Armazena dados completos das consultas CNPJA (cache)
- **Tabela `enderecos_geocoding`**: Armazena dados de geocoding, coordenadas e imagens de endereços

## 🔒 Segurança

- Senhas são armazenadas com hash SHA-256
- Cada usuário só visualiza suas próprias empresas cadastradas
- Validação de formato de CNPJ antes do cadastro

## 🔌 Integrações com APIs

### API CNPJA

O sistema utiliza a API CNPJA para consultar dados cadastrais de empresas na Receita Federal. A consulta retorna informações como:

- Razão Social e Nome Fantasia
- CNPJ formatado
- Status e Situação Cadastral
- Data de Abertura
- Endereço completo
- Email e Telefone
- Todas as atividades CNAE (principal + secundárias)

**Documentação**: https://cnpja.com/api/reference#tag/cadastro-de-contribuintes

### Google Maps API

O sistema utiliza a Google Maps API para:

- **Geocoding**: Converter endereços em coordenadas (latitude/longitude)
- **Street View**: Verificar disponibilidade e obter imagens da fachada
- **Places API**: Buscar fotos de estabelecimentos quando disponíveis

**APIs utilizadas**:
- Geocoding API
- Street View Static API
- Street View Metadata API
- Places API (Text Search, Details, Photos)

**Documentação**: https://developers.google.com/maps/documentation

## 📝 Notas

- O banco de dados SQLite é criado localmente no diretório do projeto
- O arquivo `savic.db` é ignorado pelo Git (não será versionado)
- O arquivo `.env` com a chave da API também não é versionado por segurança
- Para produção, considere usar um banco de dados mais robusto e implementar validação de dígitos verificadores do CNPJ
- A API CNPJA possui limites de requisições conforme seu plano de assinatura