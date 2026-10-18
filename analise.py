"""Matemática de odds: probabilidade implícita, valor esperado, Kelly limitado e backtest.

Nenhuma função garante lucro. Servem para medir se uma estimativa tem vantagem sobre a odd.
"""
from __future__ import annotations


def implied_probs(odds: list[float]) -> list[float]:
    """Probabilidades sem margem da casa (normalizadas pelo overround)."""
    if not odds or any(o <= 1.0 for o in odds):
        raise ValueError("odds decimais devem ser > 1")
    raw = [1.0 / o for o in odds]
    total = sum(raw)
    return [p / total for p in raw]


def expected_value(prob: float, odds: float) -> float:
    """Valor esperado por unidade apostada: p * odd - 1."""
    return prob * odds - 1.0


def kelly_fraction(prob: float, odds: float, cap: float = 0.05) -> float:
    """Fração do bankroll segundo Kelly, limitada a `cap` e nunca negativa."""
    b = odds - 1.0
    if b <= 0:
        return 0.0
    f = (b * prob - (1.0 - prob)) / b
    return max(0.0, min(f, cap))


def find_value_bets(model_probs: dict[str, float], odds: dict[str, float], min_edge: float = 0.03) -> list[dict]:
    """Seleções em que a estimativa supera a probabilidade implícita da odd em `min_edge` ou mais."""
    bets = []
    for selection, prob in model_probs.items():
        if selection not in odds:
            continue
        odd = odds[selection]
        edge = prob - 1.0 / odd
        if edge >= min_edge:
            bets.append({
                "selection": selection,
                "odds": odd,
                "model_prob": round(prob, 4),
                "edge": round(edge, 4),
                "ev": round(expected_value(prob, odd), 4),
                "kelly": round(kelly_fraction(prob, odd), 4),
            })
    return sorted(bets, key=lambda item: item["edge"], reverse=True)


def backtest(bets: list[dict], stake: float = 1.0) -> dict:
    """Resultado de apostas passadas com stake fixa. Cada aposta: {"odds": float, "won": bool}."""
    if not bets:
        return {"n": 0, "staked": 0.0, "profit": 0.0, "roi_pct": None, "hit_rate_pct": None}
    profit = sum(stake * (b["odds"] - 1.0) if b["won"] else -stake for b in bets)
    staked = stake * len(bets)
    wins = sum(1 for b in bets if b["won"])
    return {
        "n": len(bets),
        "staked": round(staked, 2),
        "profit": round(profit, 2),
        "roi_pct": round(profit / staked * 100, 2),
        "hit_rate_pct": round(wins / len(bets) * 100, 2),
    }
