# Contratos na Base (chain id 8453)

| O quê | Endereço |
|---|---|
| Uniswap v3 NonfungiblePositionManager | 0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1 |
| Uniswap v3 Factory | 0x33128a8fC17869897dcE68Ed026d694621f6FDfD |
| Pool cbBTC/USDC 0,05% | 0xfBB6Eed8e7aa03B138556eeDaF5D271A5E1e43ef |
| USDC (nativo) | 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 |
| cbBTC | 0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf |

RPC público: https://mainnet.base.org

## Leituras úteis (view, sem custo)
- `NPM.positions(tokenId)` → token0, token1, fee, tickLower, tickUpper, liquidity, tokensOwed.
- `NPM.ownerOf(tokenId)` → dono do NFT.
- `NPM.collect((tokenId, owner, 2^128-1, 2^128-1))` via eth_call com `from=owner`
  → taxas não coletadas (simulação, não executa).
- `Pool.slot0()` → sqrtPriceX96 e tick atual.

Links: posição → https://app.uniswap.org/positions/v3/base/<ID> · explorer → https://basescan.org
Atenção: o endereço do cbBTC é igual em várias redes; confira sempre o ícone da Base.
