"""
Polymarket Edge Bot — version finale
======================================
Stratégie : détecter les marchés mal pricés en comparant
le prix Polymarket à des sources externes vérifiables.

Sources d'edge :
  1. CRYPTO_THRESHOLD : BTC/ETH above/below $X → prix Binance
  2. CRYPTO_UPDOWN    : BTC/ETH Up or Down → variation depuis ouverture
  3. WEATHER          : Température max/min ville → prévision Open-Meteo

Fixes v4 :
  - bankroll_engaged : distingue capital libre et capital engagé
  - circuit-breaker sur valeur totale (libre + engagé)
  - paper mode : résolution en 30s au lieu d'attendre time_left
  - MAX_CONCURRENT et MAX_RISK cohérents pour éviter over-allocation
  - Kelly fractionnel (1/4) pour le sizing

Dépendances :
  pip install requests ccxt py_clob_client_v2 python-dotenv

Fichier .env :
  POLY_PRIVATE_KEY=0x...
  POLY_API_KEY=...
  POLY_SECRET=...
  POLY_PASSPHRASE=...
  PAPER_MODE=true
  BANKROLL=1000
  MIN_EDGE=0.03
  MAX_RISK=0.02
  MAX_CONCURRENT=15
  SCAN_INTERVAL=30
  MIN_LIQUIDITY=200
"""

import json
import math
import os
import re
import time
import logging
import requests
import ccxt
from datetime import datetime, timezone
from dotenv import load_dotenv
from py_clob_client_v2 import ClobClient, OrderArgs, OrderType, Side, ApiCreds
from py_clob_client_v2.constants import POLYGON

# ─────────────────────────────────────────────
# 0. LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("edge_bot")

# ─────────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────────
load_dotenv()

PRIVATE_KEY = os.environ["POLY_PRIVATE_KEY"]
API_KEY = os.environ.get("POLY_API_KEY", "")
API_SECRET = os.environ.get("POLY_SECRET", "")
API_PASS = os.environ.get("POLY_PASSPHRASE", "")

INITIAL_BANKROLL = float(os.environ.get("BANKROLL", "50"))
MAX_RISK_PER_TRADE = float(os.environ.get("MAX_RISK", "0.02"))
MIN_EDGE = float(os.environ.get("MIN_EDGE", "0.02"))
MAX_DRAWDOWN = float(os.environ.get("MAX_DRAWDOWN", "0.10"))
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", "30"))
ENTRY_MIN = int(os.environ.get("ENTRY_MIN", "60"))
ENTRY_MAX = int(os.environ.get("ENTRY_MAX", "86400"))
MIN_LIQUIDITY = float(os.environ.get("MIN_LIQUIDITY", "200"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "200"))
PAPER_MODE = os.environ.get("PAPER_MODE", "true").lower() == "true"
FEES = 0.015  # frais Polymarket ~1.5%
MAX_RISK=0.03        # 3% max par trade
MIN_MARKET_PRICE=0.10   # tokens > 10¢ seulement
MAX_STAKE=5.00

# ─────────────────────────────────────────────
# 2. CLIENTS
# ─────────────────────────────────────────────
creds = ApiCreds(
    api_key=API_KEY,
    api_secret=API_SECRET,
    api_passphrase=API_PASS,
)
client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=POLYGON,
    key=PRIVATE_KEY,
    creds=creds,
)
exchange = ccxt.binance({"enableRateLimit": True})

# ─────────────────────────────────────────────
# 3. ÉTAT
# ─────────────────────────────────────────────
bankroll = INITIAL_BANKROLL
bankroll_engaged = 0.0  # capital dans des paris ouverts
peak_bankroll = INITIAL_BANKROLL
open_orders = {}
bet_market_ids = set()
pnl_history = []

# Caches
_updown_start_prices = {}  # slug → prix de référence
_weather_cache = {}  # (lat,lon,date) → temp max


# ─────────────────────────────────────────────
# 4. UTILITAIRES
# ─────────────────────────────────────────────
def _parse_end_ts(date_str: str) -> int | None:
    if not date_str:
        return None
    try:
        ts = int(float(str(date_str)))
        if ts > 4_102_444_800:
            ts //= 1000
        return ts
    except (ValueError, TypeError):
        pass
    for fmt in (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S+00:00",
            "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(str(date_str), fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def kelly_size(prob: float, price: float) -> float:
    """
    Mise optimale via Kelly fractionnel (1/4 Kelly).
    Plafonnée à MAX_RISK_PER_TRADE × bankroll libre.
    """
    if price <= 0 or price >= 1:
        return 0.0
    b = (1.0 - price) / price
    q = 1.0 - prob
    f = max(0.0, (prob * b - q) / b)
    f_kelly = f / 4
    max_mise = min(f_kelly, MAX_RISK_PER_TRADE) * bankroll
    return round(max_mise, 2)


# ─────────────────────────────────────────────
# 5. SOURCES EXTERNES
# ─────────────────────────────────────────────

CRYPTO_SYMBOLS = {
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "eth": "ETH",
    "solana": "SOL", "sol": "SOL",
    "xrp": "XRP", "ripple": "XRP",
    "bnb": "BNB",
}

UPDOWN_SYMBOLS = {
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "eth": "ETH",
    "solana": "SOL", "sol": "SOL",
}

CITY_COORDS = {
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "toulouse": (43.6047, 1.4442),
    "tokyo": (35.6762, 139.6503),
    "seoul": (37.5665, 126.9780),
    "busan": (35.1796, 129.0756),
    "beijing": (39.9042, 116.4074),
    "shanghai": (31.2304, 121.4737),
    "dubai": (25.2048, 55.2708),
    "singapore": (1.3521, 103.8198),
    "sydney": (-33.8688, 151.2093),
    "moscow": (55.7558, 37.6176),
    "berlin": (52.5200, 13.4050),
    "rome": (41.9028, 12.4964),
    "madrid": (40.4168, -3.7038),
    "chicago": (41.8781, -87.6298),
    "miami": (25.7617, -80.1918),
    "toronto": (43.6532, -79.3832),
    "hong kong": (22.3193, 114.1694),
    "mumbai": (19.0760, 72.8777),
    "bangkok": (13.7563, 100.5018),
    "cairo": (30.0444, 31.2357),
    "jakarta": (-6.2088, 106.8456),
    "mexico city": (19.4326, -99.1332),
    "sao paulo": (-23.5505, -46.6333),
    "istanbul": (41.0082, 28.9784),
    "lagos": (6.5244, 3.3792),
    "karachi": (24.8607, 67.0011),
    "lima": (-12.0464, -77.0428),
    "chicago": (41.8781, -87.6298),
    "amsterdam": (52.3676, 4.9041),
    "brussels": (50.8503, 4.3517),
    "zurich": (47.3769, 8.5417),
    "vienna": (48.2082, 16.3738),
    "stockholm": (59.3293, 18.0686),
    "oslo": (59.9139, 10.7522),
    "copenhagen": (55.6761, 12.5683),
    "helsinki": (60.1699, 24.9384),
    "warsaw": (52.2297, 21.0122),
    "prague": (50.0755, 14.4378),
    "budapest": (47.4979, 19.0402),
    "bucharest": (44.4268, 26.1025),
    "athens": (37.9838, 23.7275),
    "lisbon": (38.7223, -9.1393),
}


def get_crypto_price(symbol: str) -> float | None:
    try:
        ticker = exchange.fetch_ticker(f"{symbol}/USDT")
        return float(ticker["last"])
    except Exception:
        try:
            ticker = exchange.fetch_ticker(f"{symbol}/USD")
            return float(ticker["last"])
        except Exception as exc:
            log.debug("Prix %s indisponible : %s", symbol, exc)
            return None


def get_temp_forecast(city: str, date_str: str = None) -> float | None:
    city_lower = city.lower().strip()
    coords = None
    for name, c in CITY_COORDS.items():
        if name in city_lower or city_lower in name:
            coords = c
            break
    if coords is None:
        return None

    lat, lon = coords
    cache_key = f"{lat},{lon},{date_str or 'today'}"
    if cache_key in _weather_cache:
        return _weather_cache[cache_key]

    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])

        temp = None
        if date_str and dates:
            for i, d in enumerate(dates):
                if date_str in d:
                    # Choisit max ou min selon la question
                    temp = daily.get("temperature_2m_max", [None])[i]
                    break
        if temp is None and daily.get("temperature_2m_max"):
            temp = daily["temperature_2m_max"][0]

        if temp is not None:
            temp = float(temp)
            _weather_cache[cache_key] = temp
        return temp
    except Exception as exc:
        log.debug("Open-Meteo erreur : %s", exc)
        return None


# ─────────────────────────────────────────────
# 6. STRATÉGIES D'ESTIMATION DE PROBABILITÉ
# ─────────────────────────────────────────────

def estimate_crypto_prob(question: str, outcome: str) -> tuple[float | None, str]:
    """Stratégie CRYPTO_THRESHOLD : BTC above/below $X."""
    q = question.lower()

    symbol = None
    for key, val in CRYPTO_SYMBOLS.items():
        if key in q:
            symbol = val
            break
    if symbol is None:
        return None, ""

    # Détecte la direction
    above = any(w in q for w in ["above", "over", "exceed", "higher", "au-dessus"])
    below = any(w in q for w in ["below", "under", "less than", "en-dessous", "sous"])
    if not above and not below:
        return None, ""

    # Extrait le seuil de prix
    matches = re.findall(r'\$\s*([\d,]+(?:\.\d+)?)\s*[kK]?', question)
    if not matches:
        return None, ""
    try:
        raw = matches[0].replace(",", "")
        threshold = float(raw)
        k_pos = question.find(raw)
        if k_pos > 0 and question[k_pos + len(raw):k_pos + len(raw) + 1].lower() == "k":
            threshold *= 1000
    except (ValueError, IndexError):
        return None, ""

    current = get_crypto_price(symbol)
    if current is None:
        return None, ""

    distance = abs(current - threshold) / threshold
    direction = "above" if above else "below"

    if direction == "above":
        if current > threshold:
            if distance > 0.10:
                raw_prob = 0.98
            elif distance > 0.05:
                raw_prob = 0.95
            elif distance > 0.02:
                raw_prob = 0.90
            elif distance > 0.01:
                raw_prob = 0.82
            else:
                raw_prob = 0.70
        else:
            if distance > 0.10:
                raw_prob = 0.02
            elif distance > 0.05:
                raw_prob = 0.05
            elif distance > 0.02:
                raw_prob = 0.15
            else:
                raw_prob = 0.35
    else:
        if current < threshold:
            if distance > 0.10:
                raw_prob = 0.98
            elif distance > 0.05:
                raw_prob = 0.95
            elif distance > 0.02:
                raw_prob = 0.90
            elif distance > 0.01:
                raw_prob = 0.82
            else:
                raw_prob = 0.70
        else:
            if distance > 0.10:
                raw_prob = 0.02
            elif distance > 0.05:
                raw_prob = 0.05
            elif distance > 0.02:
                raw_prob = 0.15
            else:
                raw_prob = 0.35

    if outcome.lower() in ("no", "non", "down"):
        raw_prob = 1.0 - raw_prob

    return round(raw_prob, 4), f"CRYPTO_THRESHOLD({symbol})"


UPDOWN_PATTERN = re.compile(
    r'\b(Bitcoin|Ethereum|Solana|BTC|ETH|SOL)\b.*Up or Down',
    re.IGNORECASE,
)


def estimate_updown_prob(question: str, market: dict, outcome: str) -> tuple[float | None, str]:
    """Stratégie CRYPTO_UPDOWN : BTC/ETH Up or Down sur fenêtre courte."""
    if not UPDOWN_PATTERN.search(question):
        return None, ""

    q = question.lower()
    symbol = None
    for key, val in UPDOWN_SYMBOLS.items():
        if key in q:
            symbol = val
            break
    if symbol is None:
        return None, ""

    current = get_crypto_price(symbol)
    if current is None:
        return None, ""

    slug = market.get("slug", "")
    if slug in _updown_start_prices:
        start = _updown_start_prices[slug]
    else:
        last = market.get("lastTradePrice")
        if last is None:
            return None, ""
        start = float(last)
        _updown_start_prices[slug] = start

    if start <= 0:
        return None, ""

    variation = (current - start) / start

    def var_to_prob(var: float) -> float:
        a = abs(var)
        if a > 0.010:
            b = 0.97
        elif a > 0.005:
            b = 0.93
        elif a > 0.002:
            b = 0.85
        elif a > 0.001:
            b = 0.75
        else:
            b = 0.58
        return b if var > 0 else (1.0 - b)

    raw_prob = var_to_prob(variation)

    if outcome.lower() == "down":
        raw_prob = 1.0 - raw_prob
    elif outcome.lower() not in ("up",):
        pass  # Yes → suppose Up

    return round(raw_prob, 4), f"CRYPTO_UPDOWN({symbol})"


TEMP_PATTERN = re.compile(
    r'(?:highest|lowest|max|min)?\s*temperature\s+in\s+([\w\s]+?)\s+be\s+([\d.]+)\s*°?([CF])?',
    re.IGNORECASE,
)

MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def estimate_temp_prob(question: str, outcome: str) -> tuple[float | None, str]:
    """Stratégie WEATHER : température max/min d'une ville."""
    match = TEMP_PATTERN.search(question)
    if not match:
        return None, ""

    city = match.group(1).strip()
    threshold = float(match.group(2))
    unit = match.group(3) or "C"

    if unit.upper() == "F":
        threshold = (threshold - 32) * 5 / 9

    # Détecte la date
    date_match = re.search(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)',
        question, re.IGNORECASE,
    )
    date_str = None
    if date_match:
        month = MONTH_MAP.get(date_match.group(1).lower(), "")
        day = date_match.group(2).zfill(2)
        year = str(time.gmtime().tm_year)
        date_str = f"{year}-{month}-{day}"

    # Détecte lowest vs highest
    is_min = "lowest" in question.lower() or "minimum" in question.lower()

    forecast = get_temp_forecast(city, date_str)
    if forecast is None:
        return None, ""

    # Pour les marchés "lowest", on ajuste la prévision
    if is_min:
        forecast -= 8  # approximation : min ≈ max - 8°C

    diff = abs(forecast - threshold)

    if diff < 0.5:
        prob = 0.82
    elif diff < 1.0:
        prob = 0.60
    elif diff < 1.5:
        prob = 0.35
    elif diff < 2.5:
        prob = 0.12
    elif diff < 4.0:
        prob = 0.05
    else:
        prob = 0.02

    if outcome.lower() in ("no", "non"):
        prob = 1.0 - prob

    return round(prob, 4), f"WEATHER({city})"


# ─────────────────────────────────────────────
# 7. FETCH MARCHÉS
# ─────────────────────────────────────────────

def fetch_active_markets(limit: int = 300) -> list[dict]:
    results = []
    offset = 0
    now = int(time.time())

    while True:
        log.info("  → Scan gamma-api/markets offset=%d ...", offset)
        data = None

        for attempt in range(3):
            try:
                resp = requests.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={
                        "active": "true",
                        "closed": "false",
                        "limit": 100,
                        "offset": offset,
                        "order": "endDate",
                        "ascending": "true",
                    },
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.Timeout:
                log.warning("  Timeout tentative %d/3 ...", attempt + 1)
                time.sleep(2)
            except requests.RequestException as exc:
                log.warning("  Erreur : %s", exc)
                break

        if not data:
            break

        for m in data:
            end_ts = _parse_end_ts(m.get("endDate") or "")
            if end_ts is None:
                continue

            time_left = end_ts - now
            if time_left < ENTRY_MIN or time_left > ENTRY_MAX:
                continue

            liquidity = float(m.get("liquidityNum") or m.get("liquidity") or 0)
            if liquidity < MIN_LIQUIDITY:
                continue

            try:
                token_ids = json.loads(m.get("clobTokenIds") or "[]")
            except (json.JSONDecodeError, TypeError):
                continue

            if len(token_ids) < 2:
                continue

            try:
                outcomes = json.loads(m.get("outcomes") or '["Yes","No"]')
            except (json.JSONDecodeError, TypeError):
                outcomes = ["Yes", "No"]

            try:
                prices = json.loads(m.get("outcomePrices") or '["0.5","0.5"]')
            except (json.JSONDecodeError, TypeError):
                prices = ["0.5", "0.5"]

            m["_tokens"] = [
                {
                    "token_id": token_ids[i],
                    "outcome": outcomes[i] if i < len(outcomes) else str(i),
                    "price": float(prices[i]) if i < len(prices) else 0.5,
                }
                for i in range(len(token_ids))
            ]

            m["_time_left"] = time_left
            m["_question"] = m.get("question") or m.get("title") or "?"
            m["_liquidity"] = liquidity
            results.append(m)

        offset += 100
        if len(data) < 100 or len(results) >= limit:
            break
        time.sleep(0.3)

    log.info("Marchés retenus : %d", len(results))
    return results


# ─────────────────────────────────────────────
# 8. PRIX DU CARNET
# ─────────────────────────────────────────────

def get_market_price(token_id: str, market: dict = None) -> dict | None:
    # Priorité 1 : prix gamma
    if market:
        best_ask = market.get("bestAsk")
        best_bid = market.get("bestBid")
        if best_ask is not None and best_bid is not None:
            best_ask = float(best_ask)
            best_bid = float(best_bid)
            spread = best_ask - best_bid
            if 0 < spread < 0.25:
                depth = market.get("_liquidity", 0) / 2
                return {
                    "best_ask": best_ask,
                    "best_bid": best_bid,
                    "mid": (best_ask + best_bid) / 2,
                    "spread": spread,
                    "depth": depth,
                }

    # Priorité 2 : CLOB
    try:
        ob = client.get_order_book(token_id)
        asks = [(float(a["price"]), float(a["size"])) for a in (ob.get("asks") or [])]
        bids = [(float(b["price"]), float(b["size"])) for b in (ob.get("bids") or [])]

        if not asks or not bids:
            return None

        best_ask = asks[0][0]
        best_bid = bids[0][0]
        spread = best_ask - best_bid

        if spread > 0.25:
            return None

        return {
            "best_ask": best_ask,
            "best_bid": best_bid,
            "mid": (best_ask + best_bid) / 2,
            "spread": spread,
            "depth": sum(p * s for p, s in asks[:5]),
        }
    except Exception as exc:
        log.debug("Erreur CLOB token=%s : %s", token_id, exc)
        return None


# ─────────────────────────────────────────────
# 9. ÉVALUATION D'UN MARCHÉ
# ─────────────────────────────────────────────

def evaluate_market(market: dict) -> list[dict]:
    question = market.get("_question", "")
    time_left = market["_time_left"]
    market_id = market.get("id") or market.get("conditionId", "")

    if market_id in bet_market_ids:
        return []

    opportunities = []

    for token in (market.get("_tokens") or []):
        tid = token.get("token_id")
        outcome = token.get("outcome", "Yes")
        if not tid:
            continue

        true_prob = None
        strategy = None

        # Stratégie 1 : Crypto threshold
        if true_prob is None:
            p, s = estimate_crypto_prob(question, outcome)
            if p is not None:
                true_prob, strategy = p, s

        # Stratégie 2 : Crypto Up/Down
        if true_prob is None:
            p, s = estimate_updown_prob(question, market, outcome)
            if p is not None:
                true_prob, strategy = p, s

        # Stratégie 3 : Météo température
        if true_prob is None:
            p, s = estimate_temp_prob(question, outcome)
            if p is not None:
                true_prob, strategy = p, s

        if true_prob is None:
            log.debug("  ✗ pas de stratégie : %s", question[:80])
            continue

        # Prix du marché
        ob = get_market_price(tid, market=market)
        if ob is None:
            continue

        # Filtre liquidité minimale
        if ob["depth"] < 10:
            log.debug("  ✗ liquidité trop faible (depth=%.2f$) : %s", ob["depth"], question[:55])
            continue

        market_price = ob["best_ask"]
        if market_price < 0.05:
            log.debug("  ✗ prix trop bas (%.3f) → liquidité inexistante : %s", market_price, question[:55])
            continue
        if market_price > 0.95:
            log.debug("  ✗ prix trop haut (%.3f) → payout nul : %s", market_price, question[:55])
            continue

        edge = true_prob - market_price - FEES

        log.info(
            "  [%s] %s | %s | P_true=%.3f P_mkt=%.3f edge=%.3f spread=%.3f depth=%.0f$",
            strategy, question[:50], outcome,
            true_prob, market_price, edge, ob["spread"], ob["depth"],
        )

        if edge < MIN_EDGE:
            continue
        if ob["spread"] > 0.20:
            continue
        if true_prob < 0.60:
            continue

        stake = kelly_size(true_prob, market_price)
        if stake < 1.0:
            continue

        opportunities.append({
            "market_id": market_id,
            "market_slug": market.get("slug", ""),
            "market_name": question,
            "strategy": strategy,
            "token_id": tid,
            "outcome": outcome,
            "true_prob": round(true_prob, 4),
            "market_price": round(market_price, 4),
            "edge": round(edge, 4),
            "spread": ob["spread"],
            "depth": ob["depth"],
            "time_left": time_left,
            "stake": stake,
        })

        time.sleep(0.05)

    return opportunities


# ─────────────────────────────────────────────
# 10. PLACEMENT D'ORDRE
# ─────────────────────────────────────────────

def place_order(opp: dict) -> str | None:
    global bankroll, bankroll_engaged

    price = round(opp["market_price"] + 0.005, 3)
    stake = min(opp["stake"], bankroll * 0.05)  # max 5% du bankroll

    # Contrainte 2 : size limitée par la profondeur réelle du carnet
    max_size_by_depth = opp["depth"] * 0.30  # max 30% de la liquidité disponible
    size = min(
        round(stake / opp["market_price"], 2),
        max_size_by_depth,
    )

    # Contrainte 3 : recalcule la mise réelle
    stake = round(size * opp["market_price"], 2)

    if stake < 0.50:  # mise trop petite après contraintes → skip
        log.debug("  ✗ mise trop petite après contraintes (%.2f$)", stake)
        return None

    if PAPER_MODE:
        fake_id = f"PAPER-{int(time.time() * 1000)}"
        log.info(
            "[PAPER] [%s] %s | %s | P=%.3f edge=%.3f mise=%.2f$ depth=%.0f$ %ds",
            opp["strategy"], opp["market_name"][:45], opp["outcome"],
            opp["true_prob"], opp["edge"], opp["stake"],
            opp["depth"], opp["time_left"],
        )
        open_orders[fake_id] = {
            **opp, "price": price, "size": size, "ts": time.time(),
        }
        return fake_id

    try:
        order_args = OrderArgs(
            token_id=opp["token_id"],
            price=price,
            size=size,
            side=Side.BUY,
        )
        resp = client.create_and_post_order(order_args, order_type=OrderType.FOK)
        oid = resp.get("orderID") or resp.get("id")
        if oid:
            log.info("✅ %s | mise=%.2f$ edge=%.3f", oid, opp["stake"], opp["edge"])
            open_orders[oid] = {
                **opp, "price": price, "size": size, "ts": time.time(),
            }
            return oid
        log.warning("Ordre rejeté : %s", resp)
    except Exception as exc:
        log.error("Erreur ordre : %s", exc)
    return None


# ─────────────────────────────────────────────
# 11. SUIVI DES ORDRES & P&L
# ─────────────────────────────────────────────

def reconcile_open_orders():
    global bankroll, bankroll_engaged
    now = time.time()
    resolved = []

    for oid, meta in open_orders.items():
        age = now - meta["ts"]

        if PAPER_MODE:
            # En paper : résout après 30s pour recycler le capital rapidement
            if age < 30:
                continue
        else:
            # En live : attend l'expiry + 30s de marge
            if age < meta["time_left"] + 30:
                continue

        if PAPER_MODE:
            # On attend quand même l'expiry réel
            if age < meta["time_left"] + 30:
                continue
            # Mais on vérifie le VRAI résultat sur Polymarket
            won = _fetch_result(meta["market_slug"], meta["outcome"])
            if won is None:
                log.debug("Résultat pas encore disponible pour %s", oid)
                continue
            gain = _apply_pnl(meta, won)
            _log_result(oid, meta, won, gain)
            resolved.append(oid)

        try:
            info = client.get_order(oid)
            status = info.get("status", "")

            if status in ("MATCHED", "FILLED"):
                won = _fetch_result(meta["market_slug"], meta["outcome"])
                if won is None:
                    continue
                gain = _apply_pnl(meta, won)
                _log_result(oid, meta, won, gain)
                resolved.append(oid)

            elif status in ("CANCELLED", "EXPIRED", "UNMATCHED"):
                bankroll += meta["stake"]
                bankroll_engaged -= meta["stake"]
                log.info("Ordre %s non exécuté → remboursé %.2f$", oid, meta["stake"])
                resolved.append(oid)

        except Exception as exc:
            log.warning("Vérif ordre %s : %s", oid, exc)

    for oid in resolved:
        bet_market_ids.discard(open_orders[oid].get("market_id", ""))
        del open_orders[oid]


def _fetch_result(slug: str, outcome: str) -> bool | None:
    try:
        resp = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        market = (data[0] if isinstance(data, list) else data) if data else {}

        if not market.get("resolved"):
            return None

        outcomes = json.loads(market.get("outcomes") or "[]")
        prices = json.loads(market.get("outcomePrices") or "[]")

        for i, p in enumerate(prices):
            if float(p) == 1.0 and i < len(outcomes):
                return outcomes[i].upper() == outcome.upper()
    except Exception as exc:
        log.warning("Résultat %s : %s", slug, exc)
    return None


def _apply_pnl(meta: dict, won: bool) -> float:
    global bankroll, bankroll_engaged
    stake = meta["stake"]
    bankroll_engaged -= stake

    if won:
        payout = meta["size"] * (1.0 - meta["price"])
        bankroll += stake + payout
        pnl_history.append(payout)
        return payout
    else:
        pnl_history.append(-stake)
        return -stake


def _log_result(oid: str, meta: dict, won: bool, gain: float):
    icon = "✅" if won else "❌"
    log.info(
        "%s %s | [%s] %s | P=%.3f | gain=%.2f$ | libre=%.2f$ engagé=%.2f$",
        icon, oid, meta.get("strategy", "?"), meta.get("market_name", "?")[:40],
        meta.get("true_prob", 0), gain, bankroll, bankroll_engaged,
    )


# ─────────────────────────────────────────────
# 12. CIRCUIT-BREAKER
# ─────────────────────────────────────────────

def check_circuit_breaker() -> bool:
    global peak_bankroll

    # Valeur totale = capital libre + capital engagé
    total = bankroll + bankroll_engaged
    peak_bankroll = max(peak_bankroll, total)
    drawdown = (peak_bankroll - total) / peak_bankroll if peak_bankroll > 0 else 0

    log.info(
        "Bankroll libre=%.2f$ | engagé=%.2f$ | total=%.2f$ | drawdown=%.2f%%",
        bankroll, bankroll_engaged, total, drawdown * 100,
    )

    if drawdown >= MAX_DRAWDOWN:
        log.critical("🛑 CIRCUIT-BREAKER | drawdown=%.2f%%", drawdown * 100)
        return True

    if len(pnl_history) >= 5 and all(p < 0 for p in pnl_history[-5:]):
        log.critical("🛑 5 pertes consécutives → pause 10 min")
        time.sleep(600)

    return False


# ─────────────────────────────────────────────
# 13. STATS
# ─────────────────────────────────────────────

def print_stats():
    total = len(pnl_history)
    if total == 0:
        return
    wins = sum(1 for p in pnl_history if p > 0)
    total_pnl = sum(pnl_history)
    roi = total_pnl / INITIAL_BANKROLL * 100
    wr = wins / total * 100
    log.info(
        "── STATS | P&L=%.2f$ | ROI=%.2f%% | WR=%.0f%% (%d/%d) | Actifs=%d",
        total_pnl, roi, wr, wins, total, len(open_orders),
    )


# ─────────────────────────────────────────────
# 14. BOUCLE PRINCIPALE
# ─────────────────────────────────────────────

def main():
    global bankroll, bankroll_engaged

    mode = "📄 PAPER" if PAPER_MODE else "💰 LIVE"
    log.info(
        "🚀 Edge Bot | %s | Bankroll=%.0f$ | MIN_EDGE=%.2f | "
        "MAX_RISK=%.1f%% | MAX_CONCURRENT=%d",
        mode, bankroll, MIN_EDGE, MAX_RISK_PER_TRADE * 100, MAX_CONCURRENT,
    )

    # Vérifie Binance
    btc = get_crypto_price("BTC")
    if btc:
        log.info("✅ Binance OK | BTC=%.2f$", btc)
    else:
        log.warning("⚠️  Binance indisponible")

    # Vérifie Open-Meteo
    temp = get_temp_forecast("paris")
    if temp:
        log.info("✅ Open-Meteo OK | Paris max=%.1f°C", temp)
    else:
        log.warning("⚠️  Open-Meteo indisponible")

    cycle = 0
    while True:
        try:
            cycle += 1
            log.info("── Cycle %d ──────────────────────────────────", cycle)

            # 1. Résoudre les ordres expirés / résolus
            reconcile_open_orders()

            # 2. Circuit-breaker
            if check_circuit_breaker():
                log.info("Bot arrêté.")
                break

            # 3. Limite paris simultanés
            if len(open_orders) >= MAX_CONCURRENT:
                log.info("Max simultanés atteint (%d/%d).", len(open_orders), MAX_CONCURRENT)
                time.sleep(SCAN_INTERVAL)
                continue

            # 4. Scanner les marchés
            markets = fetch_active_markets(limit=300)
            if not markets:
                time.sleep(SCAN_INTERVAL)
                continue

            # 5. Évaluer toutes les opportunités
            all_opps = []
            for market in markets:
                all_opps.extend(evaluate_market(market))

            all_opps.sort(key=lambda x: x["edge"], reverse=True)

            if not all_opps:
                log.info("Aucune opportunité (edge > %.2f).", MIN_EDGE)
                print_stats()
                time.sleep(SCAN_INTERVAL)
                continue

            log.info("Opportunités : %d", len(all_opps))
            for o in all_opps[:5]:
                log.info(
                    "  [%s] %s | %s | P=%.3f mkt=%.3f edge=%.3f mise=%.2f$ depth=%.0f$",
                    o["strategy"], o["market_name"][:42], o["outcome"],
                    o["true_prob"], o["market_price"], o["edge"],
                    o["stake"], o["depth"],
                )

            # 6. Parier sur les N meilleures
            slots = MAX_CONCURRENT - len(open_orders)
            for opp in all_opps[:slots]:
                if bankroll < opp["stake"]:
                    log.warning("Bankroll libre insuffisant (%.2f$).", bankroll)
                    break
                oid = place_order(opp)
                if oid:
                    bankroll -= opp["stake"]
                    bankroll_engaged += opp["stake"]
                    bet_market_ids.add(opp["market_id"])
                time.sleep(0.5)

            print_stats()
            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            log.info("Arrêt. P&L final : %.2f$", sum(pnl_history))
            break
        except Exception as exc:
            log.exception("Erreur : %s", exc)
            time.sleep(15)


if __name__ == "__main__":
    main()
