"""Registo de palpites com fecho pelos resultados oficiais.

Cada palpite é guardado antes do início do jogo e fica pendente até haver
resultado. Depois é marcado como green (ganhou), red (perdeu) ou void (sem
resultado válido). Cada palpite vale 1 unidade de stake.

Os palpites são seleções com sinal de valor, não garantias. Não há limite
de lucro: o histórico mostra a taxa real, incluindo as perdas.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import banca as b
from valor import MIN_CASAS

LISBOA = ZoneInfo("Europe/Lisbon")
MAX_POR_DIA = 5
UNIDADE = 1.0
EMPATE = "Draw"
DIAS_SEM_RESULTADO = 4


class PalpiteInvalido(ValueError):
    pass


def carregar(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    return json.loads(caminho.read_text(encoding="utf-8"))


def guardar(caminho: Path, palpites: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(palpites, ensure_ascii=False, indent=2), encoding="utf-8")


def _inicio(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def dia_lisboa(instante: str | datetime) -> str:
    """Data (AAAA-MM-DD) de um instante no fuso de Lisboa."""
    if isinstance(instante, str):
        instante = _inicio(instante)
    return instante.astimezone(LISBOA).date().isoformat()


def registar_do_dia(
    palpites: list[dict],
    analises: list[dict],
    dia: str,
    agora: datetime | None = None,
    limite: int = MAX_POR_DIA,
    dia_jogo: str | None = None,
    estrategia: Literal["valor", "favorito_mercado"] = "valor",
) -> list[dict]:
    """Regista seleções simuladas de uma estratégia, até ao limite diário.

    Só entram jogos cujo início cai em `dia_jogo` (hora de Lisboa; por omissão,
    `dia`). `valor` usa apenas sinais que passam os critérios; `favorito_mercado`
    escolhe a maior probabilidade média, com odds completas de pelo menos
    MIN_CASAS e sem odd suspeita. Ignora jogos iniciados e duplicados.
    """
    if estrategia not in ("valor", "favorito_mercado"):
        raise ValueError(f"estratégia desconhecida: {estrategia}")
    agora = agora or datetime.now(timezone.utc)
    dia_jogo = dia_jogo or dia
    ja_no_dia = sum(1 for p in palpites if dia_lisboa(p["inicio"]) == dia_jogo)
    existentes = {(p["id"], p["seleccao"]) for p in palpites}
    jogos_existentes = {p["id"] for p in palpites if dia_lisboa(p["inicio"]) == dia_jogo}

    candidatos = []
    for analise in analises:
        if dia_lisboa(analise["inicio"]) != dia_jogo:
            continue
        if estrategia == "valor":
            candidatos.extend((analise, sel) for sel in analise["selecoes"] if sel["valor"])
            continue
        if analise.get("casas", 0) < MIN_CASAS or analise["id"] in jogos_existentes:
            continue
        elegiveis = [sel for sel in analise["selecoes"] if not sel.get("odd_suspeita", False)]
        if elegiveis:
            favoritos = max(elegiveis, key=lambda sel: sel["prob_mercado"])
            candidatos.append((analise, favoritos))

    chave_ordem = "vantagem" if estrategia == "valor" else "prob_mercado"
    candidatos.sort(key=lambda par: par[1][chave_ordem], reverse=True)

    novos = []
    for analise, sel in candidatos:
        if ja_no_dia + len(novos) >= limite:
            break
        if (analise["id"], sel["seleccao"]) in existentes:
            continue
        if estrategia == "favorito_mercado" and analise["id"] in jogos_existentes:
            continue
        if _inicio(analise["inicio"]) <= agora:
            continue
        banca_agora = b.banca_atual(palpites)
        stake = b.stake_para(banca_agora)
        if not b.pode_apostar(stake, banca_agora, palpites + novos):
            break
        novo = {
            "id": analise["id"],
            "desporto": analise["desporto"],
            "jogo": analise["jogo"],
            "inicio": analise["inicio"],
            "casa_equipa": analise["casa_equipa"],
            "fora_equipa": analise["fora_equipa"],
            "seleccao": sel["seleccao"],
            "odd": sel["melhor_odd"],
            "casa_apostas": sel["casa"],
            "prob_mercado": sel["prob_mercado"],
            "vantagem": sel["vantagem"],
            "metodo": estrategia,
            "data_registo": dia,
            "estado": "pendente",
            "vencedor": None,
            "stake": stake,
            "registado_em": agora.isoformat(timespec="minutes"),
            "fechado_em": None,
        }
        novos.append(novo)
        existentes.add((analise["id"], sel["seleccao"]))
        jogos_existentes.add(analise["id"])
    palpites.extend(novos)
    return novos


def vencedor(evento: dict) -> str | None:
    """Seleção vencedora de um jogo concluído, ou None se não houver resultado válido."""
    if not evento.get("completed"):
        return None
    try:
        pontos = {s["name"]: int(s["score"]) for s in (evento.get("scores") or []) if s.get("score") not in (None, "")}
    except (KeyError, TypeError, ValueError):
        return None
    casa, fora = evento.get("home_team"), evento.get("away_team")
    if casa not in pontos or fora not in pontos:
        return None
    if pontos[casa] > pontos[fora]:
        return casa
    if pontos[fora] > pontos[casa]:
        return fora
    return EMPATE


def liquidar(palpites: list[dict], eventos: dict[str, dict], agora: datetime | None = None) -> int:
    """Fecha os palpites pendentes. Devolve quantos fechou.

    Fecha com green/red quando há resultado. Anula (void) quando, passados
    DIAS_SEM_RESULTADO desde o início, ainda não há resultado.
    """
    agora = agora or datetime.now(timezone.utc)
    fechados = 0
    for palpite in palpites:
        if palpite["estado"] != "pendente":
            continue
        evento = eventos.get(palpite["id"])
        if evento and evento.get("completed"):
            resultado = vencedor(evento)
        elif agora - _inicio(palpite["inicio"]) > timedelta(days=DIAS_SEM_RESULTADO):
            resultado = None
        else:
            continue
        palpite["vencedor"] = resultado
        palpite["fechado_em"] = agora.isoformat(timespec="minutes")
        if resultado is None:
            palpite["estado"] = "void"
        elif resultado == palpite["seleccao"]:
            palpite["estado"] = "green"
        else:
            palpite["estado"] = "red"
        fechados += 1
    return fechados


def resumo(palpites: list[dict]) -> dict:
    fechados = [p for p in palpites if p["estado"] in ("green", "red")]
    greens = sum(1 for p in fechados if p["estado"] == "green")
    lucro = sum((p["odd"] - 1) * UNIDADE if p["estado"] == "green" else -UNIDADE for p in fechados)
    apostado = len(fechados) * UNIDADE
    return {
        "total": len(palpites),
        "pendentes": sum(1 for p in palpites if p["estado"] == "pendente"),
        "green": greens,
        "red": len(fechados) - greens,
        "void": sum(1 for p in palpites if p["estado"] == "void"),
        "taxa_acerto": greens / len(fechados) if fechados else None,
        "lucro_unidades": round(lucro, 2),
        "roi": lucro / apostado if apostado else None,
    }
