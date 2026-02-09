# Como funciona

1. **Configuração**: as séries são definidas em `config/series_config.yaml`.
2. **Coleta**: o script consulta a API SGS do Banco Central com intervalo de datas.
3. **Transformação**: datas são convertidas para `datetime` e colunas são padronizadas.
4. **Persistência**: `data/output/indicadores_bcb.xlsx` recebe novos registros sem duplicar datas/séries.
5. **Status**: a aba `status` registra data/hora, linhas novas e erro (se houver).

## Boas práticas
- Mantenha o YAML atualizado.
- Revise periodicamente a aba `status`.
- Acompanhe o log para diagnósticos rápidos.
