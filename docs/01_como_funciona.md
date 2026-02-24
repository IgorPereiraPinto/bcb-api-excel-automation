# Como Funciona — Arquitetura e Fluxo de Dados

## Visão Geral
```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  YAML Config    │────▶│  API SGS (BCB)   │────▶│  Transform       │────▶│  Excel Output   │
│                 │     │                  │     │                  │     │                 │
│ series_config   │     │ GET /dados/serie │     │ Padroniza datas  │     │ 3 abas:         │
│ .yaml           │     │ JSON response    │     │ Deduplica        │     │ dados / series  │
│                 │     │                  │     │ Valida tipos     │     │ / status        │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └─────────────────┘
        │                                                                        │
        │                                                                        ▼
        │                                                                ┌─────────────────┐
        └───────────────────────────────────────────────────────────────▶│  Log (run.log)  │
                                                                         └─────────────────┘
```

## Passo a Passo Detalhado

### 1. Configuração (`config/series_config.yaml`)

O YAML define **quais séries** coletar. Cada série tem:

| Campo | Obrigatório | Exemplo | Descrição |
|-------|:-----------:|---------|-----------|
| `nome` | ✅ | "Dólar comercial (compra)" | Nome legível do indicador |
| `codigo` | ✅ | 1 | Código SGS no Banco Central |
| `unidade` | ✅ | "R$/US$" | Unidade de medida |
| `categoria` | Não | "cambio" | Agrupamento (câmbio, juros, inflação) |
| `uso` | Não | "Contratos de importação" | Contexto de negócio |

Para adicionar uma nova série, basta incluir um bloco no YAML. Nenhuma alteração de código é necessária.

### 2. Coleta (`src/bcb_sgs_client.py`)

O script consulta a API SGS do Banco Central para cada série configurada:
```
GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={dd/MM/yyyy}&dataFinal={dd/MM/yyyy}
```

**Tratamento de erros:**

| Cenário | Comportamento |
|---------|--------------|
| API fora do ar (timeout) | Registra erro no log, tenta novamente (até 2 retentativas), segue para a próxima série |
| Código inválido | Registra erro, não interrompe as demais séries |
| Sem dados no período | Registra aviso, não gera erro |
| Resposta malformada | Registra erro com o conteúdo recebido para diagnóstico |

**Por que não trava tudo por causa de uma série?** Se o Dólar falhou mas o Euro e a Selic funcionaram, o relatório da holding sai com 2 de 3 indicadores — melhor do que nenhum.

### 3. Transformação (`src/transform.py`)

Os dados brutos da API passam por 3 tratamentos:

| Etapa | O que faz | Por quê |
|-------|----------|---------|
| **Conversão de datas** | `dd/MM/yyyy` (formato BCB) → `datetime` (formato Python/Excel) | Padronização para filtros e ordenação |
| **Normalização decimal** | Vírgula → ponto em valores numéricos | API pode retornar "5,32" como texto |
| **Deduplicação** | Remove registros com mesma data + série | Se rodar duas vezes no mesmo dia, não duplica |

### 4. Persistência (`src/excel_writer.py`)

O Excel é atualizado de forma **incremental** (append), não substituído:
```
Execução 1 (segunda):   Excel tem dados de seg
Execução 2 (terça):     Lê o Excel existente + dados novos de ter → salva tudo junto
Execução 3 (quarta):    Lê o Excel existente + dados novos de qua → salva tudo junto
```

**Se o Excel não existir** (primeira execução), cria do zero com as 3 abas.

**Se já existir**, lê os dados existentes, faz merge com os novos e salva — sem perder histórico.

### 5. Status e Logs

Dois mecanismos de monitoramento:

| Mecanismo | Onde fica | Para quem |
|-----------|----------|-----------|
| **Aba `status`** no Excel | Dentro do próprio arquivo de saída | Quem abre a planilha vê imediatamente se a última execução foi OK |
| **`run.log`** | `data/output/run.log` | Analista/TI — histórico completo com timestamps e erros detalhados |

---

## Diagrama de Módulos
```
src/
├── main.py              ← Ponto de entrada (CLI): recebe --days-back ou --from/--to
│   ├── chama → bcb_sgs_client.py    (coleta)
│   ├── chama → transform.py         (tratamento)
│   ├── chama → excel_writer.py      (persistência)
│   └── chama → logging_config.py    (logs)
│
├── bcb_sgs_client.py    ← Faz as requisições HTTP à API SGS
├── transform.py         ← Padroniza, converte e deduplica
├── excel_writer.py      ← Lê/escreve o Excel com 3 abas
├── logging_config.py    ← Configura formato e destino dos logs
└── utils.py             ← Funções auxiliares (parsing de datas, leitura de YAML)
```

---

## Boas Práticas de Operação

| Prática | Frequência | Por quê |
|---------|-----------|---------|
| Revisar a aba `status` | Semanal | Verificar se houve falha silenciosa |
| Conferir `run.log` | Quando houver suspeita de erro | Diagnóstico detalhado com timestamp |
| Atualizar `series_config.yaml` | Quando necessário | Adicionar ou remover séries sem mexer em código |
| Verificar códigos SGS | Semestral | Séries podem ser descontinuadas pelo Banco Central |
| Fazer backup do Excel | Mensal | Proteger o histórico acumulado |
