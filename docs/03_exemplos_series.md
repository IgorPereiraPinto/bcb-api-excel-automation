# Exemplos de séries e como descobrir códigos

Os códigos abaixo são apenas **exemplos**. Use o SGS para confirmar se continuam válidos.

## Exemplos no arquivo de configuração
- Dólar comercial (compra): `1`
- Euro (compra): `21619`
- Selic (a.a.): `432`

## Como descobrir novos códigos
1. Acesse o SGS do Banco Central: https://www3.bcb.gov.br/sgspub/
2. Use a busca por tema ou palavra-chave.
3. Abra a série desejada e copie o código SGS.
4. Atualize `config/series_config.yaml`.

## Observações
- Caso um código retorne erro na API, ele pode estar descontinuado.
- Sempre valide a unidade e a periodicidade no próprio SGS.
