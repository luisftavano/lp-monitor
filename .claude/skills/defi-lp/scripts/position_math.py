#!/usr/bin/env python3
"""
Calcula o estado de uma posição Uniswap v3 cbBTC/USDC (Base) a partir de dados on-chain.
Só matemática: não acessa rede. Pegue liquidity/ticks de NPM.positions(id) e o preço
de Pool.slot0() (ou passe o preço do BTC em USDC direto).

Ex.:
  python3 position_math.py --liquidity 27602164 --tick-lower -67620 --tick-upper -67120 \
      --price 84475 --init-base 0.00011657 --init-quote 10.082643
"""
import argparse
import math

DEC0, DEC1 = 6, 8          # token0 = USDC, token1 = cbBTC (pool da Base)
ADJ = 10 ** (DEC0 - DEC1)


def btc_price_from_tick(tick):
    return 1 / (1.0001 ** tick * ADJ)


def sqrt_raw_from_btc_price(p):
    return math.sqrt((1 / p) / ADJ)


def amounts(L, sp, tick_lower, tick_upper):
    """Retorna (btc, usdc) em unidades humanas."""
    sa, sb = math.sqrt(1.0001 ** tick_lower), math.sqrt(1.0001 ** tick_upper)
    if sp <= sa:
        a0, a1 = L * (sb - sa) / (sa * sb), 0.0
    elif sp >= sb:
        a0, a1 = 0.0, L * (sb - sa)
    else:
        a0, a1 = L * (sb - sp) / (sp * sb), L * (sp - sa)
    return a1 / 10 ** DEC1, a0 / 10 ** DEC0


def br(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--liquidity", type=int, required=True)
    ap.add_argument("--tick-lower", type=int, required=True)
    ap.add_argument("--tick-upper", type=int, required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--price", type=float, help="preço do BTC em USDC")
    g.add_argument("--sqrt-price-x96", type=int)
    ap.add_argument("--init-base", type=float, help="cbBTC depositado")
    ap.add_argument("--init-quote", type=float, help="USDC depositado")
    ap.add_argument("--fees-usd", type=float, default=0.0)
    a = ap.parse_args()

    sp = a.sqrt_price_x96 / 2 ** 96 if a.sqrt_price_x96 else sqrt_raw_from_btc_price(a.price)
    price = 1 / (sp ** 2 * ADJ)
    # tickLower (raw) corresponde ao MAIOR preço do BTC, por causa da inversão
    lo = btc_price_from_tick(a.tick_upper)
    hi = btc_price_from_tick(a.tick_lower)

    btc, usdc = amounts(a.liquidity, sp, a.tick_lower, a.tick_upper)
    value = btc * price + usdc
    status = "DENTRO" if lo <= price <= hi else ("ACIMA" if price > hi else "ABAIXO")

    print(f"Preço BTC: {br(price)}  |  Faixa: {br(lo)} – {br(hi)}  |  {status} da faixa")
    if status == "DENTRO":
        print(f"Distância: {br((price-lo)/price*100)}% da borda de baixo, "
              f"{br((hi-price)/price*100)}% da de cima")
    print(f"Posição: {btc:.8f} cbBTC + {br(usdc, 6)} USDC = {br(value)} USD")

    for label, p in (("borda de baixo", lo), ("borda de cima", hi)):
        b, u = amounts(a.liquidity, sqrt_raw_from_btc_price(p), a.tick_lower, a.tick_upper)
        line = f"Na {label} ({br(p)}): {b:.8f} cbBTC + {br(u, 4)} USDC = {br(b*p+u)} USD"
        if a.init_base is not None and a.init_quote is not None:
            hold = a.init_base * p + a.init_quote
            line += f"  | IL vs segurar: {br(b*p+u-hold, 4)}"
        print(line)

    if a.init_base is not None and a.init_quote is not None:
        hold = a.init_base * price + a.init_quote
        print(f"Segurar valeria: {br(hold)}  |  IL agora: {br(value-hold, 4)}  |  "
              f"Resultado c/ taxas: {br(value + a.fees_usd - hold, 4)}")

    half = (hi / math.sqrt(lo * hi)) - 1
    print(f"Faixa sugerida (mesma largura ±{br(half*100,1)}%): "
          f"{br(price*(1-half))} – {br(price*(1+half))}")


if __name__ == "__main__":
    main()
