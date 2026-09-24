#!/usr/bin/env python3
"""
Backtest simples de larguras de faixa para uma posição BTC/USDC de liquidez concentrada.

Entrada: CSV com colunas timestamp,close (preço do BTC em USD), em ordem cronológica,
de preferência horário. Estratégia simulada: abre a faixa centrada no preço; quando o
preço sai da faixa e fica fora por --delay-steps passos, remove, rebalanceia e reabre.

Modelo de taxas (ESTIMATIVA): enquanto está na faixa, rende
    pool_apr × eficiência(faixa) / eficiência(faixa_media_dos_LPs)
Ajuste --pool-apr (APR da pool na Uniswap) e --avg-lp-width conforme a realidade.

Ex.: python3 backtest_ranges.py precos.csv --capital 20 --widths 2 2.5 3 5 10
"""
import argparse
import csv
import math
from datetime import datetime


def eff(w):
    pa, pb = 1 - w, 1 + w
    return 1 / (1 - (pa / pb) ** 0.25)


def make_pos(capital, p, w):
    pa, pb = p * (1 - w), p * (1 + w)
    x_per_L = 1 / math.sqrt(p) - 1 / math.sqrt(pb)
    y_per_L = math.sqrt(p) - math.sqrt(pa)
    L = capital / (x_per_L * p + y_per_L)
    return dict(L=L, pa=pa, pb=pb)


def value(pos, p):
    L, pa, pb = pos["L"], pos["pa"], pos["pb"]
    if p <= pa:
        x, y = L * (1 / math.sqrt(pa) - 1 / math.sqrt(pb)), 0.0
    elif p >= pb:
        x, y = 0.0, L * (math.sqrt(pb) - math.sqrt(pa))
    else:
        x, y = L * (1 / math.sqrt(p) - 1 / math.sqrt(pb)), L * (math.sqrt(p) - math.sqrt(pa))
    return x * p + y


def run(prices, times, w, a):
    step_years = a.step_hours / (24 * 365)
    apr = a.pool_apr / 100 * eff(w) / eff(a.avg_lp_width / 100)
    capital = a.capital
    pos = make_pos(capital, prices[0], w)
    fees = costs = 0.0
    in_steps = rebal = out_count = 0
    for p in prices[1:]:
        v = value(pos, p)
        if pos["pa"] <= p <= pos["pb"]:
            in_steps += 1
            out_count = 0
            fees += v * apr * step_years
        else:
            out_count += 1
            if out_count > a.delay_steps:
                cost = a.gas_usd + v * 0.5 * a.swap_fee
                costs += cost
                capital = v + fees - cost      # reinveste as taxas no reposicionamento
                fees = 0.0
                pos = make_pos(capital, p, w)
                rebal += 1
                out_count = 0
    final = value(pos, prices[-1]) + fees
    return dict(in_pct=in_steps / (len(prices) - 1) * 100, rebal=rebal, costs=costs,
                final=final, apr_used=apr * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--capital", type=float, default=20)
    ap.add_argument("--widths", type=float, nargs="+", default=[2, 2.5, 3, 5, 10],
                    help="meia-largura em %% (2.5 = ±2,5%%)")
    ap.add_argument("--pool-apr", type=float, default=15.7)
    ap.add_argument("--avg-lp-width", type=float, default=10,
                    help="meia-largura média estimada dos LPs da pool, em %%")
    ap.add_argument("--step-hours", type=float, default=1)
    ap.add_argument("--delay-steps", type=int, default=2,
                    help="passos fora da faixa antes de reposicionar (tempo de reação)")
    ap.add_argument("--gas-usd", type=float, default=0.10)
    ap.add_argument("--swap-fee", type=float, default=0.0005)
    a = ap.parse_args()

    times, prices = [], []
    with open(a.csv) as f:
        for row in csv.DictReader(f):
            times.append(row["timestamp"])
            prices.append(float(row["close"]))

    p0, p1 = prices[0], prices[-1]
    hodl = a.capital / 2 / p0 * p1 + a.capital / 2
    print(f"Período: {times[0]} → {times[-1]}  ({len(prices)} pontos)")
    print(f"BTC: {p0:,.0f} → {p1:,.0f}  ({(p1/p0-1)*100:+.1f}%)")
    print(f"Referências: segurar 50/50 = {hodl:.2f}  |  só USDC = {a.capital:.2f}  |  "
          f"só BTC = {a.capital/p0*p1:.2f}\n")
    print(f"{'faixa':>7} {'APR na faixa':>13} {'% na faixa':>11} {'reposic.':>9} "
          f"{'custos':>8} {'final':>8} {'vs 50/50':>9}")
    for wp in a.widths:
        r = run(prices, times, wp / 100, a)
        print(f"{'±'+str(wp)+'%':>7} {r['apr_used']:>12.0f}% {r['in_pct']:>10.1f}% "
              f"{r['rebal']:>9} {r['costs']:>8.2f} {r['final']:>8.2f} {r['final']-hodl:>+9.2f}")
    print("\nTaxas são ESTIMATIVA (modelo de eficiência). Use para comparar faixas, "
          "não como previsão de lucro.")


if __name__ == "__main__":
    main()
