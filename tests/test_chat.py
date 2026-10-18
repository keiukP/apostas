from datetime import datetime, timedelta, timezone

import chat


AGORA = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def _palpite(id_, estado, jogo="Casa <x> vs Fora", vencedor=None, registo=AGORA):
    fecho = (registo + timedelta(hours=3)).isoformat(timespec="minutes") if estado != "pendente" else None
    return {
        "id": id_,
        "desporto": "soccer_epl",
        "jogo": jogo,
        "inicio": (registo + timedelta(hours=2)).isoformat(),
        "casa_equipa": "Casa",
        "fora_equipa": "Fora",
        "seleccao": "Casa",
        "odd": 2.0,
        "casa_apostas": "Bookie",
        "prob_mercado": 0.4,
        "vantagem": 0.05,
        "data_registo": registo.date().isoformat(),
        "estado": estado,
        "vencedor": vencedor,
        "stake": 2.0,
        "registado_em": registo.isoformat(timespec="minutes"),
        "fechado_em": fecho,
    }


def test_sem_palpites_mostra_instrucao():
    pagina = chat.html_chat([], AGORA)
    assert "--atualizar" in pagina
    assert "<h2>Em espera</h2>" in pagina
    assert "<h2>Histórico de vitórias e derrotas</h2>" in pagina
    assert "Ainda não há resultados fechados." in pagina
    assert '<span>Lucro simulado</span><strong>0,00 €</strong>' in pagina
    assert "ROI —" in pagina
    assert "2,00 € por aposta · até 5/dia" in pagina


def test_escapa_nomes_dos_jogos():
    pagina = chat.html_chat([_palpite("a", "pendente")], AGORA)
    assert "Casa &lt;x&gt; vs Fora" in pagina
    assert "Casa <x>" not in pagina


def test_proposta_aparece_antes_do_resultado():
    palpites = [_palpite("a", "green", vencedor="Casa")]
    pagina = chat.html_chat(palpites, AGORA + timedelta(hours=4))
    assert pagina.index("APOSTA SIMULADA #1") < pagina.index("GREEN")


def test_green_red_e_void_com_lucro_simulado():
    palpites = [
        _palpite("g", "green", vencedor="Casa"),
        _palpite("r", "red", vencedor="Fora"),
        _palpite("v", "void"),
    ]
    pagina = chat.html_chat(palpites, AGORA + timedelta(hours=4))
    assert "✅ GREEN" in pagina and "❌ RED" in pagina and "⚪ VOID" in pagina
    assert "+2,00 €" in pagina
    assert "-2,00 €" in pagina
    assert "Stake simulada" in pagina
    assert "Lucro/prejuízo" in pagina


def test_contagens_no_painel():
    palpites = [
        _palpite("g1", "green", vencedor="Casa"),
        _palpite("g2", "green", vencedor="Casa"),
        _palpite("r1", "red", vencedor="Fora"),
        _palpite("p1", "pendente"),
    ]
    pagina = chat.html_chat(palpites, AGORA + timedelta(hours=4))
    assert '<span>Green</span><strong>2</strong>' in pagina
    assert '<span>Red</span><strong>1</strong>' in pagina
    assert '<span>Em espera</span><strong>1</strong>' in pagina
    assert "67%" in pagina
    assert '<span>Lucro simulado</span><strong>+2,00 €</strong>' in pagina


def test_pendentes_mostram_montante_em_espera():
    pagina = chat.html_chat([_palpite("p", "pendente")], AGORA)
    assert "APOSTA SIMULADA #1 · ⏳ EM ESPERA" in pagina
    assert "APOSTA NA EQUIPA" in pagina
    assert "Apostou (simulado)" in pagina
    assert "Se ganhar: profit" in pagina
    assert "1 · 2,00 € em jogo" in pagina
    assert "2,00 € em jogo" in pagina


def test_ticker_e_metodologia_aparecem():
    pagina = chat.html_chat([_palpite("p", "pendente")], AGORA)
    assert 'class="ticker"' in pagina
    assert "Como são decididas estas apostas" in pagina
    assert "Gestão da banca" in pagina


def test_desafio_de_30_dias_mostra_progresso_e_profit():
    pagina = chat.html_chat([_palpite("p", "pendente")], AGORA)
    assert "Teste de 30 dias" in pagina
    assert pagina.count('class="dia ') == 30
    assert "Profit acumulado" in pagina


def test_lucro_negativo_fica_destacado():
    pagina = chat.html_chat([_palpite("red", "red", vencedor="Fora")], AGORA)
    assert 'class="indicador profit negativo"' in pagina
    assert '<span>Lucro simulado</span><strong>-2,00 €</strong>' in pagina


def test_contagem_amanha_e_hora_de_lisboa():
    palpite = _palpite("amanha", "pendente")
    palpite["inicio"] = "2026-10-19T12:00:00Z"
    pagina = chat.html_chat([palpite], AGORA)
    assert "19/10 13:00 Lisboa" in pagina


def test_resumo_analise_explica_quando_nao_ha_sinal():
    analise = {
        "id": "jogo",
        "inicio": "2026-10-19T12:00:00Z",
        "jogo": "Casa vs Fora",
        "casas": 8,
        "selecoes": [{
            "seleccao": "Casa",
            "vantagem": 0.01,
            "prob_mercado": 0.6,
            "valor": False,
        }],
    }
    pagina = chat.html_chat([], AGORA, [analise], "2026-10-19")
    assert "0 apostas simuladas registadas para 19/10" in pagina
    assert "1 jogo avaliado; 0 com sinais válidos" in pagina
    assert "Mais provável segundo as odds: Casa (60.0%" in pagina
    assert "SEM APOSTA REGISTADA" in pagina
    assert "escolhe, por jogo, o favorito pelas odds" in pagina
    assert "Casa vs Fora" in pagina


def test_resumo_identifica_aposta_simulada_registada():
    palpite = _palpite("jogo", "pendente")
    palpite["inicio"] = "2026-10-19T12:00:00Z"
    analise = {
        "id": "jogo",
        "inicio": "2026-10-19T12:00:00Z",
        "jogo": "Casa <x> vs Fora",
        "casas": 8,
        "selecoes": [{
            "seleccao": "Casa",
            "vantagem": 0.03,
            "prob_mercado": 0.6,
            "valor": True,
        }],
    }
    pagina = chat.html_chat([palpite], AGORA, [analise], "2026-10-19")
    assert "1 aposta simulada registada para 19/10" in pagina
    assert "APOSTA SIMULADA REGISTADA" in pagina
    assert "Casa @ 2.00 · 2,00 € · EM ESPERA" in pagina
    assert "Jogo: Casa &lt;x&gt; vs Fora" in pagina


def test_stop_loss_mostra_aviso():
    perdas = [_palpite(f"r{i}", "red", vencedor="Fora") for i in range(30)]
    pagina = chat.html_chat(perdas, AGORA + timedelta(hours=4))
    assert "Stop-loss ativo" in pagina
