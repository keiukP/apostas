"""Controlo de banca para a simulação. Todo o dinheiro aqui é fictício.

Regras:
- Banca inicial de 100 €.
- Stake de 2% da banca, mínimo 1 €, máximo 5% da banca (o máximo prevalece).
- Stop-loss: sem novos palpites quando a banca cai para 50% da inicial.
- Exposição: a soma dos stakes pendentes não passa de 10% da banca.
"""
from __future__ import annotations

BANCA_INICIAL = 100.0
FRACAO_STAKE = 0.02
FRACAO_STAKE_MAXIMA = 0.05
STAKE_MINIMO = 1.0
FRACAO_STOP_LOSS = 0.5
FRACAO_EXPOSICAO_MAXIMA = 0.10


def stake_para(banca_atual: float) -> float:
    if banca_atual <= 0:
        return 0.0
    stake = max(STAKE_MINIMO, banca_atual * FRACAO_STAKE)
    stake = min(stake, banca_atual * FRACAO_STAKE_MAXIMA)
    return round(stake, 2)


def lucro_palpite(palpite: dict) -> float:
    if palpite["estado"] == "green":
        return round(palpite["stake"] * (palpite["odd"] - 1), 2)
    if palpite["estado"] == "red":
        return -round(palpite["stake"], 2)
    return 0.0


def banca_atual(palpites: list[dict], inicial: float = BANCA_INICIAL) -> float:
    return round(inicial + sum(lucro_palpite(p) for p in palpites), 2)


def exposicao_pendente(palpites: list[dict]) -> float:
    return round(sum(p["stake"] for p in palpites if p["estado"] == "pendente"), 2)


def stop_loss_ativo(banca: float, inicial: float = BANCA_INICIAL) -> bool:
    return banca <= inicial * FRACAO_STOP_LOSS


def pode_apostar(stake: float, banca: float, palpites: list[dict]) -> bool:
    """Confirma que o novo stake cabe na exposição máxima permitida."""
    if stake <= 0 or stop_loss_ativo(banca):
        return False
    return exposicao_pendente(palpites) + stake <= banca * FRACAO_EXPOSICAO_MAXIMA + 1e-9


def curva(palpites: list[dict], inicial: float = BANCA_INICIAL) -> list[tuple[str, float]]:
    """Evolução da banca após cada palpite fechado, por ordem de início do jogo."""
    fechados = sorted(
        (p for p in palpites if p["estado"] in ("green", "red", "void")),
        key=lambda p: p["inicio"],
    )
    saldo = inicial
    pontos = [("início", round(inicial, 2))]
    for palpite in fechados:
        saldo += lucro_palpite(palpite)
        pontos.append((palpite["jogo"], round(saldo, 2)))
    return pontos
