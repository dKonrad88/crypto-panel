#!/usr/bin/env python3
"""
Coletor do Crypto Panel — roda no GitHub Actions (cron horario) e tambem local.
Sem dependencias (stdlib) e sem chave para o caminho padrao.

Fontes (gratis):
  - Cripto : Binance (preco + velas, USDT)              [sem chave]
  - Acoes BR: brapi.dev (B3, BRL, historico completo)   [sem chave]
  - Cambio : AwesomeAPI USD-BRL (historico + atual)     [sem chave]
  - On-chain: mempool.space (BTC) + DefiLlama (TVL)      [sem chave]
  - Acoes US: brapi.dev (USD) — SO se BRAPI_TOKEN existir (token gratis do brapi.dev)

Grava em <repo>/data: cache.json, candles_1d.json, onchain-history.json
"""
import json, os, urllib.request, urllib.error, datetime, time

CRYPTO = [
    {"id":"BTC","name":"Bitcoin","type":"crypto","market":"Cripto","ccy":"USDT","binance":"BTCUSDT","tv":"BINANCE:BTCUSDT","llama":"Bitcoin"},
    {"id":"ETH","name":"Ethereum","type":"crypto","market":"Cripto","ccy":"USDT","binance":"ETHUSDT","tv":"BINANCE:ETHUSDT","llama":"Ethereum"},
    {"id":"SOL","name":"Solana","type":"crypto","market":"Cripto","ccy":"USDT","binance":"SOLUSDT","tv":"BINANCE:SOLUSDT","llama":"Solana"},
    {"id":"BNB","name":"BNB","type":"crypto","market":"Cripto","ccy":"USDT","binance":"BNBUSDT","tv":"BINANCE:BNBUSDT","llama":"BSC"},
    {"id":"XRP","name":"XRP","type":"crypto","market":"Cripto","ccy":"USDT","binance":"XRPUSDT","tv":"BINANCE:XRPUSDT","llama":"XRPL"},
    {"id":"SUI","name":"Sui","type":"crypto","market":"Cripto","ccy":"USDT","binance":"SUIUSDT","tv":"BINANCE:SUIUSDT","llama":"Sui"},
]
BR = [
    {"id":"PETR4","name":"Petrobras","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"PETR4","tv":"BMFBOVESPA:PETR4"},
    {"id":"VALE3","name":"Vale","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"VALE3","tv":"BMFBOVESPA:VALE3"},
    {"id":"ITUB4","name":"Itaú","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"ITUB4","tv":"BMFBOVESPA:ITUB4"},
    {"id":"BBAS3","name":"Banco do Brasil","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"BBAS3","tv":"BMFBOVESPA:BBAS3"},
    {"id":"BBDC4","name":"Bradesco","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"BBDC4","tv":"BMFBOVESPA:BBDC4"},
    {"id":"B3SA3","name":"B3","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"B3SA3","tv":"BMFBOVESPA:B3SA3"},
    {"id":"WEGE3","name":"WEG","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"WEGE3","tv":"BMFBOVESPA:WEGE3"},
    {"id":"ABEV3","name":"Ambev","type":"stock","market":"Ações BR","ccy":"BRL","brapi":"ABEV3","tv":"BMFBOVESPA:ABEV3"},
]
US = [
    {"id":"AAPL","name":"Apple","type":"stock","market":"Ações US","ccy":"USD","brapi":"AAPL","tv":"NASDAQ:AAPL"},
    {"id":"MSFT","name":"Microsoft","type":"stock","market":"Ações US","ccy":"USD","brapi":"MSFT","tv":"NASDAQ:MSFT"},
    {"id":"NVDA","name":"NVIDIA","type":"stock","market":"Ações US","ccy":"USD","brapi":"NVDA","tv":"NASDAQ:NVDA"},
    {"id":"AMZN","name":"Amazon","type":"stock","market":"Ações US","ccy":"USD","brapi":"AMZN","tv":"NASDAQ:AMZN"},
    {"id":"GOOGL","name":"Alphabet","type":"stock","market":"Ações US","ccy":"USD","brapi":"GOOGL","tv":"NASDAQ:GOOGL"},
    {"id":"META","name":"Meta","type":"stock","market":"Ações US","ccy":"USD","brapi":"META","tv":"NASDAQ:META"},
    {"id":"TSLA","name":"Tesla","type":"stock","market":"Ações US","ccy":"USD","brapi":"TSLA","tv":"NASDAQ:TSLA"},
    {"id":"SPY","name":"S&P 500 ETF","type":"stock","market":"Ações US","ccy":"USD","brapi":"SPY","tv":"AMEX:SPY"},
]
BINANCE_HOSTS = ["https://api.binance.com", "https://data-api.binance.vision"]
BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN", "").strip()
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FRONT_KEYS = ("id", "name", "type", "market", "ccy", "tv", "binance", "llama")


def get(url, timeout=25, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 502, 503):
                time.sleep(1.5 * (i + 1)); continue
            raise
        except Exception as e:
            last = e; time.sleep(1)
    raise last


def binance(path):
    last = None
    for h in BINANCE_HOSTS:
        try:
            return get(h + path)
        except Exception as e:
            last = e
    raise last


def brapi_quote(symbol):
    url = f"https://brapi.dev/api/quote/{symbol}?range=2y&interval=1d"
    if BRAPI_TOKEN:
        url += f"&token={BRAPI_TOKEN}"
    d = get(url)
    r = d["results"][0]
    h = r.get("historicalDataPrice") or []
    cd = [[p["date"] * 1000, p["open"], p["high"], p["low"], p["close"], p.get("volume") or 0]
          for p in h if p.get("close") is not None]
    cd = cd[:-1] if len(cd) > 1 else cd
    price = r.get("regularMarketPrice") or (cd[-1][4] if cd else None)
    ch24 = r.get("regularMarketChangePercent") or 0.0
    return cd, price, ch24


def fetch_fx():
    # Frankfurter (ECB, global, cloud-friendly) — historico + atual
    try:
        end = datetime.date.today()
        start = end - datetime.timedelta(days=760)
        d = get(f"https://api.frankfurter.app/{start}..{end}?from=USD&to=BRL")
        ser = []
        for ds, v in (d.get("rates") or {}).items():
            br = v.get("BRL")
            if br is None:
                continue
            t = int(datetime.datetime.strptime(ds, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).timestamp()) * 1000
            ser.append([t, br, br, br, br, 0])
        ser.sort(key=lambda z: z[0])
        cur = get("https://api.frankfurter.app/latest?from=USD&to=BRL")["rates"]["BRL"]
        if ser:
            return ser, float(cur)
    except Exception as e:
        print("WARN fx frankfurter", e)
    # fallback: AwesomeAPI (BR) — pode falhar de IP de nuvem
    d = get("https://economia.awesomeapi.com.br/json/daily/USD-BRL/360")
    ser = sorted(([int(x["timestamp"]) * 1000, float(x["bid"]), float(x["bid"]), float(x["bid"]), float(x["bid"]), 0] for x in d), key=lambda z: z[0])
    cur = get("https://economia.awesomeapi.com.br/json/last/USD-BRL")["USDBRL"]["bid"]
    return ser, float(cur)


def main():
    os.makedirs(DATA, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    universe = CRYPTO + (BR + US if BRAPI_TOKEN else [])  # acoes so com token (brapi sem token = cota minima)
    cache = {"updated": now, "fx": {}, "universe": [{k: a[k] for k in FRONT_KEYS if k in a} for a in universe], "assets": {}}
    candles = {"updated": now, "interval": "1d", "assets": {}}
    onchain = {"ts": now, "btc": {}, "chains": {}}

    # cambio
    try:
        fxc, fxp = fetch_fx()
        cache["fx"]["USDBRL"] = fxp
        candles["assets"]["USDBRL"] = fxc
    except Exception as e:
        cache["fx"]["USDBRL"] = None; print("WARN fx", e)

    # ativos
    for a in universe:
        try:
            if a["type"] == "crypto":
                tk = binance(f"/api/v3/ticker/24hr?symbol={a['binance']}")
                kl = binance(f"/api/v3/klines?symbol={a['binance']}&interval=1d&limit=500")
                price = float(tk["lastPrice"]); ch24 = float(tk["priceChangePercent"])
                cd = [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in kl[:-1]]
            else:
                cd, price, ch24 = brapi_quote(a["brapi"]); time.sleep(0.3)
            cache["assets"][a["id"]] = {"price": price, "ch24": ch24, "ccy": a["ccy"], "type": a["type"], "market": a["market"]}
            candles["assets"][a["id"]] = cd
        except Exception as e:
            cache["assets"][a["id"]] = {"error": str(e), "ccy": a["ccy"], "type": a["type"], "market": a["market"]}
            print("WARN ativo", a["id"], e)

    # on-chain BTC
    try:
        hr = get("https://mempool.space/api/v1/mining/hashrate/3d")
        fees = get("https://mempool.space/api/v1/fees/recommended")
        mp = get("https://mempool.space/api/mempool")
        onchain["btc"] = {"hashrate": hr.get("currentHashrate"), "difficulty": hr.get("currentDifficulty"),
                          "feeHalfHour": fees.get("halfHourFee"), "feeFastest": fees.get("fastestFee"),
                          "mempoolCount": mp.get("count")}
    except Exception as e:
        onchain["btc"] = {"error": str(e)}; print("WARN btc onchain", e)
    for a in CRYPTO:
        if a["id"] == "BTC":
            continue
        try:
            s = get("https://api.llama.fi/v2/historicalChainTvl/" + a["llama"])
            onchain["chains"][a["id"]] = {"tvl": s[-1]["tvl"]} if s else {"error": "empty"}
        except Exception as e:
            onchain["chains"][a["id"]] = {"error": str(e)}
    cache["onchain"] = onchain

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
    hist = hist[-2160:]
    with open(hist_path, "w") as f:
        json.dump(hist, f, separators=(",", ":"))

    ok = [k for k, v in cache["assets"].items() if "price" in v]
    print(f"collected {now} | ok {len(ok)}/{len(universe)} | US={'on' if BRAPI_TOKEN else 'off'} | fx {cache['fx'].get('USDBRL')} | hist {len(hist)}")


if __name__ == "__main__":
    main()
