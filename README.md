# Automação de Indicadores Macro — API Banco Central → Excel

## Pergunta de Negócio

> "Quanto está o dólar e o euro hoje? E a tendência da última semana? Preciso disso atualizado no relatório da holding até as 9h."

Toda empresa com exposição cambial (importação, exportação, contratos internacionais) precisa acompanhar cotações diariamente. Na prática, alguém da equipe abre o site do Banco Central, copia os valores e cola numa planilha. **Todos os dias. Manualmente.**

Este projeto elimina esse retrabalho: um script Python consulta a API oficial do Banco Central (SGS), coleta as cotações configuradas e atualiza automaticamente um Excel pronto para apresentação à holding.

---

## O Que Este Projeto Faz
```
API SGS (Banco Central)         Python (requests + pandas)         Excel (.xlsx)
        │                               │                               │
        ▼                               ▼                               ▼
  Cotações oficiais:            Coleta, padroniza,              Planilha atualizada
  Dólar, Euro, Selic,          trata duplicidades,             com histórico, status
  IPCA, CDI, etc.              e registra logs                 e metadados das séries
```

**Em uma linha:** configura as séries desejadas no YAML → agenda a execução diária → o Excel se atualiza sozinho.

---

## Por Que Automatizar (e Não Só "Consultar")

| Cenário | Manual | Automatizado |
|---------|--------|-------------|
| Tempo diário | 15-20 min (abrir site, copiar, colar, formatar) | 0 min (roda sozinho às 7h) |
| Risco de erro | Colar na célula errada, esquecer um dia, trocar vírgula por ponto | Zero — dados vêm da API oficial |
| Histórico | Depende de alguém lembrar de salvar | Acumula automaticamente sem duplicidade |
| Auditoria | "De onde veio esse número?" — ninguém sabe | Log com data, hora, código da série e status |
| Escalabilidade | Adicionar IPCA? Mais 10 min/dia | Adicionar 1 linha no YAML |

---

## Séries Configuradas (Padrão)

| Indicador | Código SGS | Unidade | Uso na holding |
|-----------|-----------|---------|---------------|
| **Dólar comercial (compra)** | 1 | R$/US$ | Contratos de importação, pricing internacional |
| **Euro (compra)** | 21619 | R$/EUR | Operações com fornecedores europeus |
| **Selic (a.a.)** | 432 | % a.a. | Custo de oportunidade, projeções financeiras |

> **Para adicionar mais séries** (IPCA, CDI, IGP-M, etc.), basta editar `config/series_config.yaml`. Consulte `docs/03_exemplos_series.md` para o catálogo completo de códigos.

### Configuração (`config/series_config.yaml`)
```yaml
series:
  - nome: "Dólar comercial (compra)"
    codigo: 1
    unidade: "R$/US$"
  - nome: "Euro (compra)"
    codigo: 21619
    unidade: "R$/EUR"
  - nome: "Selic (a.a.)"
    codigo: 432
    unidade: "% a.a."
```

Para incluir uma nova série: adicione um bloco com `nome`, `codigo` e `unidade`. O script faz o resto.

---

## Output: O Que o Excel Contém

O arquivo `data/output/indicadores_bcb.xlsx` tem 3 abas:

| Aba | Conteúdo | Para quem |
|-----|----------|-----------|
| **dados** | Histórico completo: data, indicador, valor, unidade | Analistas — base para gráficos e cálculos |
| **series** | Catálogo das séries configuradas com código SGS e descrição | Documentação — saber exatamente o que está sendo coletado |
| **status** | Log da última execução: data/hora, séries coletadas, erros | Auditoria — "rodou hoje? deu erro em alguma série?" |

---

## Instalação
```bash
# 1. Clonar o repositório
git clone https://github.com/IgorPereiraPinto/bcb-api-excel-automation.git
cd bcb-api-excel-automation

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Instalar dependências
pip install -r requirements.txt
```

---

## Execução

### Manual (sob demanda)
```bash
# Coletar os últimos 10 dias
python -m src.main --days-back 10

# Coletar um período específico
python -m src.main --from 2024-01-01 --to 2024-12-31

# Coletar apenas hoje (padrão para uso diário)
python -m src.main --days-back 1
```

### Automação Diária (o objetivo principal)

O script foi feito para rodar automaticamente todos os dias, antes do horário da reunião. Instruções completas em `docs/02_como_agendar.md`.

**Resumo rápido:**

| Sistema | Ferramenta | Comando |
|---------|-----------|---------|
| **Windows** | Agendador de Tarefas | Criar tarefa → Disparador: diário às 7h → Ação: `python -m src.main --days-back 3` |
| **Linux/Mac** | cron | `0 7 * * 1-5 cd /caminho/projeto && .venv/bin/python -m src.main --days-back 3` |

> **Por que `--days-back 3`?** Para cobrir fins de semana e feriados em que a API não publica dados. O script trata duplicidades automaticamente — se o dado do dia já existe, não duplica.

---

## Estrutura do Projeto
```
bcb-api-excel-automation/
│
├── config/
│   └── series_config.yaml       ← séries a coletar (editável)
│
├── src/
│   ├── main.py                  ← ponto de entrada (CLI)
│   ├── bcb_sgs_client.py        ← cliente da API SGS do Banco Central
│   ├── transform.py             ← padronização e deduplicação
│   ├── excel_writer.py          ← escrita do Excel com 3 abas
│   ├── logging_config.py        ← configuração de logs
│   └── utils.py                 ← funções auxiliares
│
├── data/
│   ├── output/                  ← Excel final + logs (gerados automaticamente)
│   └── raw/                     ← dados brutos da API (cache)
│
├── docs/
│   ├── 01_como_funciona.md      ← arquitetura e fluxo de dados
│   ├── 02_como_agendar.md       ← automação (Task Scheduler / cron)
│   └── 03_exemplos_series.md    ← catálogo de séries SGS disponíveis
│
├── tests/                       ← testes automatizados
├── requirements.txt
└── README.md
```

---

## Fluxo Técnico
```
1. Lê config/series_config.yaml
   → Lista de séries com código, nome e unidade

2. Para cada série, chama a API SGS:
   GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
   → Retorna JSON com data + valor

3. Padroniza os dados (transform.py):
   → Converte datas para datetime
   → Normaliza separador decimal
   → Remove duplicidades por data/série

4. Atualiza o Excel (excel_writer.py):
   → Lê o Excel existente (se houver)
   → Faz append dos dados novos sem duplicar
   → Salva com 3 abas padronizadas

5. Registra log (logging_config.py):
   → Sucesso: "Série 1 (Dólar): 47 registros coletados"
   → Erro: "Série 432 (Selic): timeout após 30s — será tentada novamente amanhã"
```

---

## Logs e Monitoramento

- **Log de execução:** `data/output/run.log` — histórico de todas as execuções
- **Status da última execução:** aba `status` do Excel — visível para quem abre a planilha
- **Tratamento de erros:** se a API estiver fora do ar, o script registra o erro e continua com as demais séries (não trava tudo por causa de uma série)

---

## Testes
```bash
pytest
```

Os testes cobrem: parsing de resposta da API, tratamento de duplicidades, escrita do Excel e validação do YAML.

---

## Contexto de Portfólio

Este projeto demonstra:

| Competência | Como aparece |
|------------|-------------|
| **Integração com APIs REST** | Consumo da API SGS do Banco Central com tratamento de erros |
| **Automação de rotinas** | Script agendável que elimina retrabalho manual diário |
| **Tratamento de dados** | Deduplicação, padronização de tipos, merge incremental |
| **Entrega para o negócio** | Excel pronto para apresentação com histórico e auditoria |
| **Boas práticas** | YAML configurável, logs, testes, documentação, separação de responsabilidades |

> O valor deste projeto não é técnico — é operacional. Ele transforma 15 minutos diários de trabalho manual repetitivo em zero, com maior confiabilidade e rastreabilidade completa.

---

## Autor

**Igor Pereira Pinto** — Senior Data/BI Analyst

- [LinkedIn](https://www.linkedin.com/in/igorpereirapinto/)
- [Portfólio](https://sites.google.com/view/portfolio-de-projetos/home)
- [GitHub](https://github.com/IgorPereiraPinto)
