# Catálogo de Séries SGS — Banco Central do Brasil

## Como Usar Este Catálogo

1. Encontre a série que precisa na tabela abaixo
2. Copie o **código SGS**
3. Adicione em `config/series_config.yaml`
4. Execute o script — os dados da nova série serão coletados automaticamente

---

## Séries Mais Utilizadas

### Câmbio

| Código | Indicador | Unidade | Periodicidade | Uso típico |
|:------:|-----------|---------|:-------------:|------------|
| **1** | Dólar comercial (compra) | R$/US$ | Diária | Importação, pricing, hedge |
| **10813** | Dólar comercial (venda) | R$/US$ | Diária | Exportação, recebíveis em USD |
| **21619** | Euro (compra) | R$/EUR | Diária | Fornecedores europeus |
| **21620** | Euro (venda) | R$/EUR | Diária | Receita em EUR |
| **21623** | Libra esterlina (compra) | R$/GBP | Diária | Operações com Reino Unido |
| **21621** | Iene japonês (compra) | R$/100 JPY | Diária | Operações com Japão |
| **21625** | Franco suíço (compra) | R$/CHF | Diária | Investimentos, seguros |

### Juros

| Código | Indicador | Unidade | Periodicidade | Uso típico |
|:------:|-----------|---------|:-------------:|------------|
| **432** | Selic (meta a.a.) | % a.a. | Diária | Custo de oportunidade, valuation |
| **4389** | CDI (a.a.) | % a.a. | Diária | Benchmark de investimentos |
| **226** | TR (mensal) | % a.m. | Mensal | Financiamentos imobiliários |
| **253** | TJLP | % a.a. | Trimestral | Financiamentos BNDES |

### Inflação

| Código | Indicador | Unidade | Periodicidade | Uso típico |
|:------:|-----------|---------|:-------------:|------------|
| **433** | IPCA (variação mensal) | % a.m. | Mensal | Reajustes contratuais, meta de inflação |
| **10764** | IPCA acumulado 12 meses | % a.a. | Mensal | Visão anualizada da inflação |
| **189** | IGP-M (variação mensal) | % a.m. | Mensal | Reajuste de aluguéis |
| **190** | IGP-DI (variação mensal) | % a.m. | Mensal | Contratos industriais |
| **7478** | IPC-Fipe (variação mensal) | % a.m. | Mensal | Referência em São Paulo |

### Atividade Econômica

| Código | Indicador | Unidade | Periodicidade | Uso típico |
|:------:|-----------|---------|:-------------:|------------|
| **24363** | IBC-Br (proxy mensal do PIB) | Índice | Mensal | Cenário macroeconômico |
| **24369** | Taxa de desemprego (PNAD) | % | Trimestral | Mercado de trabalho |
| **1344** | Produção industrial | Índice | Mensal | Setor industrial |

### Crédito

| Código | Indicador | Unidade | Periodicidade | Uso típico |
|:------:|-----------|---------|:-------------:|------------|
| **20786** | Spread bancário (PJ) | p.p. | Mensal | Custo de crédito empresarial |
| **20714** | Inadimplência PJ | % | Mensal | Risco de crédito no mercado |

---

## Como Descobrir Novos Códigos

### Método 1 — Portal SGS (oficial)

1. Acesse: [https://www3.bcb.gov.br/sgspub](https://www3.bcb.gov.br/sgspub)
2. Clique em "Consultar séries"
3. Busque por tema (Câmbio, Juros, Inflação) ou palavra-chave
4. Abra a série desejada → o **código** aparece na URL e no cabeçalho
5. Copie e adicione ao YAML

### Método 2 — API direta (para testar antes de configurar)

Teste no navegador antes de adicionar ao YAML:
```
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{CODIGO}/dados?formato=json&dataInicial=01/01/2025&dataFinal=31/01/2025
```

Exemplos:
```
# Dólar (código 1):
https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json&dataInicial=01/01/2025&dataFinal=31/01/2025

# Selic (código 432):
https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial=01/01/2025&dataFinal=31/01/2025
```

Se retornar JSON com dados → código válido.
Se retornar erro 404 → código inválido ou descontinuado.

---

## Cuidados Importantes

| Situação | O que acontece | O que fazer |
|----------|---------------|-------------|
| Código descontinuado | API retorna erro 404 | Consultar o SGS para encontrar o código substituto |
| Série com periodicidade diferente | Série mensal misturada com diárias | Tratar no Excel ou separar por periodicidade no YAML |
| Valores retroativos revisados | BCB pode revisar dados antigos (ex: IPCA) | O script sobrescreve com o valor mais recente |
| API fora do ar | Timeout na requisição | O script faz retry automático e registra no log |

---

## Exemplo: Adicionando o IPCA ao YAML
```yaml
# Adicione este bloco em config/series_config.yaml:
  - nome: "IPCA (variação mensal)"
    codigo: 433
    unidade: "% a.m."
    categoria: "inflacao"
    uso: "Reajuste de contratos, correção de preços"
```

Depois execute:
```bash
python -m src.main --days-back 365    # coleta o último ano de IPCA
```

O Excel será atualizado automaticamente com o histórico do IPCA.
