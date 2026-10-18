"""Compara a melhor odd de cada seleção com a probabilidade média do mercado.

Um sinal de valor aparece quando a melhor odd paga mais do que a probabilidade
média (sem margem) das casas sugere. O consenso também erra, por isso isto é
uma medida de desvio do mercado, não uma previsão de resultado.
"""
from __future__ import annotations

from statistics import mean, median

from analise import implied_probs

MIN_VANTAGEM = 0.02
MIN_CASAS = 5
LIMITE_OUTLIER = 1.15


def _precos_h2h(bookmaker: dict) -> dict[str, float]:
    mercado = next((m for m in bookmaker.get("markets", []) if m.get("key") == "h2h"), None)
    if not mercado:
        return {}
    precos = {}
    for outcome in mercado.get("outcomes", []):
        preco = float(outcome.get("price", 0))
        if preco > 1.0:
            precos[outcome["name"]] = preco
    return precos


def analisar_evento(event: dict, min_vantagem: float = MIN_VANTAGEM, min_casas: int = MIN_CASAS) -> dict | None:
    todas = [(bm.get("title", bm.get("key", "?")), _precos_h2h(bm)) for bm in event.get("bookmakers", [])]
    resultados = set()
    for _, precos in todas:
        resultados |= set(precos)
    completas = [(nome, p) for nome, p in todas if resultados and set(p) == resultados]
    if not completas:
        return None

    prob_por_seleccao = {r: [] for r in resultados}
    for _, precos in completas:
        chaves = sorted(precos)
        for chave, prob in zip(chaves, implied_probs([precos[k] for k in chaves])):
            prob_por_seleccao[chave].append(prob)

    selecoes = []
    for seleccao in sorted(resultados):
        precos_todos = [(nome, p[seleccao]) for nome, p in todas if seleccao in p]
        casa, melhor = max(precos_todos, key=lambda item: item[1])
        prob_mercado = mean(prob_por_seleccao[seleccao])
        vantagem = prob_mercado - 1.0 / melhor
        mediana = median(preco for _, preco in precos_todos)
        suspeita = melhor > LIMITE_OUTLIER * mediana
        selecoes.append({
            "seleccao": seleccao,
            "melhor_odd": melhor,
            "casa": casa,
            "prob_mercado": round(prob_mercado, 4),
            "vantagem": round(vantagem, 4),
            "valor": vantagem >= min_vantagem and len(completas) >= min_casas and not suspeita,
            "odd_suspeita": suspeita,
        })
    selecoes.sort(key=lambda s: s["vantagem"], reverse=True)

    return {
        "id": event.get("id", ""),
        "desporto": event.get("sport_key", ""),
        "jogo": f"{event.get('home_team')} vs {event.get('away_team')}",
        "casa_equipa": event.get("home_team", ""),
        "fora_equipa": event.get("away_team", ""),
        "inicio": event.get("commence_time", ""),
        "casas": len(completas),
        "selecoes": selecoes,
    }
