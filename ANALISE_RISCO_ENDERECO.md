# Análise de Risco de Endereço com Gemini Vision

## 📋 Visão Geral

Sistema completo de análise de risco de endereço usando Google Gemini Vision para analisar imagens de fachadas e verificar compatibilidade com CNAEs da empresa.

## 🏗️ Arquitetura

### Componentes Principais

1. **`address_risk_service.py`**
   - Serviço principal de análise de risco
   - Integração com Gemini Vision API
   - Análise de imagens de endereços
   - Aplicação de regras de compatibilidade

2. **`cnae_compatibility_rules.py`**
   - Mapeamento de CNAEs para tipos de local esperados
   - Regras de risco baseadas em análise visual
   - Sistema de scoring de risco (0-100)

3. **`database.py`** (atualizado)
   - Tabela `analises_risco_endereco`: armazena análises completas
   - Tabela `cnae_tipo_local`: mapeamento CNAE → tipo local
   - Funções para salvar/buscar análises

## 🔄 Fluxo de Dados

```
1. Usuário consulta CNPJ → API CNPJA
2. Processa endereço → Google Maps (geocoding + imagens)
3. Analisa imagem → Gemini Vision
4. Aplica regras → Compatibilidade CNAE
5. Gera score de risco → Banco de dados
6. Exibe resultados → Interface Streamlit
```

## 📊 Schema de Análise

### Análise Visual (Gemini)
```json
{
  "zona_aparente": "COMERCIAL | RESIDENCIAL | INDUSTRIAL | RURAL | INDEFINIDO",
  "tipo_via": "ASFALTADA | TERRA | NAO_VISIVEL",
  "presenca_placas_comerciais": true/false,
  "presenca_vitrines_ou_lojas": true/false,
  "presenca_casas_residenciais": true/false,
  "compatibilidade_cnae": "ALTA | MEDIA | BAIXA | DESCONHECIDA",
  "motivos_incompatibilidade": ["motivo1", "motivo2"],
  "sugestao_nivel_risco": "ALTO | MEDIO | BAIXO",
  "analise_detalhada": "texto detalhado"
}
```

### Resultado Final
```json
{
  "analise_visual": {...},
  "tipo_local_esperado": "COMERCIAL | ESCRITORIO | INDUSTRIAL | ECOMMERCE_DOMICILIAR_OK",
  "risco_final": "ALTO | MEDIO | BAIXO",
  "flags_risco": ["flag1", "flag2"],
  "score_risco": 0-100
}
```

## 🎯 Tipos de Local Esperados

### COMERCIAL
- Comércio varejista (4711, 4719, 4721, etc.)
- Espera: lojas, vitrines, placas comerciais, movimento

### ESCRITORIO
- Serviços, tecnologia, consultorias (6201, 6204, 7020, etc.)
- Espera: prédios comerciais, escritórios, pode ser home office

### INDUSTRIAL
- Indústria, logística, construção (1011, 2511, 4211, etc.)
- Espera: galpões, zonas industriais, áreas afastadas

### ECOMMERCE_DOMICILIAR_OK
- E-commerce, serviços que podem funcionar em casa (4791, etc.)
- Aceita: zona residencial (home office)

## 🚨 Regras de Risco

### ALTO RISCO (Score 60+)
- CNAE comercial/industrial em zona residencial
- Rua de terra + CNAE comercial + zona residencial
- Ausência de placas comerciais em CNAE comercial
- Compatibilidade baixa reportada pelo Gemini
- Indústria em zona não industrial

### MÉDIO RISCO (Score 30-59)
- Escritório em zona residencial (suspeito)
- Compatibilidade média
- Zona indefinida

### BAIXO RISCO (Score 0-29)
- Compatibilidade alta
- CNAE compatível com home office em residencial

## 📝 Flags de Risco

- `INCOMPATIBILIDADE_ZONA_COMERCIAL_RESIDENCIAL`
- `RUA_TERRA_COM_CNae_COMERCIAL`
- `AUSENCIA_SINAIS_COMERCIAIS`
- `AREA_RESIDENCIAL_SEM_COMERCIO`
- `COMPATIBILIDADE_BAIXA_IA`
- `INDUSTRIA_EM_ZONA_NAO_INDUSTRIAL`
- `ESCRITORIO_EM_RESIDENCIAL_SUSPEITO`
- `ESCRITORIO_EM_RESIDENCIAL_POSSIVEL_HOME_OFFICE`
- `COMPATIBILIDADE_MEDIA_IA`
- `ZONA_INDEFINIDA`
- `COMPATIVEL_HOME_OFFICE`
- `COMPATIBILIDADE_ALTA_IA`

## 🔧 Uso

### Via Interface Streamlit
1. Consulte um CNPJ
2. Processe o endereço (botão "🗺️ Processar Endereço")
3. Clique em "🤖 Analisar Risco"
4. Visualize os resultados na interface

### Via Código Python
```python
from address_risk_service import analisar_endereco_completo

resultado = analisar_endereco_completo(
    cnpj="12345678000190",
    image_bytes=imagem_bytes,  # opcional, busca do banco se não fornecido
    cnaes=[  # opcional, busca do CNPJA se não fornecido
        {"codigo": "6201-5/01", "descricao": "Desenvolvimento de programas"}
    ],
    razao_social="Empresa Exemplo",
    nome_fantasia="Exemplo"
)

print(f"Risco: {resultado['risco_final']}")
print(f"Score: {resultado['score_risco']}/100")
```

## 📦 Dependências

Todas as dependências já estão no `requirements.txt`:
- `requests` - para chamadas à API Gemini
- `google-generativeai` - (opcional, não usado atualmente, usando REST direto)

## ⚙️ Configuração

Configure no arquivo `.env`:
```
GEMINI_API_KEY=sua_chave_aqui
# ou
VERTEX_AI_API_KEY=sua_chave_aqui
```

## 🗄️ Banco de Dados

### Tabela `analises_risco_endereco`
Armazena análises completas de risco por CNPJ.

### Tabela `cnae_tipo_local`
Permite customizar mapeamento de CNAEs para tipos de local esperados.

## 🔍 Exemplo de Uso

Veja `exemplo_analise_risco.py` para um exemplo completo de uso.

## ⚠️ Observações Importantes

1. **Ferramenta de Apoio**: A análise é uma ferramenta de apoio à decisão, não prova definitiva.

2. **Combinação de Evidências**: Combine com:
   - Idade do domínio
   - Dados cadastrais oficiais
   - Histórico de pagamentos
   - Outros bureaus

3. **Revisão Manual**: Casos de risco alto devem ser revisados manualmente.

4. **Limitações**:
   - Depende da qualidade da imagem disponível
   - Pode não detectar todos os casos suspeitos
   - Análise visual não substitui verificação física

## 🚀 Próximos Passos

- [ ] Adicionar mais CNAEs ao mapeamento
- [ ] Melhorar regras de risco baseadas em feedback
- [ ] Adicionar histórico de análises
- [ ] Exportar relatórios de risco
- [ ] Integrar com sistema de scoring geral

