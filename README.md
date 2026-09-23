# LP Monitor — Uniswap v3 na Base

Monitora uma posição de liquidez e avisa no WhatsApp (e/ou Telegram) quando:

- 🔴 o preço sai da faixa (parou de ganhar taxa)
- 🟡 o preço chega perto da borda (padrão: 5%)
- ⚠️ a perda impermanente passa das taxas acumuladas
- 📊 resumo diário (padrão: 9h, horário de Brasília)

Só **lê** a blockchain. Não usa chave privada e não mexe na sua posição.
Custo: R$ 0 (GitHub Actions + RPC público da Base).

## 1. Canal de alerta

**WhatsApp (CallMeBot):** mande "I allow callmebot to send me messages" para o
número indicado em callmebot.com/blog/free-api-whatsapp-messages e guarde a apikey.

**Telegram (opcional, reserva):** crie um bot com @BotFather, mande /start pra ele
e pegue seu chat id em `https://api.telegram.org/bot<TOKEN>/getUpdates`.

Se os dois estiverem configurados, o alerta vai pelos dois.

## 2. Abrir a posição

No app da Uniswap, crie a posição na rede **Base** e escolha a versão **v3**
(o app às vezes sugere a v4, e este monitor lê só a v3).
Anote:
- o **ID da posição**: o número no final da URL da posição (`.../positions/v3/base/123456`)
- quanto você depositou de cada token (ex: 0.00075 cbBTC e 75 USDC)

## 3. Subir no GitHub

1. Crie um repositório **privado** e suba esta pasta (incluindo `.github/`).
2. Em *Settings → Secrets and variables → Actions*:
   - **Secrets**: `WHATSAPP_PHONE` (ex: `+5511999999999`) e `CALLMEBOT_APIKEY`; opcional: `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`
   - **Variables**: `POSITION_ID`, `INITIAL_BASE` (qtd do token volátil),
     `INITIAL_QUOTE` (qtd da stable). Opcionais: `EDGE_PCT`, `SUMMARY_HOUR`
3. Na aba *Actions*, abra "LP monitor" e clique em **Run workflow** pra testar.

## Testar local

```bash
pip install -r requirements.txt
POSITION_ID=123456 INITIAL_BASE=0.00075 INITIAL_QUOTE=75 python monitor.py
```
Sem nenhum canal configurado, ele só imprime a mensagem no terminal.

## Observações

- Roda a cada 30 min, o que dá ~1.440 min/mês, dentro dos 2.000 gratuitos de repo privado.
  O GitHub pode atrasar execuções agendadas em alguns minutos.
- Se o GitHub pausar o agendamento por inatividade, é só reativar na aba Actions.
- Se você reposicionar (fechar e abrir outra faixa), o ID muda: atualize
  `POSITION_ID`, `INITIAL_BASE` e `INITIAL_QUOTE`, e apague o `state.json`.
