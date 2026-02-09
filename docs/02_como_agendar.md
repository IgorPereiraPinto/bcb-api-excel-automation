# Como agendar execução diária

## Windows Task Scheduler
1. Abra o **Agendador de Tarefas**.
2. Clique em **Criar Tarefa Básica**.
3. Defina o gatilho como **Diariamente**.
4. Em **Ação**, selecione **Iniciar um programa**.
5. No campo **Programa/script**, use o caminho do Python:
   - `C:\Python310\python.exe` ou o Python do seu ambiente virtual.
6. Em **Adicionar argumentos**, use:
   - `-m src.main --days-back 10`
   - `-m src.main --from 2024-01-01 --to 2024-12-31`
7. Em **Iniciar em**, informe o caminho do projeto.

> Dica: para rodar sem janela, use `pythonw.exe`.

## Cron (Linux/Mac)
1. Abra o crontab:
   ```bash
   crontab -e
   ```
2. Adicione uma linha (exemplo diário às 8h):
   ```bash
   0 8 * * * /usr/bin/python3 -m src.main --days-back 10
   ```
3. Salve e feche.

## Comandos de exemplo
```bash
python -m src.main --days-back 10
python -m src.main --from 2024-01-01 --to 2024-12-31
```
