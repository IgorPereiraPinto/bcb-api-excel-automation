# Como Agendar Execução Diária

## Objetivo

Configurar o script para rodar **automaticamente todos os dias úteis**, antes do horário da reunião com a holding. O Excel será atualizado sem intervenção manual.

---

## Windows — Agendador de Tarefas

### Passo a Passo

1. **Abra** o Agendador de Tarefas (`taskschd.msc` no Executar)

2. **Clique** em "Criar Tarefa" (não "Criar Tarefa Básica" — a versão completa dá mais controle)

3. **Aba Geral:**
   - Nome: `BCB Indicadores - Atualização Diária`
   - Marque: "Executar estando o usuário conectado ou não"
   - Marque: "Executar com privilégios mais altos"

4. **Aba Disparadores → Novo:**
   - Iniciar a tarefa: "Diariamente"
   - Hora: `07:00:00` (ou 1h antes da reunião)
   - Recorrência: a cada 1 dia
   - *(Opcional)* Repetir a cada 1 hora por 3 horas → cobre se a API estiver fora no 1º horário

5. **Aba Ações → Nova:**
   - Ação: "Iniciar um programa"
   - Programa/script: caminho do Python
```
   # Se usa ambiente virtual (recomendado):
   C:\caminho\do\projeto\.venv\Scripts\python.exe

   # Se usa Python global:
   C:\Python310\python.exe
```

   - Adicionar argumentos:
```
   -m src.main --days-back 3
```

   - Iniciar em (pasta do projeto):
```
   C:\caminho\do\projeto\bcb-api-excel-automation
```

6. **Aba Condições:**
   - Desmarque "Iniciar a tarefa somente se o computador estiver ligado à rede elétrica" (para notebooks)

7. **Aba Configurações:**
   - Marque "Se a tarefa falhar, reiniciar a cada 5 minutos"
   - Número de tentativas: 3

### Verificar se Funcionou
```cmd
# Testar manualmente no prompt ANTES de agendar:
cd C:\caminho\do\projeto\bcb-api-excel-automation
.venv\Scripts\python.exe -m src.main --days-back 3

# Depois de agendar, verificar:
# 1. Abra o Agendador → clique na tarefa → "Último resultado": 0x0 = OK
# 2. Abra data/output/indicadores_bcb.xlsx → aba status → confira data/hora
# 3. Abra data/output/run.log → última linha deve ser [OK]
```

### Dica: Execução Sem Janela

Para rodar sem abrir a janela do prompt (execução silenciosa), use `pythonw.exe` em vez de `python.exe`:
```
C:\caminho\do\projeto\.venv\Scripts\pythonw.exe
```

---

## Linux / Mac — Cron

### Passo a Passo

1. **Abra** o crontab:
```bash
crontab -e
```

2. **Adicione** a linha (execução diária às 7h, de segunda a sexta):
```bash
# Atualização diária de indicadores BCB (seg-sex às 7h)
0 7 * * 1-5 cd /caminho/do/projeto/bcb-api-excel-automation && /caminho/do/projeto/.venv/bin/python -m src.main --days-back 3 >> /caminho/do/projeto/data/output/cron.log 2>&1
```

**Explicação do cron:**
```
┌───────────── minuto (0)
│ ┌─────────── hora (7)
│ │ ┌───────── dia do mês (qualquer)
│ │ │ ┌─────── mês (qualquer)
│ │ │ │ ┌───── dia da semana (1-5 = seg-sex)
│ │ │ │ │
0 7 * * 1-5  comando
```

3. **Salve e feche** (`:wq` no vim, `Ctrl+X` no nano)

### Verificar se Funcionou
```bash
# Testar manualmente antes de agendar:
cd /caminho/do/projeto/bcb-api-excel-automation
.venv/bin/python -m src.main --days-back 3

# Verificar agendamentos ativos:
crontab -l

# Verificar logs do cron:
tail -20 /caminho/do/projeto/data/output/cron.log
```

---

## Por Que `--days-back 3`?

| Cenário | `--days-back 1` | `--days-back 3` |
|---------|:---------------:|:---------------:|
| Segunda-feira (dados de sex) | ❌ Perde sexta | ✅ Pega sex, sáb, dom |
| Após feriado prolongado | ❌ Perde feriado | ✅ Cobre 3 dias |
| API fora do ar 1 dia | ❌ Perde o dia | ✅ Recupera no dia seguinte |
| Duplicidade | — | ✅ O script deduplica automaticamente |

**Regra prática:** use `--days-back 3` para execuções diárias. O custo de pedir dados "extras" é zero (a API retorna vazio se não há dado), e a deduplicação garante que não haverá registros duplicados.

---

## Cenário Ideal para a Holding
```
07:00  Script roda automaticamente (Task Scheduler / cron)
07:01  Excel atualizado em data/output/indicadores_bcb.xlsx
07:05  Analista abre o Excel, copia para o modelo da apresentação
09:00  Reunião com a holding — dados atualizados e auditáveis
```

Se quiser eliminar até o passo de "copiar para o modelo", a evolução natural é integrar com Power BI (importar o Excel como fonte) ou enviar por e-mail automaticamente via Python (`smtplib`).
