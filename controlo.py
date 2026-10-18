"""Estado do modo contínuo (ativo ou em pausa), partilhado entre main.py e servidor.py."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FICHEIRO = RAIZ / "data" / "controlo.json"


def estado(ficheiro: Path = FICHEIRO) -> dict:
    if not ficheiro.exists():
        return {"ativo": True, "ultimo_ciclo": None}
    dados = json.loads(ficheiro.read_text(encoding="utf-8"))
    return {"ativo": bool(dados.get("ativo", True)), "ultimo_ciclo": dados.get("ultimo_ciclo")}


def definir_ativo(ativo: bool, ficheiro: Path = FICHEIRO) -> dict:
    atual = estado(ficheiro)
    atual["ativo"] = bool(ativo)
    _guardar(atual, ficheiro)
    return atual


def registar_ciclo(agora: datetime, ficheiro: Path = FICHEIRO) -> None:
    atual = estado(ficheiro)
    atual["ultimo_ciclo"] = agora.isoformat(timespec="seconds")
    _guardar(atual, ficheiro)


def _guardar(dados: dict, ficheiro: Path) -> None:
    ficheiro.parent.mkdir(exist_ok=True)
    ficheiro.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
