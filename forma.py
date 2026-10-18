"""Forma recente: últimos 5 jogos de cada equipa, com fonte verificável.

A API de odds não tem histórico de jogos, por isso estes dados vêm de
`data/forma.json`. Cada jogo precisa de data, mando, golos e um link https
da fonte. Registos incompletos são rejeitados, nunca estimados.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

JANELA = 5
PONTOS = {"V": 3, "E": 1, "D": 0}
CAMPOS = ("data", "local", "adversario", "golos_marcados", "golos_sofridos", "fonte")
AVISO_AMOSTRA = "Amostra de 5 jogos: indicador fraco, não é previsão."


class FormaInvalida(ValueError):
    pass


def validar_jogo(jogo: dict) -> None:
    faltam = [c for c in CAMPOS if jogo.get(c) in (None, "")]
    if faltam:
        raise FormaInvalida(f"jogo sem campos {faltam}")
    try:
        date.fromisoformat(jogo["data"])
    except (TypeError, ValueError) as exc:
        raise FormaInvalida(f"data inválida: {jogo['data']}") from exc
    if jogo["local"] not in ("C", "F"):
        raise FormaInvalida("local deve ser C (casa) ou F (fora)")
    for campo in ("golos_marcados", "golos_sofridos"):
        valor = jogo[campo]
        if not isinstance(valor, int) or isinstance(valor, bool) or valor < 0:
            raise FormaInvalida(f"{campo} deve ser inteiro >= 0")
    if not str(jogo["fonte"]).startswith("https://"):
        raise FormaInvalida("fonte deve ser um link https")


def _resultado(jogo: dict) -> str:
    if jogo["golos_marcados"] > jogo["golos_sofridos"]:
        return "V"
    if jogo["golos_marcados"] == jogo["golos_sofridos"]:
        return "E"
    return "D"


def resumo_equipa(jogos: list[dict]) -> dict:
    """Resume exatamente JANELA jogos válidos, do mais recente para o mais antigo."""
    if len(jogos) != JANELA:
        raise FormaInvalida(f"são precisos {JANELA} jogos, há {len(jogos)}")
    for jogo in jogos:
        validar_jogo(jogo)
    if len({(j["data"], j["adversario"]) for j in jogos}) != JANELA:
        raise FormaInvalida("jogos duplicados")
    recentes = sorted(jogos, key=lambda j: j["data"], reverse=True)
    resultados = [_resultado(j) for j in recentes]
    em_casa = [j for j in recentes if j["local"] == "C"]
    fora = [j for j in recentes if j["local"] == "F"]
    return {
        "sequencia": "".join(resultados),
        "pontos": sum(PONTOS[r] for r in resultados),
        "marcados_media": sum(j["golos_marcados"] for j in recentes) / JANELA,
        "sofridos_media": sum(j["golos_sofridos"] for j in recentes) / JANELA,
        "mais_de_2_5": sum(1 for j in recentes if j["golos_marcados"] + j["golos_sofridos"] > 2) / JANELA,
        "ambas_marcam": sum(1 for j in recentes if j["golos_marcados"] > 0 and j["golos_sofridos"] > 0) / JANELA,
        "sem_sofrer": sum(1 for j in recentes if j["golos_sofridos"] == 0) / JANELA,
        "pontos_casa": sum(PONTOS[_resultado(j)] for j in em_casa),
        "jogos_casa": len(em_casa),
        "pontos_fora": sum(PONTOS[_resultado(j)] for j in fora),
        "jogos_fora": len(fora),
        "fontes": sorted({j["fonte"] for j in recentes}),
    }


def carregar_forma(caminho: Path) -> dict[str, list[dict]]:
    """Lê `{"equipas": {"Nome": [jogos...]}}`. Ficheiro inexistente devolve {}."""
    if not caminho.exists():
        return {}
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    equipas = dados.get("equipas", {})
    for nome, jogos in equipas.items():
        try:
            resumo_equipa(jogos)
        except FormaInvalida as exc:
            raise FormaInvalida(f"{nome}: {exc}") from exc
    return equipas


def _percentagem(valor: float) -> str:
    return f"{valor * 100:.0f}%"


def analisar_confronto(casa: str, fora: str, equipas: dict[str, list[dict]]) -> dict | None:
    """Devolve as linhas de análise, ou None se alguma equipa não tem dados válidos."""
    if casa not in equipas or fora not in equipas:
        return None
    rc = resumo_equipa(equipas[casa])
    rf = resumo_equipa(equipas[fora])
    diferenca = rc["pontos"] - rf["pontos"]
    if diferenca >= 4:
        leitura = f"A forma favorece {casa}."
    elif diferenca <= -4:
        leitura = f"A forma favorece {fora}."
    else:
        leitura = "Forma equilibrada entre as duas equipas."
    linhas = [
        f"Forma: {casa} {rc['pontos']}/15 ({rc['sequencia']}) · {fora} {rf['pontos']}/15 ({rf['sequencia']})",
        f"Casa de {casa}: {rc['pontos_casa']} pts em {rc['jogos_casa']} jogos · "
        f"fora de {fora}: {rf['pontos_fora']} pts em {rf['jogos_fora']} jogos",
        f"Golos médios: {casa} marca {rc['marcados_media']:.1f} e sofre {rc['sofridos_media']:.1f} · "
        f"{fora} marca {rf['marcados_media']:.1f} e sofre {rf['sofridos_media']:.1f}",
        f"Mais de 2,5 golos: {casa} {_percentagem(rc['mais_de_2_5'])} · {fora} {_percentagem(rf['mais_de_2_5'])}",
        f"Ambas marcam: {casa} {_percentagem(rc['ambas_marcam'])} · {fora} {_percentagem(rf['ambas_marcam'])}",
        leitura,
        AVISO_AMOSTRA,
    ]
    return {
        "casa": casa,
        "fora": fora,
        "linhas": linhas,
        "fontes": sorted(set(rc["fontes"]) | set(rf["fontes"])),
    }
