---
name: revisao-semanal
description: Revisão semanal da estratégia de LP — como a posição foi na semana e se os parâmetros devem mudar. Use quando o usuário pedir "revisão semanal", "como foi a semana da pool" ou digitar /revisao-semanal.
---

# Revisão semanal da pool

1. Delegue ao agente `pool-analyst`: situação atual, taxas da semana, IL, rendimento real
   anualizado e resultado vs. segurar.
2. Delegue ao agente `strategy-optimizer`: backtest dos últimos 90 dias com o APR atual,
   comparando a faixa atual com alternativas.
3. Junte num relatório curto em `reports/AAAA-MM-DD-semanal.md` com:
   - resultado da semana (taxas, IL, vs. segurar);
   - a faixa atual ainda é a melhor? (sim/não + números);
   - ações sugeridas para a próxima semana, com comandos prontos para o usuário rodar.
4. Termine perguntando se o usuário quer aplicar alguma mudança. Não aplique nada sozinho.
