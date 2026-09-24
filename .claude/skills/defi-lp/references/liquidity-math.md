# Matemática de liquidez concentrada (Uniswap v3)

Notação: preço P = quantidade de token1 por token0 (unidades "raw").
Na pool cbBTC/USDC da Base: token0 = USDC (6 decimais), token1 = cbBTC (8 decimais).
Preço humano do BTC em USDC = 1 / (1.0001^tick × 10^(6-8)).

## Tick ↔ preço
- P(tick) = 1.0001^tick   (raw, token1/token0)
- sqrtPriceX96 = sqrt(P) × 2^96  (vem de `slot0()` da pool)

## Quantidades a partir da liquidez L (raw)
Com sa = sqrt(P(tickLower)), sb = sqrt(P(tickUpper)), sp = sqrt(P atual):
- sp ≤ sa: amount0 = L(sb−sa)/(sa·sb), amount1 = 0
- sp ≥ sb: amount0 = 0, amount1 = L(sb−sa)
- entre:   amount0 = L(sb−sp)/(sp·sb), amount1 = L(sp−sa)
Divida por 10^decimais para unidades humanas.

## Intuição (par BTC/USDC)
- BTC sobe → pool vende BTC por USDC; acima da faixa = 100% USDC, para de render.
- BTC cai → pool compra BTC com USDC; abaixo da faixa = 100% BTC, para de render.
- Fora por cima: valor fica parado (perde a alta). Fora por baixo: cai 1:1 com o BTC.

## Perda impermanente (IL)
IL = valor da posição (sem taxas) − valor de só segurar as quantidades iniciais.
Resultado real = valor da posição + taxas − valor de segurar.
Referência v2 (faixa infinita): 1,5x → ~2%, 2x → ~5,7%, 3x → ~13,4%.
Faixa estreita amplifica a IL dentro da faixa, mas ela fica limitada nas bordas.

## Eficiência de capital
Faixa [Pa, Pb] rende ~1/(1 − (Pa/Pb)^(1/4)) vezes uma posição full-range com o mesmo
capital, enquanto estiver na faixa. ±2,5% ≈ 80x — mas o APR "da pool" já reflete que a
maioria dos LPs também concentra, então compare com o APR da pool, não com full range.

## Fonte
Atis Elsts, "Liquidity Math in Uniswap v3" + repositório atiselsts/uniswap-v3-liquidity-math.
