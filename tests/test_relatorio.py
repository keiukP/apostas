import relatorio as rel


def _analise(jogo="Casa vs <Fora>"):
    return {
        "id": "x",
        "desporto": "soccer_epl",
        "jogo": jogo,
        "inicio": "2026-10-18T13:00:00Z",
        "casa_equipa": "Casa",
        "fora_equipa": "Fora",
        "selecoes": [
            {"seleccao": "Casa", "melhor_odd": 2.10, "casa": "Bookie", "prob_mercado": 0.45,
             "vantagem": 0.03, "valor": True, "odd_suspeita": False},
            {"seleccao": "Draw", "melhor_odd": 3.40, "casa": "Other", "prob_mercado": 0.27,
             "vantagem": -0.01, "valor": False, "odd_suspeita": False},
        ],
    }


def test_html_mostra_empate_e_escapa_nomes():
    pagina = rel.html_site({"soccer_epl": [_analise()]}, "2026-10-18")
    assert "Empate" in pagina
    assert "&lt;Fora&gt;" in pagina
    assert "<Fora>" not in pagina


def test_html_destaca_sinal_de_valor():
    pagina = rel.html_site({"soccer_epl": [_analise()]}, "2026-10-18")
    assert "opcao valor" in pagina
    assert pagina.count("opcao valor") == 1


def test_html_sem_sinais_mostra_mensagem():
    sem_valor = _analise()
    sem_valor["selecoes"][0]["valor"] = False
    pagina = rel.html_site({"soccer_epl": [sem_valor]}, "2026-10-18")
    assert "nenhuma seleção ultrapassou" in pagina


def test_html_sem_jogos():
    pagina = rel.html_site({}, "2026-10-18")
    assert "Sem jogos com odds disponíveis" in pagina
