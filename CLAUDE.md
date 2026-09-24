# lp-monitor — memória do projeto

## O que é
Bot que monitora uma posição de liquidez concentrada **Uniswap v3 na Base** (par cbBTC/USDC,
pool 0,05%) e manda alertas no WhatsApp (CallMeBot; Telegram opcional). Só LÊ a blockchain:
não tem chave privada e não executa transações.

## Como roda
- GitHub Actions (`.github/workflows/monitor.yml`), a cada 10 min, repositório **público**.
- `monitor.py` → lê a posição on-chain (RPC público da Base), calcula valor/taxas/IL,
  decide alertas, grava `state.json` e o workflow commita esse arquivo.
- Modo teste: `gh workflow run "LP monitor" -f modo=teste`.

## Configuração (nunca escrever valores sensíveis aqui — o repo é público)
- Secrets: `WHATSAPP_PHONE`, `CALLMEBOT_APIKEY` (opcional: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`).
- Variables: `POSITION_ID`, `INITIAL_BASE`, `INITIAL_QUOTE`, `EDGE_PCT`, `SUMMARY_HOUR`,
  `FEES_ALERT_USD`, `WAIT_HOURS`, `NEW_RANGE_PCT`. Ver valores atuais com `gh variable list`.
- `INITIAL_BASE/QUOTE` = quantidades REALMENTE depositadas (derivar da liquidez on-chain
  se houver dúvida — a tela da Uniswap mostra valores antes do slippage).

## Estratégia atual (decisões do dono)
- Faixa ±7,5% em torno do preço (era ±2,5% até 24/09/2026; backtest de 90 dias mostrou que
  ±2,5% com reposicionamento imediato reposicionava ~2x/semana e ficava entre as piores).
- Saiu da faixa: **esperar ~6 h** (`WAIT_HOURS`) antes de reposicionar; se voltar, nada a fazer.
- Reinvestir taxas junto com o reposicionamento.
- Refazer a análise com 2–4 semanas de taxas reais (se vierem bem acima da estimativa,
  faixas mais estreitas esperando 24 h voltam a ser candidatas).
- Rebalanceamento automático: **não** por enquanto (decidir com dados de algumas semanas).

## Regras de trabalho
- Sempre `git pull --rebase` antes de `git push` (o bot commita `state.json` sozinho).
- Depois de mudar `monitor.py`: rodar `python3 -m unittest discover tests` e testar o modo teste.
- Não adicionar nada que assine transações ou guarde chave privada sem pedido explícito.
- Responder em português do Brasil, informal e direto.
- Para análise de pool/posição, usar a skill `defi-lp`.

## Agentes e rotina
- `pool-analyst` — situação da posição e ação recomendada agora (só leitura).
- `strategy-optimizer` — backtest com dados reais e recomendação de parâmetros.
- `monitor-dev` — mudanças no código do bot (com testes).
- `risk-reviewer` — obrigatório antes de qualquer coisa que envolva chaves ou transações.
- `/revisao-semanal` — rotina de toda semana (análise + otimização + relatório em `reports/`).
- Skills pessoais de apoio (em ~/.claude/skills, de agiprolabs, MIT): lp-math,
  impermanent-loss, yield-analysis, volatility-modeling, walk-forward-validation,
  risk-management, defillama-api, coingecko-api.
- Objetivo: resultado líquido acima de "só segurar". Se os dados mostrarem o contrário,
  dizer claramente e propor ajuste ou saída.
