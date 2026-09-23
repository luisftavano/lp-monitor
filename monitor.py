"""
Monitor de posição de liquidez — Uniswap v3 na Base.
Lê a posição on-chain (só leitura, sem chave privada), calcula o resultado
e manda alerta no WhatsApp (CallMeBot) e/ou Telegram quando algo muda.
"""
import json
import math
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from web3 import Web3

# ---------------- Config ----------------
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
POSITION_ID = int(os.getenv("POSITION_ID") or 0)
MODE = os.getenv("MODE", "normal")
PHONE = os.getenv("WHATSAPP_PHONE", "")          # ex: +5511999999999
APIKEY = os.getenv("CALLMEBOT_APIKEY", "")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN", "")      # token do bot (BotFather)
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")     # seu chat id
EDGE_PCT = float(os.getenv("EDGE_PCT", "5"))     # alerta quando faltar X% pra borda
SUMMARY_HOUR = int(os.getenv("SUMMARY_HOUR", "9"))  # hora do resumo diário (Brasília)
INITIAL_BASE = os.getenv("INITIAL_BASE")         # qtd do token volátil depositada (ex: BTC)
INITIAL_QUOTE = os.getenv("INITIAL_QUOTE")       # qtd da stable depositada (ex: USDC)
STATE_FILE = Path(__file__).parent / "state.json"

NPM = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"      # Uniswap v3 PositionManager (Base)
FACTORY = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"  # Uniswap v3 Factory (Base)
STABLES = {"USDC", "USDBC", "USDT", "DAI", "USDS", "EURC"}
MAX128 = 2**128 - 1
BRT = timezone(timedelta(hours=-3))

NPM_ABI = [
    {"name": "positions", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "tokenId", "type": "uint256"}],
     "outputs": [{"name": "nonce", "type": "uint96"}, {"name": "operator", "type": "address"},
                 {"name": "token0", "type": "address"}, {"name": "token1", "type": "address"},
                 {"name": "fee", "type": "uint24"}, {"name": "tickLower", "type": "int24"},
                 {"name": "tickUpper", "type": "int24"}, {"name": "liquidity", "type": "uint128"},
                 {"name": "fg0", "type": "uint256"}, {"name": "fg1", "type": "uint256"},
                 {"name": "tokensOwed0", "type": "uint128"}, {"name": "tokensOwed1", "type": "uint128"}]},
    {"name": "ownerOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "tokenId", "type": "uint256"}],
     "outputs": [{"name": "", "type": "address"}]},
    {"name": "collect", "type": "function", "stateMutability": "payable",
     "inputs": [{"name": "params", "type": "tuple", "components": [
         {"name": "tokenId", "type": "uint256"}, {"name": "recipient", "type": "address"},
         {"name": "amount0Max", "type": "uint128"}, {"name": "amount1Max", "type": "uint128"}]}],
     "outputs": [{"name": "amount0", "type": "uint256"}, {"name": "amount1", "type": "uint256"}]},
]
FACTORY_ABI = [{"name": "getPool", "type": "function", "stateMutability": "view",
                "inputs": [{"name": "a", "type": "address"}, {"name": "b", "type": "address"},
                           {"name": "fee", "type": "uint24"}],
                "outputs": [{"name": "", "type": "address"}]}]
POOL_ABI = [{"name": "slot0", "type": "function", "stateMutability": "view", "inputs": [],
             "outputs": [{"name": "sqrtPriceX96", "type": "uint160"}, {"name": "tick", "type": "int24"},
                         {"name": "oi", "type": "uint16"}, {"name": "oc", "type": "uint16"},
                         {"name": "ocn", "type": "uint16"}, {"name": "fp", "type": "uint8"},
                         {"name": "unlocked", "type": "bool"}]}]
ERC20_ABI = [
    {"name": "decimals", "type": "function", "stateMutability": "view", "inputs": [],
     "outputs": [{"name": "", "type": "uint8"}]},
    {"name": "symbol", "type": "function", "stateMutability": "view", "inputs": [],
     "outputs": [{"name": "", "type": "string"}]},
]


# ---------------- Matemática Uniswap v3 ----------------
def amounts_from_liquidity(L, sqrt_p, tick_lower, tick_upper):
    """Quantidades brutas (sem decimais) de token0/token1 numa posição."""
    sa = math.sqrt(1.0001 ** tick_lower)
    sb = math.sqrt(1.0001 ** tick_upper)
    if sqrt_p <= sa:
        return L * (sb - sa) / (sa * sb), 0.0
    if sqrt_p >= sb:
        return 0.0, L * (sb - sa)
    return L * (sb - sqrt_p) / (sqrt_p * sb), L * (sqrt_p - sa)


def analyze(pos, sqrt_price_x96, dec0, dec1, sym0, sym1, fees_raw):
    """Converte tudo para 'base' (volátil) cotado em 'quote' (stable, se houver)."""
    sqrt_p = sqrt_price_x96 / 2**96
    a0, a1 = amounts_from_liquidity(pos["liquidity"], sqrt_p, pos["tickLower"], pos["tickUpper"])
    a0, a1 = a0 / 10**dec0, a1 / 10**dec1
    f0, f1 = fees_raw[0] / 10**dec0, fees_raw[1] / 10**dec1

    adj = 10 ** (dec0 - dec1)
    p01 = sqrt_p**2 * adj                           # preço do token0 em token1
    lo01 = 1.0001 ** pos["tickLower"] * adj
    hi01 = 1.0001 ** pos["tickUpper"] * adj

    if sym0.upper() in STABLES and sym1.upper() not in STABLES:
        # token0 é a stable -> inverte para cotar o volátil (token1) em stable
        base, quote = sym1, sym0
        price, lower, upper = 1 / p01, 1 / hi01, 1 / lo01
        amt_b, amt_q, fee_b, fee_q = a1, a0, f1, f0
    else:
        base, quote = sym0, sym1
        price, lower, upper = p01, lo01, hi01
        amt_b, amt_q, fee_b, fee_q = a0, a1, f0, f1

    value = amt_b * price + amt_q
    fees_value = fee_b * price + fee_q

    if price < lower or price > upper:
        status = "out_range"
    else:
        dist = min(price - lower, upper - price) / price * 100
        status = "near_edge" if dist <= EDGE_PCT else "in_range"

    r = dict(base=base, quote=quote, price=price, lower=lower, upper=upper,
             amt_b=amt_b, amt_q=amt_q, fee_b=fee_b, fee_q=fee_q,
             value=value, fees_value=fees_value, status=status,
             hodl=None, il=None, net=None)

    if INITIAL_BASE and INITIAL_QUOTE:
        hodl = float(INITIAL_BASE) * price + float(INITIAL_QUOTE)
        r["hodl"] = hodl
        r["il"] = value - hodl                     # perda impermanente (negativa = perda)
        r["net"] = value + fees_value - hodl       # resultado real vs só segurar
    return r


# ---------------- Blockchain ----------------
def fetch_position():
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
    npm = w3.eth.contract(address=NPM, abi=NPM_ABI)
    p = npm.functions.positions(POSITION_ID).call()
    pos = dict(token0=p[2], token1=p[3], fee=p[4], tickLower=p[5], tickUpper=p[6],
               liquidity=p[7], owed0=p[10], owed1=p[11])

    t0 = w3.eth.contract(address=pos["token0"], abi=ERC20_ABI)
    t1 = w3.eth.contract(address=pos["token1"], abi=ERC20_ABI)
    dec0, dec1 = t0.functions.decimals().call(), t1.functions.decimals().call()
    sym0, sym1 = t0.functions.symbol().call(), t1.functions.symbol().call()

    pool_addr = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI).functions.getPool(
        pos["token0"], pos["token1"], pos["fee"]).call()
    slot0 = w3.eth.contract(address=pool_addr, abi=POOL_ABI).functions.slot0().call()

    # Taxas não coletadas: simula um collect (eth_call, não gasta nada nem muda nada)
    try:
        owner = npm.functions.ownerOf(POSITION_ID).call()
        fees = npm.functions.collect((POSITION_ID, owner, MAX128, MAX128)).call({"from": owner})
    except Exception:
        fees = (pos["owed0"], pos["owed1"])

    return pos, slot0[0], dec0, dec1, sym0, sym1, fees


# ---------------- Alertas ----------------
def send_alert(text):
    print("----- mensagem -----\n" + text)
    sent = False
    if PHONE and APIKEY:
        url = ("https://api.callmebot.com/whatsapp.php?phone=" + urllib.parse.quote(PHONE)
               + "&text=" + urllib.parse.quote(text) + "&apikey=" + urllib.parse.quote(APIKEY))
        resp = requests.get(url, timeout=30)
        print("WhatsApp:", resp.status_code)
        sent = True
    if TG_TOKEN and TG_CHAT:
        resp = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                             json={"chat_id": TG_CHAT, "text": text}, timeout=30)
        print("Telegram:", resp.status_code)
        sent = True
    if not sent:
        print("(nenhum canal configurado, só imprimindo)")


def fmt(x, d=2):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def report(r, title):
    lines = [title, "",
             f"Preço {r['base']}: {fmt(r['price'])} {r['quote']}",
             f"Faixa: {fmt(r['lower'])} – {fmt(r['upper'])}",
             f"Posição: {fmt(r['amt_b'], 6)} {r['base']} + {fmt(r['amt_q'])} {r['quote']}",
             f"Valor: {fmt(r['value'])} {r['quote']}",
             f"Taxas a coletar: {fmt(r['fees_value'])} {r['quote']}"]
    if r["net"] is not None:
        lines += [f"Se só tivesse segurado: {fmt(r['hodl'])}",
                  f"Perda impermanente: {fmt(r['il'])}",
                  f"Resultado real (c/ taxas): {fmt(r['net'])} {r['quote']}"]
    return "\n".join(lines)


STATUS_MSG = {
    "out_range": "🔴 FORA DA FAIXA — você parou de ganhar taxas. Avalie tirar ou reposicionar.",
    "near_edge": f"🟡 PERTO DA BORDA — preço a menos de {EDGE_PCT:g}% do limite da faixa.",
    "in_range": "🟢 De volta à faixa — ganhando taxas normalmente.",
}


def run_test():
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
    block = w3.eth.block_number
    print(f"Base conectada, bloco {block}")
    send_alert(f"✅ LP Monitor conectado!\nBase OK (bloco {block}).\n"
                  + (f"Monitorando posição #{POSITION_ID}." if POSITION_ID
                     else "Nenhuma posição configurada ainda."))


def main():
    if MODE == "teste":
        run_test()
        return
    if not POSITION_ID:
        print("Nenhuma posição configurada (POSITION_ID vazio). Nada a fazer.")
        return
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    pos, sqrt_price, dec0, dec1, sym0, sym1, fees = fetch_position()

    if pos["liquidity"] == 0:
        if state.get("status") != "closed":
            send_alert(f"⚪ Posição #{POSITION_ID} está sem liquidez (fechada ou retirada).")
        state["status"] = "closed"
        STATE_FILE.write_text(json.dumps(state, indent=2))
        return

    r = analyze(pos, sqrt_price, dec0, dec1, sym0, sym1, fees)
    msgs = []

    # 1) Mudança de status (fora / perto da borda / dentro)
    prev = state.get("status")
    if r["status"] != prev and not (prev is None and r["status"] == "in_range"):
        msgs.append(report(r, STATUS_MSG[r["status"]]))

    # 2) Perda impermanente passou das taxas acumuladas
    il_bad = r["net"] is not None and r["net"] < 0
    if il_bad and not state.get("il_bad"):
        msgs.append(report(r, "⚠️ A perda impermanente já passou das taxas: "
                              "hoje você estaria melhor só segurando os tokens."))
    elif not il_bad and state.get("il_bad"):
        msgs.append(report(r, "✅ As taxas voltaram a superar a perda impermanente."))

    # 3) Resumo diário
    now = datetime.now(BRT)
    today = now.strftime("%Y-%m-%d")
    if now.hour == SUMMARY_HOUR and state.get("last_summary") != today and not msgs:
        msgs.append(report(r, f"📊 Resumo diário — posição #{POSITION_ID}"))
        state["last_summary"] = today

    for m in msgs:
        send_alert(m)
    if not msgs:
        print(report(r, "(sem alertas)"))

    state.update(status=r["status"], il_bad=il_bad)
    STATE_FILE.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
