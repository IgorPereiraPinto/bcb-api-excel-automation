"""
Pacote principal do projeto BCB API Excel Automation.

Módulos:
    main.py            → Ponto de entrada (CLI)
    bcb_sgs_client.py  → Cliente HTTP da API SGS do Banco Central
    transform.py       → Padronização, conversão e deduplicação
    excel_writer.py    → Persistência incremental no Excel (3 abas)
    logging_config.py  → Configuração de logs (arquivo + console)
    utils.py           → Dataclasses, parsing de datas, leitura de YAML
"""
