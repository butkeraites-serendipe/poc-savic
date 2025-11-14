# Análise de Escopo vs Implementação - Relatório Excel

## ✅ Itens Implementados

### a. Consulta automática à base da Receita Federal e CNPJA.com
- ✅ **Implementado**: Consulta CNPJA via `cnpja_api.py`
- ✅ **No Relatório**: Data de abertura, CNAEs (código e descrição), endereço
- ✅ **Status**: Completo

### b. Utilização de técnicas de IA para analisar CNAEs
- ✅ **Implementado**: `gemini_api.py` com função `avaliar_compatibilidade_cnaes()`
- ✅ **Armazenado**: Tabela `avaliacoes_cnae` no banco de dados
- ❌ **No Relatório**: **FALTANDO** - Análise semântica de CNAE não aparece no Excel
- ⚠️ **Status**: Implementado mas não incluído no relatório

### c. Algoritmo para identificar e-mails falsos parecidos com domínio lícito
- ❌ **Implementado**: **NÃO IMPLEMENTADO**
- ❌ **No Relatório**: **FALTANDO**
- ⚠️ **Status**: **FALTA IMPLEMENTAR** (typosquatting detection)

### d. Sinalização de e-mail não corporativo
- ✅ **Implementado**: Checkbox na interface, flag `email_nao_corporativo`
- ✅ **No Relatório**: Aparece em "Sinalizações de Risco (Email)"
- ✅ **Status**: Completo

### e. Verificação automática da data de criação do domínio
- ✅ **Implementado**: `whois_check.py` com `check_domain_age()`
- ✅ **Armazenado**: Flag `email_dominio_recente` no banco
- ⚠️ **No Relatório**: **FALTANDO DETALHES** - Só mostra flag, não mostra:
  - Data de criação do domínio
  - Idade do domínio em dias
  - Limite configurado (min_days)
- ⚠️ **Status**: Parcialmente no relatório

### f. Utilização de algoritmo de IA para analisar imagem do endereço
- ✅ **Implementado**: `address_risk_service.py` com Gemini Vision
- ✅ **No Relatório**: Seção completa "6. ANÁLISE VISUAL (GEMINI VISION)"
- ✅ **Status**: Completo

### g. Geração de relatório em Excel
- ✅ **Implementado**: `relatorio_excel.py`
- ✅ **No Relatório**: Formato fixo com todas as seções principais
- ✅ **Status**: Completo

---

## ❌ O que FALTA no Relatório Excel

### 1. Análise Semântica de CNAE (Item b)
**O que falta:**
- Resultado da análise de compatibilidade entre CNAEs
- Score de compatibilidade (0-100)
- Análise textual da compatibilidade
- Observações sobre inconsistências entre CNAEs

**Onde buscar:** Tabela `avaliacoes_cnae` via `get_avaliacao_cnae(cnpj)`

**Sugestão de seção:**
```
3.5. ANÁLISE SEMÂNTICA DE CNAE (IA)
- Compatível: Sim/Não
- Score: 85/100
- Análise: [texto completo]
- Observações:
  1. [observação 1]
  2. [observação 2]
```

### 2. Detalhes da Idade do Domínio (Item e)
**O que falta:**
- Data de criação do domínio (formato DD/MM/YYYY)
- Idade do domínio em dias
- Limite configurado (min_days)
- Status: Recente/Antigo

**Onde buscar:** `whois_check.check_domain_age(email)` retorna:
- `creation_date`
- `age_days`
- `threshold_days`
- `is_recent`

**Sugestão de seção:**
```
4. ANÁLISE DE EMAIL E DOMÍNIO
  ...
  - Data de Criação do Domínio: 15/03/2024
  - Idade do Domínio: 45 dias
  - Limite Configurado: 180 dias
  - Status: ⚠️ Domínio criado recentemente
```

### 3. Detecção de Typosquatting (Item c)
**O que falta:**
- Algoritmo completo para detectar domínios similares
- Comparação com domínio do CNPJA
- Exemplo: `lemovo.com` vs `lenovo.com`

**Status:** **NÃO IMPLEMENTADO** - Precisa criar:
- Função para calcular similaridade de strings (Levenshtein, etc.)
- Comparação entre domínio cadastrado e domínio CNPJA
- Flag `email_dominio_suspeito` ou similar

**Sugestão de implementação:**
```python
def detectar_typosquatting(dominio_cadastro: str, dominio_cnpja: str) -> Dict[str, Any]:
    """
    Detecta se o domínio cadastrado é similar ao domínio do CNPJA
    (possível typosquatting).
    """
    # Calcular distância de Levenshtein
    # Verificar substituições comuns (o->0, i->l, etc.)
    # Retornar score de similaridade e flag de suspeita
```

### 4. Outras Sinalizações de Risco
**O que falta no relatório:**
- Telefone suspeito (`telefone_suspeito`)
- Pressa em aprovação (`pressa_aprovacao`)
- Entrega marcada (`entrega_marcada`)
- Endereço de entrega diferente (`endereco_entrega_diferente`)

**Onde buscar:** Tabela `empresas`, campos já existentes

**Sugestão de seção:**
```
4.5. OUTRAS SINALIZAÇÕES DE RISCO
- Telefone Suspeito: ❌ Sim / ✅ Não
- Pressa em Aprovação: ❌ Sim / ✅ Não
- Entrega Marcada: ❌ Sim / ✅ Não
- Endereço de Entrega Diferente: ❌ Sim / ✅ Não
```

---

## 📋 Resumo de Ações Necessárias

### Prioridade ALTA (Falta no Relatório)
1. ✅ Adicionar seção de **Análise Semântica de CNAE** no Excel
2. ✅ Adicionar **detalhes da idade do domínio** (data, dias, limite)
3. ✅ Adicionar seção de **Outras Sinalizações de Risco**

### Prioridade MÉDIA (Falta Implementar)
4. ⚠️ Implementar **detecção de typosquatting** (algoritmo de similaridade)
5. ⚠️ Adicionar flag de typosquatting no banco de dados
6. ⚠️ Incluir detecção de typosquatting no relatório

---

## 🎯 Estrutura Sugerida do Relatório Completo

```
1. DADOS DA EMPRESA
   - CNPJ, Razão Social, Nome Fantasia, Data de Abertura
   - Email Cadastrado, Email CNPJA

2. ENDEREÇO
   - Endereço Completo, Coordenadas, Place ID

3. ATIVIDADES CNAE
   - CNAE Principal e Secundários (código + descrição)
   
3.5. ANÁLISE SEMÂNTICA DE CNAE (IA) ⬅️ ADICIONAR
   - Compatível: Sim/Não
   - Score: X/100
   - Análise detalhada
   - Observações

4. ANÁLISE DE EMAIL E DOMÍNIO
   - Email Cadastrado vs CNPJA
   - Comparação de Domínios
   - Data de Criação do Domínio ⬅️ ADICIONAR DETALHES
   - Idade do Domínio (dias) ⬅️ ADICIONAR
   - Limite Configurado ⬅️ ADICIONAR
   - Sinalizações de Risco (Email)
   - Detecção de Typosquatting ⬅️ ADICIONAR (quando implementado)

4.5. OUTRAS SINALIZAÇÕES DE RISCO ⬅️ ADICIONAR
   - Telefone Suspeito
   - Pressa em Aprovação
   - Entrega Marcada
   - Endereço de Entrega Diferente

5. RESULTADO DA ANÁLISE DE RISCO
   - Risco Final, Score, Tipo Local Esperado

6. ANÁLISE VISUAL (GEMINI VISION)
   - Zona Aparente, Tipo de Via, etc.

7. FLAGS DE RISCO
   - Lista de flags identificadas

8. ANÁLISE DETALHADA
   - Texto completo da análise
```

