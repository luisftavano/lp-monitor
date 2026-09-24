# Runbooks

## Reposicionar (saiu da faixa)
1. Esperar ~6 h fora da faixa antes de mexer (o bot só manda o passo a passo depois
   de `WAIT_HOURS`). Se o preço voltar, não há nada a fazer.
2. Uniswap → posição → Remove liquidity 100% (já coleta as taxas).
3. Swap de ~metade do token que sobrou pelo outro (tokens com ícone da Base).
4. Nova posição **v3** 0,05%, faixa ±7,5% no preço atual (o alerta do bot já traz a faixa).
   O bot não lê v4.
5. Pegar o novo ID (número no fim da URL da posição).
6. Atualizar o monitor:
   `gh variable set POSITION_ID --body "<id>"`
   `gh variable set INITIAL_BASE --body "<cbBTC depositado>"`
   `gh variable set INITIAL_QUOTE --body "<USDC depositado>"`
   Use quantidades reais; em dúvida, derive com position_math.py a partir da liquidez.

## Reinvestir taxas (sem reposicionar)
Só vale com taxas ≥ ~US$ 1 (gas ~US$ 0,05 por ciclo).
Collect fees → Add liquidity na mesma posição → somar o adicionado em INITIAL_BASE/QUOTE.

## Mudar o código do bot
`git pull --rebase` → editar → `python3 -m unittest discover tests` → commit → push →
`gh workflow run "LP monitor" -f modo=teste`.
