import os, json, time, csv, io
from datetime import datetime, timezone
from urllib.request import urlopen, Request

# Freshness window (minutes) used to auto-label stale fallbacks
FRESH_MINUTES = int(os.getenv("VDP_FRESH_MINUTES", "10"))

def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _iso_from_epoch(sec):
    try:
        return datetime.utcfromtimestamp(int(sec)).replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return _now_iso()

def _is_stale(ts_utc: str, minutes: int = FRESH_MINUTES) -> bool:
    try:
        ts = (ts_utc or "").replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
    except Exception:
        return True
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() > minutes * 60

def _get_json(url, headers=None, timeout=6):
    req = Request(url, headers=headers or {"User-Agent": "teof/ocers"})
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _get_text(url, headers=None, timeout=6):
    req = Request(url, headers=headers or {"User-Agent": "teof/ocers"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")

def _env_price(key):
    v = os.getenv(key)
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None

def _retry(fn, attempts=2, delay=1.0):
    last = None
    for _ in range(attempts):
        last = fn()
        if last:
            return last
        time.sleep(delay)
    return last

def _pack(value, ts, source, provenance):
    d = {
        "value": float(value),
        "timestamp_utc": ts,
        "source": source,
        "provenance": provenance,
        "volatile": True,
    }
    if _is_stale(ts):
        d["stale_labeled"] = True
    return d

def _pack_env(key):
    v = _env_price(key)
    if v is not None:
        return _pack(v, _now_iso(), f"manual://env/{key}", "fallback:env")
    return None

# --- BTC (CoinGecko, then env) ---
def _fetch_btc_coingecko():
    try:
        data = _get_json(
            "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
        )
        price = float(data["market_data"]["current_price"]["usd"])
        ts = (data.get("last_updated") or _now_iso()).replace("+00:00", "Z")
        return _pack(price, ts, "https://api.coingecko.com/api/v3/coins/bitcoin", "auto:coingecko")
    except Exception:
        return None

def fetch_btc():
    got = _retry(_fetch_btc_coingecko)
    if got:
        return got
    env = _pack_env("PRICE_BTC")
    if env:
        return env
    return None

# --- Yahoo + Stooq helpers (equities/ETFs) ---
def _yf_quote(symbols):
    return _get_json("https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + symbols)

def _fetch_yf_one(symbol):
    try:
        j = _yf_quote(symbol)
        res = j["quoteResponse"]["result"]
        if not res:
            return None
        q = res[0]
        price = q.get("regularMarketPrice")
        t = q.get("regularMarketTime")
        if price is None or t is None:
            return None
        return _pack(price, _iso_from_epoch(t), f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}", "auto:yahoo")
    except Exception:
        return None

def _fetch_stooq_one(symbol):
    try:
        sym = symbol.lower() + ".us"
        url = f"https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv"
        text = _get_text(url)
        row = next(csv.DictReader(io.StringIO(text)), None)
        if not row:
            return None
        close = row.get("Close")
        date = row.get("Date")
        t = row.get("Time") or "00:00:00"
        if not close or close == "N/D":
            return None
        ts = f"{date}T{t}Z"
        return _pack(close, ts, url, "fallback:stooq")
    except Exception:
        return None

def _fetch_with_env(symbol, env_key):
    got = _retry(lambda: _fetch_yf_one(symbol))
    if got:
        return got
    got = _retry(lambda: _fetch_stooq_one(symbol))
    if got:
        return got
    env = _pack_env(env_key)
    if env:
        return env
    return None

def fetch_ibit():
    return _fetch_with_env("IBIT", "PRICE_IBIT")

def fetch_nvda():
    return _fetch_with_env("NVDA", "PRICE_NVDA")

def fetch_pltr():
    return _fetch_with_env("PLTR", "PRICE_PLTR")

def fetch_mstr():
    return _fetch_with_env("MSTR", "PRICE_MSTR")
