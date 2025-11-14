# Relatório Excel de Análise de Risco

## 📋 Visão Geral

Sistema de geração de relatórios Excel formatados com todos os dados da análise de risco de endereço.

## 📦 Instalação

Instale a dependência necessária:

```bash
pip install openpyxl
```

Ou instale todas as dependências:

```bash
pip install -r requirements.txt
```

## 📊 Formato do Relatório

O relatório Excel é gerado com formato fixo e inclui as seguintes seções:

### 1. Dados da Empresa
- CNPJ (formatado)
- Razão Social
- Nome Fantasia
- Data de Abertura

### 2. Endereço
- Endereço Completo
- Coordenadas (Lat/Lng)
- Place ID

### 3. Atividades CNAE
- Tabela com CNAE Principal e Secundários
- Código e Descrição de cada CNAE

### 4. Resultado da Análise de Risco
- **RISCO FINAL** (com destaque colorido):
  - ALTO (vermelho)
  - MÉDIO (amarelo)
  - BAIXO (verde)
- Score de Risco (0-100)
- Tipo Local Esperado (CNAE)

### 5. Análise Visual (Gemini Vision)
- Zona Aparente
- Tipo de Via
- Presença de Placas Comerciais
- Presença de Vitrines/Lojas
- Presença de Casas Residenciais
- Compatibilidade CNAE
- Sugestão de Risco
- Motivos de Incompatibilidade (lista)

### 6. Flags de Risco
- Lista completa de flags detectados

### 7. Análise Detalhada
- Texto completo da análise do Gemini

## 🎨 Formatação

O relatório utiliza:
- **Cores**: 
  - Azul escuro para títulos
  - Cinza claro para cabeçalhos de seção
  - Vermelho para risco ALTO
  - Amarelo para risco MÉDIO
  - Verde para risco BAIXO
- **Bordas**: Todas as células têm bordas
- **Alinhamento**: Texto alinhado à esquerda, números centralizados
- **Largura de colunas**: Ajustada automaticamente

## 🔧 Uso

### Via Interface Streamlit

1. Consulte um CNPJ
2. Processe o endereço
3. Execute a análise de risco
4. Clique no botão **"📥 Baixar Relatório Excel"**
5. O arquivo será baixado automaticamente

### Via Código Python

```python
from relatorio_excel import gerar_relatorio_para_cnpj

# Gerar relatório e salvar em arquivo
gerar_relatorio_para_cnpj("12345678000190", caminho_saida="relatorio.xlsx")

# Ou gerar e obter bytes
relatorio_bytes = gerar_relatorio_para_cnpj("12345678000190")
with open("relatorio.xlsx", "wb") as f:
    f.write(relatorio_bytes)
```

### Função Avançada

```python
from relatorio_excel import gerar_relatorio_excel
from database import get_consulta_cnpj, get_endereco_geocoding, get_analise_risco_endereco

cnpj = "12345678000190"

# Buscar dados
dados_cnpj = get_consulta_cnpj(cnpj)
dados_endereco = get_endereco_geocoding(cnpj)
analise_risco = get_analise_risco_endereco(cnpj)

# Preparar dados
dados_empresa = {
    "razao_social": dados_cnpj.get("company", {}).get("name", "N/A"),
    "nome_fantasia": dados_cnpj.get("alias", "N/A"),
    "data_abertura": dados_cnpj.get("founded", "N/A")
}

# Preparar CNAEs
cnaes = []
if dados_cnpj.get("mainActivity"):
    cnae_principal = dados_cnpj["mainActivity"]
    cnaes.append({
        "codigo": str(cnae_principal.get("id", ""))[:7],
        "descricao": cnae_principal.get("text", "")
    })

# Gerar relatório
gerar_relatorio_excel(
    cnpj=cnpj,
    dados_empresa=dados_empresa,
    dados_endereco=dados_endereco,
    analise_risco=analise_risco,
    cnaes=cnaes,
    caminho_saida="relatorio.xlsx"
)
```

## 📝 Estrutura do Arquivo

O arquivo Excel gerado contém uma única planilha chamada "Análise de Risco" com todas as informações organizadas em seções numeradas.

## ⚠️ Requisitos

- Python 3.7+
- openpyxl >= 3.1.0
- Dados da análise de risco já salvos no banco de dados

## 🔍 Exemplo de Nome de Arquivo

O arquivo gerado pela interface Streamlit terá o formato:
```
relatorio_risco_07275920000161_20250112_143025.xlsx
```

Onde:
- `07275920000161` é o CNPJ
- `20250112_143025` é a data e hora de geração

## 📌 Notas

- O relatório é gerado em tempo real a partir dos dados do banco
- Se a análise não existir, será exibido um erro
- O formato é fixo e padronizado para facilitar análise e compartilhamento
- O arquivo pode ser aberto no Excel, Google Sheets, LibreOffice, etc.

