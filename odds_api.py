"""Cliente mínimo da The Odds API v4 (apenas biblioteca padrão)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.the-odds-api.com/v4"
TIMEOUT_SEGUNDOS = 15


class OddsApiError(RuntimeError):
    pass


def _get(path: str, api_key: str, **params) -> tuple[object, dict]:
    if not api_key:
        raise OddsApiError("Define a variável de ambiente ODDS_API_KEY.")
    query = urllib.parse.urlencode({"apiKey": api_key, **params})
    url = f"{BASE_URL}{path}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SEGUNDOS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            restantes = resp.headers.get("x-requests-remaining")
    except urllib.error.HTTPError as exc:
        raise OddsApiError(f"The Odds API respondeu HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise OddsApiError(f"Não foi possível ligar à The Odds API: {exc.reason}") from exc
    return body, {"restantes": restantes}


def list_sports(api_key: str) -> list[dict]:
    """Desportos com temporada ativa. Não gasta quota."""
    body, _ = _get("/sports/", api_key)
    return [s for s in body if s.get("active")]


def fetch_scores(sport: str, api_key: str, dias_atras: int = 3) -> list[dict]:
    """Jogos concluídos nos últimos dias com o resultado. Custa 2 créditos por desporto."""
    body, _ = _get(f"/sports/{sport}/scores/", api_key, daysFrom=dias_atras, dateFormat="iso")
    return body


def fetch_odds(sport: str, api_key: str, regions: str = "eu", markets: str = "h2h") -> tuple[list[dict], dict]:
    """Jogos com odds pré-jogo. Custa 1 crédito por região e mercado."""
    body, meta = _get(
        f"/sports/{sport}/odds/",
        api_key,
        regions=regions,
        markets=markets,
        oddsFormat="decimal",
        dateFormat="iso",
    )
    return body, meta
