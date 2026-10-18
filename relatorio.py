"""Gera o texto diário, a página HTML e envia o resumo por Telegram."""
from __future__ import annotations

import html
import json
import urllib.error
import urllib.request

TELEGRAM_LIMITE = 4000

AVISO = (
    "Informação estatística, não é recomendação nem garantia de lucro. "
    "O consenso de mercado também erra. Joga só com dinheiro que podes perder "
    "e apenas em operadores licenciados pelo SRIJ."
)


def _data_curta(inicio: str) -> str:
    return inicio[:16].replace("T", " ") if inicio else "?"


def sinais_de_valor(analises: list[dict]) -> list[tuple[dict, dict]]:
    pares = []
    for analise in analises:
        for selecao in analise["selecoes"]:
            if selecao["valor"]:
                pares.append((analise, selecao))
    return sorted(pares, key=lambda par: par[1]["vantagem"], reverse=True)


def texto_resumo(analises: list[dict], data: str, max_linhas: int = 15) -> str:
    sinais = sinais_de_valor(analises)
    linhas = [f"Sinais de valor - {data}", ""]
    if not sinais:
        linhas.append("Hoje nenhuma seleção ficou acima do limiar de vantagem com casas suficientes.")
    for analise, sel in sinais[:max_linhas]:
        linhas.append(
            f"{analise['jogo']} ({_data_curta(analise['inicio'])})\n"
            f"  {sel['seleccao']} @ {sel['melhor_odd']:.2f} ({sel['casa']})"
            f" | mercado {sel['prob_mercado'] * 100:.1f}%"
            f" | vantagem {sel['vantagem'] * 100:+.1f} pp"
        )
    linhas += ["", AVISO]
    return "\n".join(linhas)[:TELEGRAM_LIMITE]


NOMES_LIGAS = {
    "soccer_epl": "Premier League",
    "soccer_spain_la_liga": "La Liga",
    "soccer_italy_serie_a": "Serie A",
    "soccer_germany_bundesliga": "Bundesliga",
    "soccer_france_ligue_one": "Ligue 1",
    "soccer_uefa_champs_league": "Liga dos Campeões",
}

_CSS = """
:root{--fundo:#0e1013;--cartao:#161920;--linha:#242832;--texto:#d7dce2;--muted:#7d8592;--ouro:#d9a94e;--verde:#4fbf86}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);font:15px/1.5 'Segoe UI',system-ui,sans-serif}
.topo{display:flex;justify-content:space-between;align-items:center;padding:1rem 2rem;border-bottom:1px solid var(--linha)}
.marca{font-weight:600;color:#fff;letter-spacing:.02em}
.fonte{font-size:.8rem;color:var(--muted)}
main{max-width:1100px;margin:0 auto;padding:2.5rem 1.5rem 4rem}
.resumo{margin-bottom:2.5rem}
.data{margin:0;color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}
h1{font-size:1.9rem;font-weight:500;color:#fff;margin:.3rem 0}
.contagem{color:var(--muted);margin:0 0 1.2rem}
.aviso{font-size:.85rem;color:var(--muted);border-left:2px solid var(--ouro);padding:.2rem 0 .2rem 1rem;margin:0;max-width:720px}
h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.12em;color:var(--ouro);font-weight:600;margin:0 0 1rem}
.bloco{margin-bottom:3rem}
.alertas{list-style:none;margin:0;padding:0;background:var(--cartao);border:1px solid var(--linha);border-radius:10px}
.alertas li{display:grid;grid-template-columns:1fr 2fr auto auto;gap:1rem;align-items:center;padding:.85rem 1.1rem;border-bottom:1px solid var(--linha)}
.alertas li:last-child{border-bottom:0}
.alertas .nome{color:#fff;font-weight:600}
.alertas .jogo{color:var(--muted);font-size:.9rem}
.alertas .odd{color:#fff;font-weight:600;font-variant-numeric:tabular-nums}
.alertas .vant{color:var(--verde);font-size:.85rem;font-variant-numeric:tabular-nums}
.liga{margin-bottom:2.5rem}
.grelha{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem}
.cartao{background:var(--cartao);border:1px solid var(--linha);border-radius:10px;padding:1rem 1.1rem}
.cartao header{margin-bottom:.8rem}
.hora{font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums}
.cartao h3{margin:.2rem 0 0;font-size:1rem;font-weight:500;color:#fff}
.opcoes{display:grid;gap:.45rem}
.opcao{display:grid;grid-template-columns:1fr auto;column-gap:.8rem;padding:.55rem .75rem;border-radius:7px;background:#1b1e26;border:1px solid transparent}
.opcao .nome{grid-column:1;grid-row:1;font-size:.92rem}
.opcao .meta{grid-column:1;grid-row:2;font-size:.78rem;color:var(--muted)}
.opcao .odd{grid-column:2;grid-row:1/3;align-self:center;font-weight:600;font-variant-numeric:tabular-nums;color:#fff;font-size:1.05rem}
.opcao.valor{border-color:var(--ouro);background:#22201a}
.opcao.valor .meta{color:var(--ouro)}
.vazio{color:var(--muted)}
@media (max-width:640px){
.topo{padding:.9rem 1rem}
.alertas li{grid-template-columns:1fr auto}
.alertas .jogo{grid-column:1/-1;order:3}
}
"""


def nome_selecao(seleccao: str) -> str:
    return "Empate" if seleccao == "Draw" else seleccao


def _cartao(analise: dict) -> str:
    opcoes = []
    for sel in analise["selecoes"]:
        classe = "opcao valor" if sel["valor"] else "opcao"
        meta = f"{sel['casa']} · {sel['vantagem'] * 100:+.1f} pp"
        if sel.get("odd_suspeita"):
            meta += " · odd suspeita"
        opcoes.append(
            f"<div class=\"{classe}\">"
            f"<span class=\"nome\">{html.escape(nome_selecao(sel['seleccao']))}</span>"
            f"<span class=\"odd\">{sel['melhor_odd']:.2f}</span>"
            f"<span class=\"meta\">{html.escape(meta)}</span>"
            "</div>"
        )
    return (
        "<article class=\"cartao\">"
        f"<header><span class=\"hora\">{html.escape(_data_curta(analise['inicio']))} UTC</span>"
        f"<h3>{html.escape(analise['jogo'])}</h3></header>"
        f"<div class=\"opcoes\">{''.join(opcoes)}</div>"
        "</article>"
    )


def _liga(desporto: str, analises: list[dict]) -> str:
    cartoes = "".join(_cartao(a) for a in analises)
    nome = NOMES_LIGAS.get(desporto, desporto)
    return f"<section class=\"liga\"><h2>{html.escape(nome)}</h2><div class=\"grelha\">{cartoes}</div></section>"


def _alertas(todas: list[dict]) -> str:
    pares = sinais_de_valor(todas)
    if not pares:
        return "<p class=\"vazio\">Hoje nenhuma seleção ultrapassou o limiar de vantagem.</p>"
    itens = "".join(
        "<li>"
        f"<span class=\"nome\">{html.escape(nome_selecao(sel['seleccao']))}</span>"
        f"<span class=\"jogo\">{html.escape(analise['jogo'])}</span>"
        f"<span class=\"odd\">{sel['melhor_odd']:.2f}</span>"
        f"<span class=\"vant\">{sel['vantagem'] * 100:+.1f} pp</span>"
        "</li>"
        for analise, sel in pares
    )
    return f"<ul class=\"alertas\">{itens}</ul>"


def html_site(seccoes: dict[str, list[dict]], data: str) -> str:
    todas = [a for analises in seccoes.values() for a in analises]
    ligas = [(d, a) for d, a in seccoes.items() if a]
    corpo_ligas = "".join(_liga(d, a) for d, a in ligas) or "<p class=\"vazio\">Sem jogos com odds disponíveis.</p>"
    return (
        "<!doctype html><html lang=\"pt-PT\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Odds e sinais de valor</title>"
        f"<style>{_CSS}</style></head><body>"
        "<header class=\"topo\"><span class=\"marca\">Odds &amp; Valor</span>"
        "<span class=\"fonte\">Dados: The Odds API</span></header>"
        "<main>"
        "<section class=\"resumo\">"
        f"<p class=\"data\">{html.escape(data)}</p>"
        "<h1>Sinais de valor de hoje</h1>"
        f"<p class=\"contagem\">{len(todas)} jogos · {len(sinais_de_valor(todas))} sinais de valor"
        f" · {len(ligas)} ligas</p>"
        f"<p class=\"aviso\">{html.escape(AVISO)}</p>"
        "</section>"
        f"<section class=\"bloco\"><h2>Alertas</h2>{_alertas(todas)}</section>"
        f"<section class=\"bloco\">{corpo_ligas}</section>"
        "</main></body></html>"
    )


def enviar_telegram(token: str, chat_id: str, texto: str, timeout: int = 15) -> dict:
    if not token or not chat_id:
        raise RuntimeError("Define TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no ambiente.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    corpo = json.dumps({"chat_id": chat_id, "text": texto[:TELEGRAM_LIMITE]}).encode("utf-8")
    pedido = urllib.request.Request(url, data=corpo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Telegram respondeu HTTP {exc.code}") from exc
