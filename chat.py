"""Página em formato de conversa com os palpites simulados.

Cada palpite aparece como proposta e, quando fecha, como GREEN, RED ou VOID.
O dinheiro é fictício: a banca começa em banca.BANCA_INICIAL.
"""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone

import banca as b
import palpites as pal
from palpites import MAX_POR_DIA
from relatorio import AVISO, NOMES_LIGAS, nome_selecao

ATRASO_ENTRE_MENSAGENS = 0.35
ATRASO_MAXIMO = 12.0
DIA_INICIO_TESTE = "2026-10-19"
DIAS_TESTE = 30

SIMULACAO = (
    f"Dinheiro fictício: banca inicial de {b.BANCA_INICIAL:.0f} €. "
    "Estes palpites acompanham o método em simulação, não são apostas reais."
)

_RESULTADOS = {
    "green": ("✅", "GREEN", "ganhou"),
    "red": ("❌", "RED", "não ganhou"),
    "void": ("⚪", "VOID", "sem resultado válido"),
}

_CSS = """
:root{color-scheme:dark;--fundo:#0b0e13;--cartao:#141922;--linha:#27303b;--texto:#e1e7ef;--muted:#8994a3;--ouro:#e0b15c;--verde:#56d69a;--vermelho:#f07878;--azul:#79bfff}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 12% -10%,rgba(44,82,105,.3),transparent 42%),radial-gradient(ellipse at 90% 10%,rgba(103,73,34,.16),transparent 34%),var(--fundo);color:var(--texto);font:15px/1.5 'Segoe UI',system-ui,sans-serif;min-height:100vh}
.topo{display:flex;justify-content:space-between;align-items:center;padding:.9rem max(1rem,calc((100vw - 980px)/2));border-bottom:1px solid rgba(137,148,163,.16);background:rgba(11,14,19,.78);backdrop-filter:blur(16px)}
.marca{font-weight:700;color:#fff;letter-spacing:.025em}
.marca small{margin-left:.45rem;color:var(--ouro);font-size:.68rem;font-weight:600;letter-spacing:.12em}
.topo a{color:var(--muted);font-size:.85rem;text-decoration:none}
.topo a:hover{color:var(--ouro)}
.painel{position:sticky;top:0;z-index:2;background:rgba(11,14,19,.82);border-bottom:1px solid rgba(137,148,163,.16);backdrop-filter:blur(18px)}
.painel-grelha{max-width:980px;margin:0 auto;padding:.85rem 1.5rem;display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:.65rem}
.indicador{position:relative;overflow:hidden;background:linear-gradient(145deg,rgba(25,32,43,.95),rgba(18,23,31,.92));border:1px solid var(--linha);border-radius:13px;padding:.65rem .8rem;box-shadow:0 8px 26px rgba(0,0,0,.14);transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease}
.indicador:hover{transform:translateY(-2px);border-color:#435164;box-shadow:0 12px 30px rgba(0,0,0,.22)}
.indicador span{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.indicador strong{display:block;font-size:1.38rem;font-weight:650;color:#fff;font-variant-numeric:tabular-nums;letter-spacing:-.025em}
.indicador.verde strong{color:var(--verde)}
.indicador.vermelho strong{color:var(--vermelho)}
.indicador small{display:block;font-size:.75rem;color:var(--muted)}
.indicador.banca{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.8rem 1rem;background:linear-gradient(100deg,rgba(27,38,49,.96),rgba(20,25,34,.96))}
.indicador.banca strong{font-size:1.75rem}
.indicador.profit{border-color:rgba(86,214,154,.3);background:linear-gradient(135deg,rgba(23,48,42,.88),rgba(18,27,31,.96))}
.indicador.profit:after{content:"";position:absolute;width:95px;height:95px;right:-40px;top:-45px;border-radius:50%;background:rgba(86,214,154,.12);filter:blur(4px);animation:respirar 4s ease-in-out infinite}
.indicador.profit>*{position:relative;z-index:1}
.indicador.profit.positivo strong{color:var(--verde)}
.indicador.profit.negativo{border-color:rgba(240,120,120,.35);background:linear-gradient(135deg,rgba(55,33,38,.9),rgba(23,25,33,.96))}
.indicador.profit.negativo:after{background:rgba(240,120,120,.13)}
.indicador.profit.negativo strong{color:var(--vermelho)}
.indicador.profit.neutro strong{color:#fff}
.indicador strong{white-space:nowrap}
.alerta{max-width:980px;margin:.6rem auto 0;padding:.5rem .8rem;border-left:2px solid var(--vermelho);color:var(--vermelho);font-size:.85rem}
main.chat{max-width:680px;margin:0 auto;padding:2rem 1.5rem 4rem}
.feed{display:flex;flex-direction:column;gap:.9rem}
.grupo-historico{padding:1.15rem;border:1px solid rgba(137,148,163,.16);border-radius:18px;background:rgba(17,22,30,.58);box-shadow:0 16px 38px rgba(0,0,0,.14)}
.cabecalho-grupo{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:0 0 .9rem}
.cabecalho-grupo h2{margin:0;color:#fff;font-size:1.05rem;letter-spacing:-.02em}
.cabecalho-grupo p{margin:.1rem 0 0;color:var(--muted);font-size:.78rem}
.resumo-grupo{flex-shrink:0;color:var(--azul);font-size:.82rem;font-weight:650;font-variant-numeric:tabular-nums}
.lista-grupo{display:flex;flex-direction:column;gap:.75rem}
.mensagem-grupo{padding:.25rem 0;color:var(--muted);font-size:.88rem}
.msg{opacity:0;animation:entrar .5s ease forwards}
.msg.res{padding-left:1.1rem}
.balao{background:linear-gradient(145deg,rgba(23,29,39,.98),rgba(17,22,30,.98));border:1px solid var(--linha);border-radius:16px 16px 16px 5px;padding:1rem 1.1rem;max-width:560px;box-shadow:0 12px 32px rgba(0,0,0,.16)}
.msg.pendente .balao{border-left:3px solid var(--azul)}
.msg.green .balao{border-color:rgba(86,214,154,.65);box-shadow:0 0 24px rgba(86,214,154,.08)}
.msg.red .balao{border-color:rgba(240,120,120,.65);box-shadow:0 0 24px rgba(240,120,120,.08)}
.msg.void .balao{border-color:rgba(137,148,163,.5)}
.balao p{margin:.2rem 0}
.etiqueta{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ouro)}
.msg.pendente .etiqueta{color:var(--azul)}
.msg.green .etiqueta{color:var(--verde)}
.msg.red .etiqueta{color:var(--vermelho)}
.estado-resultado{display:inline-flex;align-items:center;gap:.4rem;margin:.3rem 0 .5rem;padding:.2rem .6rem;border:1px solid currentColor;border-radius:999px;font-size:.76rem;font-weight:750;letter-spacing:.04em}
.msg.green .estado-resultado{color:var(--verde);background:rgba(86,214,154,.08)}
.msg.red .estado-resultado{color:var(--vermelho);background:rgba(240,120,120,.08)}
.msg.void .estado-resultado{color:var(--muted);background:rgba(137,148,163,.08)}
.jogo{color:#fff;font-weight:500}
.hora,.linha{font-size:.82rem;color:var(--muted)}
.aposta{display:flex;justify-content:space-between;align-items:center;margin:.6rem 0;padding:.5rem .75rem;border-radius:8px;background:#1b1e26}
.valor-espera{display:flex;align-items:center;justify-content:space-between;gap:.8rem;margin:.65rem 0;padding:.65rem .8rem;border:1px solid rgba(121,191,255,.22);border-radius:10px;background:rgba(121,191,255,.06)}
.valor-espera span{color:var(--muted);font-size:.8rem}
.valor-espera strong{color:var(--azul);font-size:1rem;font-variant-numeric:tabular-nums}
.resultado-valores{display:flex;justify-content:space-between;gap:1rem;margin-top:.65rem;padding-top:.65rem;border-top:1px solid var(--linha)}
.resultado-valores span{display:block;color:var(--muted);font-size:.75rem}
.resultado-valores strong{display:block;color:#fff;font-variant-numeric:tabular-nums}
.resultado-valores .positivo{color:var(--verde)}
.resultado-valores .negativo{color:var(--vermelho)}
.aposta span:first-child{color:#fff}
.odd{font-weight:700;color:#fff;font-variant-numeric:tabular-nums}
.lucro{font-weight:600;color:#fff;font-variant-numeric:tabular-nums}
.vazio{color:var(--muted);text-align:center}
.aviso{font-size:.8rem;color:var(--muted);background:rgba(20,25,34,.84);border:1px solid var(--linha);border-left:3px solid var(--ouro);border-radius:12px;padding:.8rem 1rem;margin:2.5rem 0 0}
.analise{max-width:620px;border-left:3px solid var(--ouro);border-radius:12px}
.lista-analise{margin:.6rem 0 0;padding-left:1.2rem;color:var(--muted);font-size:.82rem}
.lista-analise li{margin:.55rem 0}
.linha-analise{display:flex;flex-direction:column;gap:.22rem}
.estado-aposta{display:inline-flex;width:max-content;align-items:center;padding:.12rem .45rem;border:1px solid rgba(121,191,255,.35);border-radius:999px;color:var(--azul);font-size:.68rem;font-weight:750;letter-spacing:.04em}
.sem-aposta{display:flex;flex-direction:column;gap:.08rem;color:var(--muted);font-size:.77rem}
.sem-aposta strong{color:var(--vermelho);font-size:.68rem;letter-spacing:.07em}
.selecao-aposta small{display:block;margin-bottom:.1rem;color:var(--azul);font-size:.65rem;font-weight:750;letter-spacing:.08em}
.selecao-aposta strong{color:#fff}
.odd small{display:block;color:var(--muted);font-size:.6rem;font-weight:600}
@keyframes entrar{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.controlo{max-width:980px;margin:.8rem auto 0;padding:0 1.5rem;display:flex;align-items:center;gap:.8rem;flex-wrap:wrap;font-size:.85rem;color:var(--muted)}
.controlo button{background:linear-gradient(120deg,#202833,#171d26);color:#fff;border:1px solid rgba(224,177,92,.65);border-radius:999px;padding:.52rem 1rem;font:inherit;font-weight:600;cursor:pointer;transition:transform .2s ease,box-shadow .2s ease}
.controlo button:hover{transform:translateY(-1px);box-shadow:0 6px 22px rgba(224,177,92,.14)}
.controlo button[data-ativo="0"]{border-color:var(--muted)}
.estado-chip{display:inline-flex;align-items:center;gap:.45rem}
.estado-chip:before{content:"";width:8px;height:8px;border-radius:50%;background:var(--muted);box-shadow:0 0 0 4px rgba(137,148,163,.1)}
.estado-chip[data-ativo="1"]:before{background:var(--verde);box-shadow:0 0 0 4px rgba(86,214,154,.12),0 0 12px rgba(86,214,154,.45)}
@keyframes respirar{0%,100%{transform:scale(.92);opacity:.7}50%{transform:scale(1.08);opacity:1}}
.topo .marca{background:linear-gradient(90deg,#fff,var(--ouro));-webkit-background-clip:text;background-clip:text;color:transparent;font-size:1.05rem}
.desafio{max-width:980px;margin:1rem auto 0;padding:1.1rem 1.3rem;border:1px solid rgba(224,177,92,.35);border-radius:18px;background:linear-gradient(120deg,rgba(52,41,22,.55),rgba(17,22,30,.9));box-shadow:0 18px 44px rgba(0,0,0,.2)}
.desafio-topo{display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;flex-wrap:wrap}
.desafio h2{margin:0;font-size:1.15rem;color:#fff;letter-spacing:-.02em}
.desafio h2 em{font-style:normal;color:var(--ouro)}
.desafio p{margin:.15rem 0 0;color:var(--muted);font-size:.8rem}
.desafio-lucro{text-align:right;font-variant-numeric:tabular-nums}
.desafio-lucro strong{display:block;font-size:1.6rem;color:#fff;letter-spacing:-.03em}
.desafio-lucro strong.positivo{color:var(--verde)}
.desafio-lucro strong.negativo{color:var(--vermelho)}
.desafio-lucro span{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.barra{height:6px;margin:.9rem 0 .7rem;border-radius:999px;background:rgba(137,148,163,.18);overflow:hidden}
.barra i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--ouro),var(--verde));box-shadow:0 0 14px rgba(224,177,92,.5)}
.dias{display:grid;grid-template-columns:repeat(15,minmax(0,1fr));gap:.3rem}
.dia{position:relative;aspect-ratio:1;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--linha);background:rgba(20,25,34,.8);color:var(--muted);font-size:.68rem;font-weight:650;cursor:default;transition:transform .15s ease}
.dia:hover{transform:translateY(-2px) scale(1.08);z-index:1}
.dia.verde{background:rgba(86,214,154,.16);border-color:rgba(86,214,154,.6);color:var(--verde)}
.dia.vermelho{background:rgba(240,120,120,.16);border-color:rgba(240,120,120,.6);color:var(--vermelho)}
.dia.espera{background:rgba(121,191,255,.12);border-color:rgba(121,191,255,.55);color:var(--azul);animation:respirar 3s ease-in-out infinite}
.dia.hoje{box-shadow:0 0 0 2px var(--ouro)}
.legenda{display:flex;gap:1rem;flex-wrap:wrap;margin-top:.7rem;color:var(--muted);font-size:.72rem}
.legenda b{display:inline-block;width:.7rem;height:.7rem;margin-right:.3rem;border-radius:3px;vertical-align:-1px}
.balao{transition:transform .2s ease,box-shadow .2s ease}
.balao:hover{transform:translateY(-2px);box-shadow:0 16px 38px rgba(0,0,0,.28)}
.msg.pendente .odd{font-size:1.5rem;color:var(--ouro)}
.msg.pendente .aposta{background:linear-gradient(100deg,rgba(121,191,255,.1),rgba(27,30,38,.9));border:1px solid rgba(121,191,255,.18)}
.selecao-aposta strong{font-size:1.1rem}
@media (max-width:820px){.dias{grid-template-columns:repeat(10,minmax(0,1fr))}.desafio{width:calc(100% - 2rem)}}
@media (max-width:820px){.painel-grelha{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:640px){.topo{padding:.8rem 1rem}.painel-grelha{grid-template-columns:repeat(2,minmax(0,1fr));padding:.8rem 1rem}.indicador.banca{align-items:flex-start;flex-direction:column;gap:.15rem}.controlo{padding:0 1rem}.grupo-historico{padding:.85rem}.cabecalho-grupo{align-items:flex-start;flex-direction:column;gap:.25rem}.resultado-valores{flex-direction:column;gap:.35rem}}
@media (prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;scroll-behavior:auto!important;transition:none!important}.msg{opacity:1}}
.painel{position:static;background:none;border:0;backdrop-filter:none}
.painel-grelha{grid-template-columns:repeat(4,minmax(0,1fr));padding:1rem 1.5rem 0}
.indicador.banca{grid-column:1/-1;grid-row:1;padding:1.2rem 1.4rem;background:linear-gradient(110deg,rgba(224,177,92,.16),rgba(20,25,34,.96) 55%);border-color:rgba(224,177,92,.4)}
.indicador.banca strong{font-size:2.6rem;background:linear-gradient(90deg,#fff,var(--ouro));-webkit-background-clip:text;background-clip:text;color:transparent}
.indicador.profit{grid-column:span 1}
.indicador.espera strong{color:var(--azul)}
.indicador.espera{animation:pulso 2.6s ease-in-out infinite}
.indicador strong{font-size:1.7rem}
.desafio{margin:.9rem auto 0;width:min(932px,calc(100% - 3rem))}
.controlo{margin:.6rem auto 0}
.estado-chip{font-size:.78rem}
.grupo-historico{background:none;border:0;box-shadow:none;padding:.4rem 0}
.cabecalho-grupo h2{font-size:1.2rem}
main.chat{max-width:980px}
.lista-grupo{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:.9rem}
.msg.res{padding-left:0}
.balao{max-width:none;height:100%;border-radius:16px}
.msg.pendente .balao{border-left:1px solid var(--linha);border-top:3px solid var(--azul);position:relative;overflow:hidden}
.msg.pendente .balao:after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 35%,rgba(121,191,255,.09) 50%,transparent 65%);transform:translateX(-100%);animation:brilho 4.5s ease-in-out infinite;pointer-events:none}
.msg.green .balao{border-top:3px solid var(--verde)}
.msg.red .balao{border-top:3px solid var(--vermelho)}
.lista-analise,.analise .linha{font-size:.8rem}
details.analise{margin-bottom:1rem;padding:.8rem 1.1rem}
details.analise summary{cursor:pointer;color:var(--ouro);font-size:.85rem;font-weight:650;list-style:none}
details.analise summary:before{content:"▸ ";transition:transform .2s}
details.analise[open] summary:before{content:"▾ "}
.aviso{margin-top:1.5rem;font-size:.72rem;opacity:.75}
.indicador{animation:entrar .6s ease backwards}
.indicador:nth-child(2){animation-delay:.08s}.indicador:nth-child(3){animation-delay:.16s}.indicador:nth-child(4){animation-delay:.24s}.indicador:nth-child(5){animation-delay:.32s}
.dia{animation:entrar .5s ease backwards}
@keyframes pulso{0%,100%{box-shadow:0 8px 26px rgba(0,0,0,.14)}50%{box-shadow:0 0 22px rgba(121,191,255,.22)}}
@keyframes brilho{0%,60%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
@media (max-width:820px){.painel-grelha{grid-template-columns:repeat(2,minmax(0,1fr))}.indicador.banca strong{font-size:2rem}main.chat{padding:1.5rem 1rem 3rem}}
.ticker{overflow:hidden;border-bottom:1px solid rgba(224,177,92,.28);background:linear-gradient(90deg,rgba(60,45,18,.55),rgba(14,18,25,.9),rgba(60,45,18,.55));-webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)}
.ticker-pista{display:flex;width:max-content;animation:correr 28s linear infinite}
.ticker:hover .ticker-pista{animation-play-state:paused}
.tk{padding:.5rem 2rem;white-space:nowrap;font-size:.82rem;color:var(--muted);font-variant-numeric:tabular-nums}
.tk b{color:var(--ouro)}
.tk:after{content:"✦";margin-left:2rem;color:rgba(224,177,92,.5)}
.indicador.banca{position:relative;overflow:hidden}
.indicador.banca:before{content:"";position:absolute;top:0;bottom:0;width:35%;left:-40%;background:linear-gradient(100deg,transparent,rgba(255,226,160,.22),transparent);transform:skewX(-18deg);animation:varrer 5s ease-in-out infinite;pointer-events:none}
.indicador.banca strong{filter:drop-shadow(0 0 14px rgba(224,177,92,.45))}
.desafio{position:relative;overflow:hidden}
.desafio:before{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:1px;background:conic-gradient(from var(--ang,0deg),transparent 0 70%,rgba(224,177,92,.9) 85%,transparent 100%);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;animation:rodar 6s linear infinite;pointer-events:none}
.barra i{position:relative;overflow:hidden}
.barra i:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.6),transparent);animation:varrer2 2.4s ease-in-out infinite}
.dia.hoje{animation:brilhar-dia 2s ease-in-out infinite}
.msg.pendente .odd{text-shadow:0 0 14px rgba(224,177,92,.55)}
.msg.green .balao{animation:glow-verde 2.8s ease-in-out infinite}
.msg.red .balao{animation:glow-vermelho 2.8s ease-in-out infinite}
.metodo{margin-top:1.5rem;padding:0;overflow:hidden}
.metodo summary{cursor:pointer;list-style:none;padding:1rem 1.2rem;color:var(--ouro);font-weight:700;letter-spacing:.02em;display:flex;justify-content:space-between;align-items:center}
.metodo summary:after{content:"+";font-size:1.3rem;transition:transform .25s}
.metodo[open] summary:after{transform:rotate(45deg)}
.metodo-corpo{padding:0 1.2rem 1.2rem;animation:entrar .4s ease}
.passos{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.8rem;margin:.6rem 0 1rem}
.passo{padding:.9rem;border:1px solid var(--linha);border-radius:12px;background:rgba(27,30,38,.7);transition:transform .2s,border-color .2s}
.passo:hover{transform:translateY(-3px);border-color:rgba(224,177,92,.6)}
.passo i{display:inline-flex;align-items:center;justify-content:center;width:1.7rem;height:1.7rem;border-radius:50%;background:rgba(224,177,92,.15);color:var(--ouro);font-style:normal;font-weight:700;font-size:.85rem}
.passo h3{margin:.5rem 0 .25rem;font-size:.92rem;color:#fff}
.passo p{margin:0;font-size:.8rem;color:var(--muted)}
.metodo-nota{font-size:.8rem;color:var(--muted);border-left:3px solid var(--vermelho);padding-left:.8rem;margin:.4rem 0 0}
@property --ang{syntax:"<angle>";initial-value:0deg;inherits:false}
@keyframes rodar{to{--ang:360deg}}
@keyframes correr{to{transform:translateX(-25%)}}
@keyframes varrer{0%,55%{left:-40%}100%{left:130%}}
@keyframes varrer2{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
@keyframes brilhar-dia{0%,100%{box-shadow:0 0 0 2px var(--ouro)}50%{box-shadow:0 0 0 2px var(--ouro),0 0 16px rgba(224,177,92,.7)}}
@keyframes glow-verde{0%,100%{box-shadow:0 0 14px rgba(86,214,154,.1)}50%{box-shadow:0 0 28px rgba(86,214,154,.32)}}
@keyframes glow-vermelho{0%,100%{box-shadow:0 0 14px rgba(240,120,120,.1)}50%{box-shadow:0 0 28px rgba(240,120,120,.3)}}
@media (prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}.msg{opacity:1}}
"""


_METODO = (
    '<details class="balao metodo"><summary>Como são decididas estas apostas</summary>'
    '<div class="metodo-corpo"><div class="passos">'
    '<div class="passo"><i>1</i><h3>Recolha de odds</h3>'
    '<p>Todos os dias, as odds de 1X2 de várias casas de apostas (The Odds API) são guardadas '
    'para as ligas acompanhadas.</p></div>'
    '<div class="passo"><i>2</i><h3>Probabilidade do mercado</h3>'
    '<p>Cada odd é convertida em probabilidade e a margem das casas é retirada. '
    'A média entre casas dá a probabilidade de cada resultado.</p></div>'
    '<div class="passo"><i>3</i><h3>Filtros de qualidade</h3>'
    '<p>Só entram jogos com pelo menos 5 casas e sem odd suspeita, '
    'isto é, sem uma odd isolada fora do consenso.</p></div>'
    '<div class="passo"><i>4</i><h3>Escolha da equipa</h3>'
    '<p>Em cada jogo escolhe-se o resultado com maior probabilidade média. '
    'Fica registada a melhor odd disponível, antes do início.</p></div>'
    '<div class="passo"><i>5</i><h3>Gestão da banca</h3>'
    '<p>Stake de 2% da banca, no máximo 5 apostas por dia e 10% da banca em risco. '
    'Stop-loss se a banca cair para metade.</p></div>'
    '<div class="passo"><i>6</i><h3>Fecho automático</h3>'
    '<p>Os resultados oficiais fecham cada aposta como green, red ou void, '
    'e o lucro é calculado pela odd registada.</p></div>'
    '</div><p class="metodo-nota">É uma simulação com dinheiro fictício. Escolher o favorito do '
    'mercado não garante lucro: as odds já incluem a margem das casas. A análise dos últimos '
    '5 jogos de cada equipa ainda não faz parte da decisão.</p></div></details>'
)


def _momento(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def _eur(valor: float, sinal: bool = False) -> str:
    prefixo = "+" if sinal and valor > 0 else ""
    return f"{prefixo}{valor:.2f}".replace(".", ",") + " €"


def _proposta(p: dict, numero: int, atraso: float) -> str:
    lucro_possivel = p["stake"] * (p["odd"] - 1)
    inicio_lisboa = _momento(p["inicio"]).astimezone(pal.LISBOA)
    return (
        f'<div class="msg pendente" style="animation-delay:{atraso:.2f}s"><div class="balao">'
        f'<p class="etiqueta">APOSTA SIMULADA #{numero} · ⏳ EM ESPERA</p>'
        f'<p class="jogo">Jogo: {html.escape(p["jogo"])}</p>'
        f'<p class="hora">{inicio_lisboa:%d/%m %H:%M} Lisboa · '
        f'{html.escape(NOMES_LIGAS.get(p["desporto"], p["desporto"]))}</p>'
        '<div class="aposta">'
        f'<span class="selecao-aposta"><small>APOSTA NA EQUIPA</small>'
        f'<strong>{html.escape(nome_selecao(p["seleccao"]))}</strong></span>'
        f'<span class="odd"><small>ODD</small>{p["odd"]:.2f}</span>'
        "</div>"
        f'<div class="valor-espera"><span>Apostou (simulado)</span>'
        f'<strong>{_eur(p["stake"])}</strong></div>'
        f'<p class="linha">Se ganhar: profit {_eur(lucro_possivel, sinal=True)} · '
        f'retorno {_eur(p["stake"] * p["odd"])} · se perder: {_eur(-p["stake"])}</p>'
        f'<p class="linha">Melhor odd em {html.escape(p["casa_apostas"])}</p>'
        "</div></div>"
    )


def _resultado(p: dict, numero: int, atraso: float) -> str:
    icone, rotulo, texto = _RESULTADOS[p["estado"]]
    vencedor = nome_selecao(p["vencedor"]) if p.get("vencedor") else "—"
    lucro = b.lucro_palpite(p)
    lucro_classe = "positivo" if lucro > 0 else "negativo" if lucro < 0 else ""
    inicio_lisboa = _momento(p["inicio"]).astimezone(pal.LISBOA)
    return (
        f'<div class="msg res {p["estado"]}" style="animation-delay:{atraso:.2f}s"><div class="balao">'
        f'<p class="etiqueta">APOSTA SIMULADA #{numero} · RESULTADO FINAL</p>'
        f'<span class="estado-resultado">{icone} {rotulo}</span>'
        f'<p class="jogo">Jogo: {html.escape(p["jogo"])}</p>'
        f'<p class="hora">{inicio_lisboa:%d/%m %H:%M} Lisboa</p>'
        f'<p class="linha">Aposta: {html.escape(nome_selecao(p["seleccao"]))} {texto}; '
        f"vencedor: {html.escape(vencedor)}</p>"
        '<div class="resultado-valores">'
        f'<div><span>Stake simulada</span><strong>{_eur(p["stake"])}</strong></div>'
        f'<div><span>Lucro/prejuízo</span><strong class="{lucro_classe}">'
        f'{_eur(lucro, sinal=True)}</strong></div></div>'
        "</div></div>"
    )


def _feed(palpites: list[dict]) -> str:
    numeros = {id(p): n for n, p in enumerate(palpites, 1)}
    pendentes = sorted(
        (p for p in palpites if p["estado"] == "pendente"),
        key=lambda p: p["inicio"],
    )
    fechados = sorted(
        (p for p in palpites if p["estado"] != "pendente"),
        key=lambda p: p.get("fechado_em") or p["inicio"],
        reverse=True,
    )
    valor_em_espera = sum(p["stake"] for p in pendentes)
    greens = sum(1 for p in fechados if p["estado"] == "green")
    reds = sum(1 for p in fechados if p["estado"] == "red")
    voids = sum(1 for p in fechados if p["estado"] == "void")

    partes = [
        '<section class="grupo-historico"><header class="cabecalho-grupo">'
        '<div><h2>Em espera</h2><p>Partidas ainda sem resultado final</p></div>'
        f'<span class="resumo-grupo">{len(pendentes)} · {_eur(valor_em_espera)} em jogo</span>'
        '</header><div class="lista-grupo">'
    ]
    if pendentes:
        partes.extend(
            _proposta(p, numeros[id(p)], min(i * ATRASO_ENTRE_MENSAGENS, ATRASO_MAXIMO))
            for i, p in enumerate(pendentes)
        )
    else:
        partes.append(
            '<p class="mensagem-grupo">Nenhum palpite à espera neste momento. '
            'A atualização automática continuará a procurar sinais válidos; '
            'atualização manual: <code>python main.py --atualizar</code>.</p>'
        )
    partes.append('</div></section>')

    partes.extend([
        '<section class="grupo-historico"><header class="cabecalho-grupo">'
        '<div><h2>Histórico de vitórias e derrotas</h2>'
        '<p>Resultados fechados, com stake e lucro/prejuízo simulado</p></div>'
        f'<span class="resumo-grupo">{greens} green · {reds} red · {voids} void</span>'
        '</header><div class="lista-grupo">'
    ])
    if fechados:
        partes.extend(
            _resultado(p, numeros[id(p)], min(i * ATRASO_ENTRE_MENSAGENS, ATRASO_MAXIMO))
            for i, p in enumerate(fechados)
        )
    else:
        partes.append('<p class="mensagem-grupo">Ainda não há resultados fechados.</p>')
    partes.append('</div></section>')
    return "".join(partes)


def _indicadores(palpites: list[dict], agora: datetime) -> str:
    fechados = [p for p in palpites if p["estado"] in ("green", "red")]
    greens = sum(1 for p in fechados if p["estado"] == "green")
    reds = len(fechados) - greens
    voids = sum(1 for p in palpites if p["estado"] == "void")
    pendentes = sum(1 for p in palpites if p["estado"] == "pendente")
    valor_em_espera = sum(p["stake"] for p in palpites if p["estado"] == "pendente")
    taxa = f"{greens / len(fechados) * 100:.0f}%" if fechados else "—"

    banca = b.banca_atual(palpites)
    lucro = banca - b.BANCA_INICIAL
    apostado = sum(p["stake"] for p in fechados)
    roi = f"{lucro / apostado * 100:+.1f}%" if apostado else "—"


    return (
        '<div class="painel"><div class="painel-grelha">'
        f'<div class="indicador banca"><div><span>Banca simulada</span>'
        f'<small>inicial {_eur(b.BANCA_INICIAL)} · {_eur(b.stake_para(banca))} por aposta · '
        f'até {MAX_POR_DIA}/dia</small></div><strong>{_eur(banca)}</strong></div>'
        f'<div class="indicador profit {"positivo" if lucro > 0 else "negativo" if lucro < 0 else "neutro"}">'
        f'<span>Lucro simulado</span><strong>{_eur(lucro, sinal=True)}</strong>'
        f"<small>ROI {roi}</small></div>"
        f'<div class="indicador espera"><span>Em espera</span><strong>{pendentes}</strong>'
        f"<small>{_eur(valor_em_espera)} em jogo</small></div>"
        f'<div class="indicador verde"><span>Green</span><strong>{greens}</strong>'
        f"<small>acerto {taxa}</small></div>"
        f'<div class="indicador vermelho"><span>Red</span><strong>{reds}</strong>'
        f"<small>{voids} void</small></div>"
        "</div>"
        + (
            '<p class="alerta">Stop-loss ativo: a banca desceu para metade. Sem novos palpites.</p>'
            if b.stop_loss_ativo(banca)
            else ""
        )
        + "</div>"
    )


def _desafio(palpites: list[dict], agora: datetime) -> str:
    inicio = datetime.fromisoformat(DIA_INICIO_TESTE).date()
    hoje = agora.astimezone(pal.LISBOA).date()
    dia_n = min(max((hoje - inicio).days + 1, 0), DIAS_TESTE)
    lucro = b.banca_atual(palpites) - b.BANCA_INICIAL
    classe = "positivo" if lucro > 0 else "negativo" if lucro < 0 else ""
    celulas = []
    for i in range(DIAS_TESTE):
        dia = inicio + timedelta(days=i)
        do_dia = [p for p in palpites if pal.dia_lisboa(p["inicio"]) == dia.isoformat()]
        fechados = [p for p in do_dia if p["estado"] in ("green", "red")]
        pl = sum(b.lucro_palpite(p) for p in fechados)
        if any(p["estado"] == "pendente" for p in do_dia):
            estado, dica = "espera", f"{len(do_dia)} apostas, {sum(1 for p in do_dia if p['estado'] == 'pendente')} em espera"
        elif fechados:
            estado, dica = ("verde" if pl > 0 else "vermelho" if pl < 0 else ""), f"{len(fechados)} fechadas · {_eur(pl, sinal=True)}"
        else:
            estado, dica = "", "sem apostas"
        extra = " hoje" if dia == hoje else ""
        celulas.append(
            f'<span class="dia {estado}{extra}" title="{dia:%d/%m} · {dica}">{dia.day}</span>'
        )
    pct = dia_n / DIAS_TESTE * 100
    return (
        '<section class="desafio"><div class="desafio-topo"><div>'
        f'<h2>Teste de {DIAS_TESTE} dias · <em>dia {dia_n}/{DIAS_TESTE}</em></h2>'
        f'<p>De {inicio:%d/%m} a {(inicio + timedelta(days=DIAS_TESTE - 1)):%d/%m} · até {MAX_POR_DIA} apostas '
        f'por dia, atualização automática</p></div>'
        f'<div class="desafio-lucro"><span>Profit acumulado</span>'
        f'<strong class="{classe}">{_eur(lucro, sinal=True)}</strong></div></div>'
        f'<div class="barra"><i style="width:{pct:.0f}%"></i></div>'
        f'<div class="dias">{"".join(celulas)}</div>'
        '<div class="legenda"><span><b style="background:var(--verde)"></b>dia positivo</span>'
        '<span><b style="background:var(--vermelho)"></b>dia negativo</span>'
        '<span><b style="background:var(--azul)"></b>em espera</span></div></section>'
    )


def _ticker(palpites: list[dict]) -> str:
    itens = []
    for p in sorted(palpites, key=lambda x: x["inicio"]):
        estado = {"pendente": "⏳", "green": "✅", "red": "❌", "void": "⚪"}[p["estado"]]
        lucro = b.lucro_palpite(p) if p["estado"] != "pendente" else p["stake"] * (p["odd"] - 1)
        itens.append(
            f'<span class="tk">{estado} <b>{html.escape(nome_selecao(p["seleccao"]))}</b> '
            f'@ {p["odd"]:.2f} · {_eur(p["stake"])} · {_eur(lucro, sinal=True)}</span>'
        )
    if not itens:
        return ""
    faixa = "".join(itens)
    return f'<div class="ticker"><div class="ticker-pista">{faixa}{faixa}{faixa}{faixa}</div></div>'


_CONTROLO_HTML = """
<div class="controlo"><button id="btn-ativo" type="button" data-ativo="1">A carregar…</button><span id="estado-txt" class="estado-chip"></span></div>
<script>
(function(){
  var btn=document.getElementById('btn-ativo'), txt=document.getElementById('estado-txt');
  var visto=null;
  function pintar(e){
    btn.dataset.ativo=e.ativo?'1':'0';
    btn.textContent=e.ativo?'Parar atualização':'Retomar atualização';
    txt.dataset.ativo=e.ativo?'1':'0';
    var data=e.ultimo_ciclo?new Date(e.ultimo_ciclo).toLocaleString('pt-PT',{timeZone:'Europe/Lisbon',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'';
    var ult=data?' · última atualização '+data+' Lisboa':'';
    txt.textContent=(e.ativo?'Ativa':'Em pausa')+ult;
  }
  function ler(){
    fetch('/api/estado',{cache:'no-store'}).then(function(r){return r.json();}).then(function(e){
      pintar(e);
      if(visto!==null && e.ultimo_ciclo!==visto){ location.reload(); }
      visto=e.ultimo_ciclo;
    }).catch(function(){ txt.textContent='Servidor desligado: corre python servidor.py'; });
  }
  btn.addEventListener('click',function(){
    fetch('/api/ativo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ativo:btn.dataset.ativo!=='1'})}).then(ler);
  });
  ler();
  setInterval(ler,30000);
})();
</script>
"""


def _resumo_analise(analises: list[dict], dia_jogo: str | None, palpites: list[dict], agora: datetime) -> str:
    if not dia_jogo:
        return ""
    jogos = [
        analise for analise in analises
        if pal.dia_lisboa(analise["inicio"]) == dia_jogo
        and _momento(analise["inicio"]) > agora
    ]
    if not jogos:
        return ""

    com_sinal = sum(
        1
        for jogo in jogos
        if any(selecao["valor"] for selecao in jogo["selecoes"])
    )
    apostas_do_dia = [p for p in palpites if pal.dia_lisboa(p["inicio"]) == dia_jogo]
    linhas = []
    for jogo in sorted(jogos, key=lambda item: item["inicio"]):
        inicio_lisboa = _momento(jogo["inicio"]).astimezone(pal.LISBOA)
        apostas_jogo = [p for p in apostas_do_dia if p["id"] == jogo["id"]]
        if apostas_jogo:
            estado_por_codigo = {
                "pendente": "EM ESPERA",
                "green": "GREEN",
                "red": "RED",
                "void": "VOID",
            }
            estado = estado_por_codigo[apostas_jogo[0]["estado"]]
            detalhes = "".join(
                '<span class="estado-aposta">'
                f'{html.escape(nome_selecao(p["seleccao"]))} @ {p["odd"]:.2f} · '
                f'{_eur(p["stake"])} · {estado_por_codigo[p["estado"]]}'
                '</span>'
                for p in apostas_jogo
            )
            descricao = (
                '<div class="sem-aposta"><strong>APOSTA SIMULADA REGISTADA</strong>'
                f'{detalhes}</div>'
            )
        elif jogo["selecoes"]:
            favorito = max(jogo["selecoes"], key=lambda selecao: selecao["prob_mercado"])
            descricao = (
                '<div class="sem-aposta"><strong>SEM APOSTA REGISTADA</strong>'
                f'<span>Mais provável segundo as odds: {html.escape(nome_selecao(favorito["seleccao"]))} '
                f'({favorito["prob_mercado"] * 100:.1f}% de probabilidade estimada pelo mercado). '
                'É apenas uma referência, não uma aposta nem uma garantia.</span>'
                '<span>Sem registo por falta de odds completas, limite diário/exposição '
                'ou uma odd considerada suspeita.</span></div>'
            )
        else:
            descricao = (
                '<div class="sem-aposta"><strong>SEM APOSTA REGISTADA</strong>'
                '<span>Sem odds completas suficientes para indicar um favorito.</span></div>'
            )
        linhas.append(
            '<li class="linha-analise"><span class="jogo">'
            f'Jogo: {html.escape(jogo["jogo"])}</span>'
            f'<span class="hora">{inicio_lisboa:%H:%M} Lisboa · {jogo["casas"]} casas analisadas</span>'
            f'{descricao}</li>'
        )
    return (
        '<details class="balao analise"><summary>'
        f'Análise de {dia_jogo[8:10]}/{dia_jogo[5:7]} · {len(jogos)} '
        f'{"jogo" if len(jogos) == 1 else "jogos"}</summary>'
        f'<p><strong>{len(apostas_do_dia)} '
        f'{"aposta simulada registada" if len(apostas_do_dia) == 1 else "apostas simuladas registadas"} '
        f'para {dia_jogo[8:10]}/{dia_jogo[5:7]}.</strong> '
        f'{len(jogos)} {"jogo avaliado" if len(jogos) == 1 else "jogos avaliados"}; '
        f'{com_sinal} {"com sinal válido" if com_sinal == 1 else "com sinais válidos"}.</p>'
        '<p class="linha">A estratégia de simulação escolhe, por jogo, o favorito pelas odds '
        '(maior probabilidade média), com pelo menos 5 casas e sem odd suspeita. '
        'Não é uma previsão garantida nem uma recomendação.</p>'
        f'<ul class="lista-analise">{"".join(linhas)}</ul>'
        '</details>'
    )


def html_chat(
    palpites: list[dict],
    agora: datetime | None = None,
    analises: list[dict] | None = None,
    dia_jogo: str | None = None,
) -> str:
    agora = agora or datetime.now(timezone.utc)
    corpo = _feed(palpites)
    if not corpo:
        corpo = (
            '<p class="vazio">Ainda não há palpites válidos para mostrar. '
            'Atualiza com <code>python main.py --atualizar</code>.</p>'
        )
    resumo_analise = _resumo_analise(analises or [], dia_jogo, palpites, agora)
    if resumo_analise:
        corpo = resumo_analise + corpo
    return (
        "<!doctype html><html lang=\"pt-PT\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Palpites simulados</title>"
        f"<style>{_CSS}</style></head><body>"
        '<header class="topo"><span class="marca">Odds &amp; Valor <small>SIMULAÇÃO</small></span>'
        '<a href="odds.html">Odds e sinais</a></header>'
        f"{_ticker(palpites)}"
        f"{_CONTROLO_HTML}"
        f"{_indicadores(palpites, agora)}"
        f"{_desafio(palpites, agora)}"
        f'<main class="chat"><div class="feed">{corpo}</div>'
        f"{_METODO}"
        f'<p class="aviso">{html.escape(SIMULACAO)} {html.escape(AVISO)}</p></main>'
        "</body></html>"
    )
