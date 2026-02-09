# bcb-api-excel-automation

Projeto em Python para coletar séries temporais da API SGS do Banco Central, transformar os dados e atualizar um Excel com histórico de indicadores. Inclui documentação e instruções de automação diária.

## Visão geral
- Coleta múltiplas séries configuradas em `config/series_config.yaml`.
- Padroniza colunas e evita duplicidades por data/série.
- Atualiza `data/output/indicadores_bcb.xlsx` com abas `dados`, `series` e `status`.
- Gera logs em `data/output/run.log`.

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração das séries
Edite `config/series_config.yaml` para definir as séries desejadas. Exemplo:
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

> Observação: códigos podem variar e os exemplos são apenas ilustrativos. Consulte o documento `docs/03_exemplos_series.md` para descobrir novos códigos.

## Execução manual
```bash
python -m src.main --days-back 10
python -m src.main --from 2024-01-01 --to 2024-12-31
```

## Automação diária
Consulte `docs/02_como_agendar.md` para instruções no Windows Task Scheduler e cron.

## Estrutura do projeto
```
config/
  series_config.yaml
src/
  main.py
  bcb_sgs_client.py
  transform.py
  excel_writer.py
  logging_config.py
  utils.py
data/
  output/
  raw/
```

## Logs e status
- Logs: `data/output/run.log`
- Status da última execução: aba `status` do Excel.

## Testes
```bash
pytest
```
