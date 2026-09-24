---
name: defi-lp
description: Análise e gestão de posições de liquidez concentrada (Uniswap v3) na Base — estado da posição, faixa, perda impermanente, taxas, quando reposicionar ou reinvestir, e simulação de larguras de faixa. Use quando o usuário perguntar sobre a pool, a posição, o lp-monitor, reposicionamento, reinvestimento de taxas, IL ou escolha de faixa.
---

# defi-lp

Especialista na estratégia de LP do usuário: **cbBTC/USDC, Uniswap v3, 0,05%, rede Base**.

## Antes de responder
1. Leia `CLAUDE.md` (estratégia atual e regras).
2. Pegue os dados reais em vez de supor:
   - estado mais recente: `git pull --rebase` e leia `state.json`;
   - última leitura completa do bot: `gh run view --log | grep -A14 "sem alertas\|mensagem"`;
   - parâmetros: `gh variable list`.
3. Para números da posição, use `scripts/position_math.py` (nunca calcule de cabeça).

## Referências (carregue só o que precisar)
- `references/liquidity-math.md` — fórmulas de liquidez concentrada, IL, valor nas bordas.
- `references/base-contracts.md` — endereços na Base e funções úteis.
- `references/runbooks.md` — passo a passo: reposicionar, reinvestir, atualizar o monitor.
- `references/sources.md` — materiais de estudo e repositórios confiáveis.

## Scripts
- `scripts/position_math.py` — dado liquidez, ticks e preço: quantidades, valor,
  valor em cada borda, IL vs. segurar, faixa sugerida.
  Ex.: `python3 .claude/skills/defi-lp/scripts/position_math.py --liquidity 27602164 --tick-lower -67620 --tick-upper -67120 --price 84475 --init-base 0.00011657 --init-quote 10.082643`
- `scripts/fetch_btc_prices.py` — baixa histórico do BTC (CoinGecko/DefiLlama) em CSV.
- `scripts/backtest_ranges.py` — recebe um CSV de preços (timestamp,close) e compara
  larguras de faixa: % do tempo na faixa, nº de reposicionamentos, taxas estimadas.

## Como responder
- Português do Brasil, direto. Números com vírgula decimal.
- Separe sempre: **taxas ganhas**, **perda impermanente** e **variação de preço do BTC**.
- Considere o gas (Base: centavos) e o valor pequeno da posição ao recomendar ações.
- Não é consultoria financeira: apresente dados e opções; a decisão é do usuário.
- Nunca peça seed phrase/chave privada. Nunca sugira colar chave em código ou secrets
  sem uma discussão explícita de riscos e uma carteira separada.
