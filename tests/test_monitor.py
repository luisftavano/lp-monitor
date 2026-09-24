import importlib
import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ADJ = 10 ** (6 - 8)
TL, TU = -67620, -67120            # faixa ~82.194 – 86.408
L = 27602164


def sqrt_x96(btc_price):
    return math.sqrt((1 / btc_price) / ADJ) * 2 ** 96


def load(**env):
    os.environ.update({"POSITION_ID": "1", "INITIAL_BASE": "0.00011657",
                       "INITIAL_QUOTE": "10.082643", "EDGE_PCT": "1",
                       "WHATSAPP_PHONE": "", "CALLMEBOT_APIKEY": "",
                       "TELEGRAM_TOKEN": "", "TELEGRAM_CHAT_ID": ""})
    os.environ.update(env)
    import monitor
    return importlib.reload(monitor)


class TestMath(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.pos = dict(liquidity=L, tickLower=TL, tickUpper=TU)

    def analyze(self, price, fees=(0, 0)):
        return self.m.analyze(self.pos, sqrt_x96(price), 6, 8, "USDC", "cbBTC", fees)

    def test_in_range(self):
        r = self.analyze(84475)
        self.assertEqual(r["status"], "in_range")
        self.assertAlmostEqual(r["value"], 19.93, places=1)
        self.assertEqual(r["base"], "cbBTC")

    def test_above_is_all_usdc(self):
        r = self.analyze(90000)
        self.assertEqual(r["status"], "out_range")
        self.assertAlmostEqual(r["amt_b"], 0.0)

    def test_below_is_all_btc(self):
        r = self.analyze(80000)
        self.assertEqual(r["status"], "out_range")
        self.assertAlmostEqual(r["amt_q"], 0.0)

    def test_suggested_range_keeps_width(self):
        r = self.analyze(90000)
        lo, hi, pct = self.m.suggested_range(r)
        self.assertAlmostEqual(pct, 2.5, delta=0.1)
        self.assertLess(lo, 90000)
        self.assertGreater(hi, 90000)


class TestAlerts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.m = load()
        self.m.STATE_FILE = Path(self.tmp.name) / "state.json"
        self.sent = []
        self.m.send_alert = self.sent.append

    def tearDown(self):
        self.tmp.cleanup()

    def tick(self, price, fees=(0, 0)):
        pos = dict(liquidity=L, tickLower=TL, tickUpper=TU)
        self.m.fetch_position = lambda: (pos, sqrt_x96(price), 6, 8, "USDC", "cbBTC", fees)
        self.m.main()

    def test_no_alert_on_first_run_in_range(self):
        self.tick(84475)
        self.assertEqual(self.sent, [])

    def test_out_of_range_alerts_once(self):
        self.tick(84475)
        self.tick(90000)
        self.tick(90100)
        self.assertEqual(sum("FORA DA FAIXA" in s for s in self.sent), 1)

    def test_back_in_range(self):
        self.tick(84475)
        self.tick(90000)
        self.tick(84475)
        self.assertTrue(any("VOLTOU" in s for s in self.sent))

    def test_fees_alert_once_and_rearms(self):
        self.tick(84475)
        self.tick(84475, fees=(1_100_000, 0))      # 1,10 USDC
        self.tick(84475, fees=(1_200_000, 0))
        self.tick(84475, fees=(10_000, 0))         # coletou
        self.tick(84475, fees=(1_100_000, 0))
        self.assertEqual(sum("taxas acumuladas" in s for s in self.sent), 2)

    def test_state_file_written(self):
        self.tick(84475)
        state = json.loads(self.m.STATE_FILE.read_text())
        self.assertEqual(state["status"], "in_range")


class TestRpcFallback(unittest.TestCase):
    def test_falls_back_to_next_rpc(self):
        m = load(RPC_URL="https://ruim.example")
        tried = []

        def fn(w3):
            url = w3.provider.endpoint_uri
            tried.append(url)
            if url == "https://ruim.example":
                raise RuntimeError("429 Too Many Requests")
            return url

        self.assertEqual(m.with_rpc(fn), m.DEFAULT_RPCS[0])
        self.assertEqual(tried, ["https://ruim.example", m.DEFAULT_RPCS[0]])

    def test_raises_when_all_fail(self):
        m = load(RPC_URL="")

        def fn(w3):
            raise RuntimeError("fora do ar")

        with self.assertRaises(RuntimeError):
            m.with_rpc(fn)


class TestModes(unittest.TestCase):
    def test_run_test_exists(self):
        m = load()
        self.assertTrue(callable(getattr(m, "run_test", None)))


if __name__ == "__main__":
    unittest.main()
