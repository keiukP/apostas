"""Palpites simulados com odds e resultados, atualizados sozinhos.

Exemplos (PowerShell):
  python main.py --listar-desportos
  python main.py --atualizar                  # uma atualização (gasta quota)
  python main.py --continuo --intervalo 360   # fica a atualizar de 6 em 6 horas
  python main.py --site                       # regenera o chat sem gastar quota
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import controlo
import palpites as pal
from chat import html_chat
from odds_api import OddsApiError, fetch_odds, fetch_scores, list_sports
from relatorio import enviar_telegram, html_site, texto_resumo
from valor import analisar_evento

RAIZ = Path(__file__).resolve().parent
PALPITES_FICHEIRO = RAIZ / "data" / "palpites.json"
DESPORTOS_PADRAO = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
]


def _desportos(args) -> list[str]:
    if args.desporto:
        return args.desporto
    env = os.getenv("ODDS_DESPORTOS")
    return [d.strip() for d in env.split(",") if d.strip()] if env else DESPORTOS_PADRAO


def _dia_alvo(args, agora: datetime) -> str:
    if args.dia_jogo:
        return args.dia_jogo.isoformat()
    if args.preparar_amanha:
        return (agora.astimezone(pal.LISBOA).date() + timedelta(days=1)).isoformat()
    return pal.dia_lisboa(agora)


def _guardar_snapshot(desporto: str, dados: list[dict], hoje: str) -> None:
    pasta = RAIZ / "historico"
    pasta.mkdir(exist_ok=True)
    (pasta / f"{hoje}_{desporto}.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def _analises_snapshot(dia: str, desportos: list[str]) -> list[dict]:
    analises = []
    for desporto in desportos:
        caminho = RAIZ / "historico" / f"{dia}_{desporto}.json"
        if caminho.exists():
            eventos = json.loads(caminho.read_text(encoding="utf-8"))
            analises.extend(
                analise
                for analise in (analisar_evento(evento) for evento in eventos)
                if analise
            )
    return analises


def _escrever_site(
    palpites: list[dict],
    seccoes: dict[str, list[dict]],
    hoje: str,
    agora: datetime,
    analises: list[dict] | None = None,
    dia_jogo: str | None = None,
) -> None:
    destino = RAIZ / "site"
    destino.mkdir(exist_ok=True)
    (destino / "index.html").write_text(
        html_chat(palpites, agora, analises=analises, dia_jogo=dia_jogo),
        encoding="utf-8",
    )
    if seccoes:
        (destino / "odds.html").write_text(html_site(seccoes, hoje), encoding="utf-8")
    print(f"Site atualizado em {destino}")


def _ciclo(args, chave: str) -> None:
    agora = datetime.now(timezone.utc)
    hoje = agora.date().isoformat()
    palpites = pal.carregar(PALPITES_FICHEIRO)

    eventos: dict[str, dict] = {}
    for desporto in sorted({p["desporto"] for p in palpites if p["estado"] == "pendente"}):
        for evento in fetch_scores(desporto, chave):
            eventos[evento["id"]] = evento
    fechados = pal.liquidar(palpites, eventos, agora)

    seccoes: dict[str, list[dict]] = {}
    todas: list[dict] = []
    for desporto in _desportos(args):
        dados, meta = fetch_odds(desporto, chave, regions=args.regiao)
        _guardar_snapshot(desporto, dados, hoje)
        analises = [a for a in (analisar_evento(e) for e in dados) if a]
        seccoes[desporto] = analises
        todas.extend(analises)
        print(f"{desporto}: {len(analises)} jogos analisados (quota restante: {meta['restantes']})")

    dia_jogo = _dia_alvo(args, agora)
    novos = pal.registar_do_dia(
        palpites,
        todas,
        hoje,
        agora,
        dia_jogo=dia_jogo,
        estrategia="favorito_mercado",
    )
    pal.guardar(PALPITES_FICHEIRO, palpites)
    print(
        f"Palpites fechados: {fechados} · novos para {dia_jogo} (favorito do mercado): "
        f"{len(novos)} · total: {len(palpites)}"
    )
    _escrever_site(palpites, seccoes, hoje, agora, todas, dia_jogo)

    if args.telegram:
        resumo = texto_resumo(todas, hoje)
        if args.dry_run:
            print(resumo)
        else:
            enviar_telegram(os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", ""), resumo)
            print("Resumo enviado por Telegram.")


def _continuo(args, chave: str) -> None:
    print(f"Modo contínuo: atualiza a cada {args.intervalo} min quando estiver ativo. Ctrl+C para parar.")
    proximo = 0.0
    while True:
        if controlo.estado()["ativo"] and time.time() >= proximo:
            try:
                _ciclo(args, chave)
                controlo.registar_ciclo(datetime.now(timezone.utc))
            except (OddsApiError, RuntimeError) as exc:
                print(f"Erro (nova tentativa no próximo ciclo): {exc}", file=sys.stderr)
            proximo = time.time() + args.intervalo * 60
        time.sleep(5)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Palpites simulados com odds e resultados (informativo).")
    parser.add_argument("--listar-desportos", action="store_true", help="lista desportos ativos (sem gastar quota)")
    parser.add_argument("--desporto", action="append", help="chave do desporto; pode repetir")
    parser.add_argument("--regiao", default="eu", help="regiões de casas, ex.: eu, uk")
    grupo_dia = parser.add_mutually_exclusive_group()
    grupo_dia.add_argument(
        "--dia-jogo",
        type=date.fromisoformat,
        help="regista propostas para esta data em Lisboa (AAAA-MM-DD); por omissão, hoje",
    )
    grupo_dia.add_argument(
        "--preparar-amanha",
        action="store_true",
        help="prepara dinamicamente o dia seguinte em Lisboa (útil em modo contínuo)",
    )
    parser.add_argument("--atualizar", action="store_true", help="fecha resultados, busca odds, regista palpites e gera o site")
    parser.add_argument("--continuo", action="store_true", help="repete --atualizar a cada --intervalo minutos")
    parser.add_argument("--intervalo", type=int, default=360, help="minutos entre atualizações com --continuo")
    parser.add_argument("--site", action="store_true", help="regenera o chat a partir de data/palpites.json, sem API")
    parser.add_argument("--telegram", action="store_true", help="envia o resumo de sinais por Telegram")
    parser.add_argument("--dry-run", action="store_true", help="mostra o resumo do Telegram sem enviar")
    args = parser.parse_args(argv)

    chave = os.getenv("ODDS_API_KEY", "")
    if args.listar_desportos:
        try:
            for s in list_sports(chave):
                print(f"{s['key']:35} {s['title']}")
            return 0
        except OddsApiError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            return 1

    if not (args.atualizar or args.continuo):
        if args.site:
            agora = datetime.now(timezone.utc)
            hoje = agora.date().isoformat()
            dia_jogo = _dia_alvo(args, agora)
            analises = _analises_snapshot(hoje, _desportos(args))
            _escrever_site(
                pal.carregar(PALPITES_FICHEIRO),
                {},
                hoje,
                agora,
                analises,
                dia_jogo,
            )
            return 0
        parser.print_help()
        return 0

    if not chave:
        print("Erro: define ODDS_API_KEY no ambiente (não a guardes em ficheiros).", file=sys.stderr)
        return 1
    try:
        if args.continuo:
            _continuo(args, chave)
        else:
            _ciclo(args, chave)
            controlo.registar_ciclo(datetime.now(timezone.utc))
    except KeyboardInterrupt:
        print("Parado.")
    except (OddsApiError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
