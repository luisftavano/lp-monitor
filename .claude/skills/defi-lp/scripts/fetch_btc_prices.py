#!/usr/bin/env python3
"""
Baixa o histórico de preço do BTC em USD e salva como CSV (timestamp,close),
no formato que o backtest_ranges.py espera. Só leitura de APIs públicas.

Fontes: CoinGecko (padrão; horário até 90 dias) ou DefiLlama (--source llama).
Ex.: python3 fetch_btc_prices.py --days 90 --out data/btc_90d.csv
"""
import argparse
import csv
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "lp-monitor", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def coingecko(days):
    key = os.getenv("COINGECKO_API_KEY")
    headers = {"x-cg-demo-api-key": key} if key else {}
    data = get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
               f"?vs_currency=usd&days={days}", headers)
    return [(int(ts / 1000), float(p)) for ts, p in data["prices"]]


def defillama(days):
    start = int(time.time()) - days * 86400
    span = days * 24
    data = get(f"https://coins.llama.fi/chart/coingecko:bitcoin?start={start}&span={span}&period=1h")
    return [(int(pt["timestamp"]), float(pt["price"]))
            for pt in data["coins"]["coingecko:bitcoin"]["prices"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--source", choices=["coingecko", "llama"], default="coingecko")
    ap.add_argument("--out", default="data/btc_prices.csv")
    a = ap.parse_args()

    try:
        rows = coingecko(a.days) if a.source == "coingecko" else defillama(a.days)
    except Exception as e:
        print(f"Falhou em {a.source} ({e}); tentando a outra fonte...")
        rows = defillama(a.days) if a.source == "coingecko" else coingecko(a.days)

    rows = sorted(set(rows))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "close"])
        for ts, p in rows:
            w.writerow([datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M"), p])
    step_h = (rows[-1][0] - rows[0][0]) / max(len(rows) - 1, 1) / 3600
    print(f"{len(rows)} pontos salvos em {out} (passo médio ~{step_h:.1f}h)")
    print(f"Use --step-hours {max(1, round(step_h))} no backtest_ranges.py")


if __name__ == "__main__":
    main()
