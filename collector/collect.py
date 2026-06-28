#!/usr/bin/env python3
"""
Coletor do Crypto Panel — roda no GitHub Actions (cron horario) e tambem local.
Sem dependencias: usa apenas a stdlib.

Grava em <repo>/data:
  - cache.json          : preco/variacao + on-chain atual (fallback de mesma origem p/ o front)
  - candles_1d.json     : velas diarias FECHADAS por ativo (fallback do backtest)
  - onchain-history.json: snapshots on-chain acumulados (historico; limitado a ~90 dias)
"""
import json, os, urllib.request, datetime

ASSETS = [
    ("BTC", "BTCUSDT", "Bitcoin"),
    ("ETH", "ETHUSDT", "Ethereum"),
    ("SOL", "SOLUSDT", "Solana"),
    ("BNB", "BNBUSDT", "BSC"),
    ("XRP", "XRPUSDT", "XRPL"),
    ("SUI", "SUIUSDT", "Sui"),
]
BINANCE_HOSTS = ["https://api.binance.com", "https://data-api.binance.vision"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "crypto-panel-collector"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def binance(path):
    last = None
    for h in BINANCE_HOSTS:
        try:
            return get(h + path)
        except Exception as e:
            last = e
    raise last


def main():
    os.makedirs(DATA, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    cache = {"updated": now, "assets": {}}
    candles = {"updated": now, "interval": "1d", "assets": {}}
    onchain = {"ts": now, "btc": {}, "chains": {}}

    # preco + velas (Binance)
    for sym, pair, llama in ASSETS:
        try:
            tk = binance(f"/api/v3/ticker/24hr?symbol={pair}")
            kl = binance(f"/api/v3/klines?symbol={pair}&interval=1d&limit=400")
            cache["assets"][sym] = {
                "price": float(tk["lastPrice"]),
                "ch24": float(tk["priceChangePercent"]),
                "qv": float(tk["quoteVolume"]),
            }
            # exclui a ultima vela (dia em andamento); guarda [t,o,h,l,c,v]
            candles["assets"][sym] = [
                [k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                for k in kl[:-1]
            ]
        except Exception as e:
            cache["assets"][sym] = {"error": str(e)}
            print("WARN preco", sym, e)

    # on-chain BTC (mempool.space)
    try:
        hr = get("https://mempool.space/api/v1/mining/hashrate/3d")
        fees = get("https://mempool.space/api/v1/fees/recommended")
        mp = get("https://mempool.space/api/mempool")
        onchain["btc"] = {
            "hashrate": hr.get("currentHashrate"),
            "difficulty": hr.get("currentDifficulty"),
            "feeHalfHour": fees.get("halfHourFee"),
            "feeFastest": fees.get("fastestFee"),
            "mempoolCount": mp.get("count"),
        }
    except Exception as e:
        onchain["btc"] = {"error": str(e)}
        print("WARN btc onchain", e)

    # TVL por chain (DefiLlama)
    for sym, pair, llama in ASSETS:
        if sym == "BTC":
            continue
        try:
            s = get("https://api.llama.fi/v2/historicalChainTvl/" + llama)
            onchain["chains"][sym] = {"tvl": s[-1]["tvl"]} if s else {"error": "empty"}
        except Exception as e:
            onchain["chains"][sym] = {"error": str(e)}
            print("WARN tvl", sym, e)

    cache["onchain"] = onchain  # snapshot atual tambem no cache (fallback da tela on-chain)

    with open(os.path.join(DATA, "cache.json"), "w") as f:
        json.dump(cache, f, separators=(",", ":"))
    with open(os.path.join(DATA, "candles_1d.json"), "w") as f:
        json.dump(candles, f, separators=(",", ":"))

    hist_path = os.path.join(DATA, "onchain-history.json")
    hist = []
    if os.path.exists(hist_path):
        try:
            with open(hist_path) as f:
                hist = json.load(f)
        except Exception:
            hist = []
    hist.append(onchain)
    hist = hist[-2160:]  # ~90 dias em cadencia horaria
    with open(hist_path, "w") as f:
        json.dump(hist, f, separators=(",", ":"))

    ok = [s for s in cache["assets"] if "price" in cache["assets"][s]]
    print(f"collected {now} | precos ok: {ok} | hist len: {len(hist)}")


if __name__ == "__main__":
    main()
