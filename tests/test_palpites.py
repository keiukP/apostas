from datetime import datetime, timedelta, timezone

import palpites as pal


AGORA = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
FUTURO = datetime(2026, 10, 18, 20, 0, tzinfo=timezone.utc).isoformat()
PASSADO = (AGORA - timedelta(hours=1)).isoformat()
AMANHA = datetime(2026, 10, 19, 20, 0, tzinfo=timezone.utc).isoformat()


def _analise(id_, seleccoes, inicio=FUTURO):
    return {
        "id": id_,
        "desporto": "soccer_epl",
        "jogo": "Casa vs Fora",
        "inicio": inicio,
        "casa_equipa": "Casa",
        "fora_equipa": "Fora",
        "selecoes": seleccoes,
    }


def _sel(nome, odd, vantagem, valor=True):
    return {
        "seleccao": nome,
        "melhor_odd": odd,
        "casa": "Bookie",
        "prob_mercado": 0.3,
        "vantagem": vantagem,
        "valor": valor,
    }


def test_registar_respeita_limite_diario():
    analises = [_analise(f"j{i}", [_sel("Casa", 2.0, 0.05 + i / 100)]) for i in range(8)]
    palp = []
    novos = pal.registar_do_dia(palp, analises, "2026-10-18", AGORA)
    assert len(novos) == pal.MAX_POR_DIA
    assert len(palp) == pal.MAX_POR_DIA


def test_registar_escolhe_maior_vantagem_primeiro():
    analises = [
        _analise("a", [_sel("Casa", 2.0, 0.02)]),
        _analise("b", [_sel("Casa", 2.0, 0.09)]),
    ]
    palp = []
    pal.registar_do_dia(palp, analises, "2026-10-18", AGORA, limite=1)
    assert palp[0]["id"] == "b"


def test_registar_ignora_jogos_iniciados_e_sem_valor():
    analises = [
        _analise("iniciado", [_sel("Casa", 2.0, 0.09)], inicio=PASSADO),
        _analise("sem-valor", [_sel("Casa", 2.0, 0.09, valor=False)]),
    ]
    palp = []
    assert pal.registar_do_dia(palp, analises, "2026-10-18", AGORA) == []


def test_registar_nao_duplica():
    analises = [_analise("a", [_sel("Casa", 2.0, 0.05)])]
    palp = []
    pal.registar_do_dia(palp, analises, "2026-10-18", AGORA)
    assert pal.registar_do_dia(palp, analises, "2026-10-18", AGORA) == []


def test_registar_so_jogos_do_dia_pedido():
    analises = [
        _analise("hoje", [_sel("Casa", 2.0, 0.05)]),
        _analise("amanha", [_sel("Casa", 2.0, 0.09)], inicio=AMANHA),
    ]
    palp = []
    pal.registar_do_dia(palp, analises, "2026-10-18", AGORA, dia_jogo="2026-10-18")
    assert [p["id"] for p in palp] == ["hoje"]


def test_favorito_mercado_regista_a_maior_probabilidade_sem_sinal_de_valor():
    favorito = _sel("Casa", 1.8, 0.005, valor=False)
    favorito["prob_mercado"] = 0.64
    alternativa = _sel("Fora", 4.2, 0.01, valor=False)
    alternativa["prob_mercado"] = 0.21
    analise = _analise("mercado", [favorito, alternativa])
    analise["casas"] = 8
    palp = []

    novos = pal.registar_do_dia(
        palp,
        [analise],
        "2026-10-18",
        AGORA,
        estrategia="favorito_mercado",
    )

    assert len(novos) == 1
    assert novos[0]["seleccao"] == "Casa"
    assert novos[0]["metodo"] == "favorito_mercado"
    assert novos[0]["stake"] == 2.0


def test_favorito_mercado_exige_casas_minimas_e_rejeita_odd_suspeita():
    favorito = _sel("Casa", 1.8, 0.005, valor=False)
    favorito["prob_mercado"] = 0.64
    favorito["odd_suspeita"] = True
    analise = _analise("mercado", [favorito])
    analise["casas"] = 4
    palp = []
    assert pal.registar_do_dia(
        palp,
        [analise],
        "2026-10-18",
        AGORA,
        estrategia="favorito_mercado",
    ) == []


def test_limite_conta_so_o_dia_de_jogo():
    existente = {"id": "x", "seleccao": "Casa", "odd": 2.0, "stake": 1.0, "estado": "pendente",
                 "inicio": AMANHA, "data_registo": "2026-10-18"}
    analises = [_analise(f"j{i}", [_sel("Casa", 2.0, 0.05 + i / 100)]) for i in range(5)]
    palp = [existente]
    novos = pal.registar_do_dia(palp, analises, "2026-10-18", AGORA, limite=3, dia_jogo="2026-10-18")
    assert len(novos) == 3


def test_dia_lisboa_usa_hora_de_lisboa():
    assert pal.dia_lisboa("2026-10-18T23:30:00Z") == "2026-10-19"
    assert pal.dia_lisboa("2026-10-18T12:00:00Z") == "2026-10-18"


def test_vencedor_casa_fora_empate_e_invalido():
    base = {"completed": True, "home_team": "Casa", "away_team": "Fora"}
    assert pal.vencedor({**base, "scores": [{"name": "Casa", "score": "2"}, {"name": "Fora", "score": "1"}]}) == "Casa"
    assert pal.vencedor({**base, "scores": [{"name": "Casa", "score": "0"}, {"name": "Fora", "score": "1"}]}) == "Fora"
    assert pal.vencedor({**base, "scores": [{"name": "Casa", "score": "1"}, {"name": "Fora", "score": "1"}]}) == pal.EMPATE
    assert pal.vencedor({**base, "completed": False, "scores": []}) is None
    assert pal.vencedor({**base, "scores": [{"name": "Casa", "score": "1"}]}) is None


def test_liquidar_green_red_void_e_pendente():
    palp = [
        {"id": "g", "seleccao": "Casa", "odd": 2.0, "inicio": FUTURO, "estado": "pendente", "vencedor": None},
        {"id": "r", "seleccao": "Casa", "odd": 2.0, "inicio": FUTURO, "estado": "pendente", "vencedor": None},
        {"id": "v", "seleccao": "Casa", "odd": 2.0, "inicio": FUTURO, "estado": "pendente", "vencedor": None},
        {"id": "p", "seleccao": "Casa", "odd": 2.0, "inicio": FUTURO, "estado": "pendente", "vencedor": None},
    ]
    def ev(h, a):
        return {"completed": True, "home_team": "Casa", "away_team": "Fora",
                "scores": [{"name": "Casa", "score": h}, {"name": "Fora", "score": a}]}
    eventos = {"g": ev("2", "0"), "r": ev("0", "1"), "v": {"completed": True, "home_team": "Casa", "away_team": "Fora", "scores": []}}
    assert pal.liquidar(palp, eventos, AGORA) == 3
    assert [p["estado"] for p in palp] == ["green", "red", "void", "pendente"]
    assert palp[0]["fechado_em"] == AGORA.isoformat(timespec="minutes")
    assert palp[3].get("fechado_em") is None


def test_liquidar_anula_sem_resultado_passados_quatro_dias():
    antigo = (AGORA - timedelta(days=pal.DIAS_SEM_RESULTADO + 1)).isoformat()
    palp = [{"id": "x", "seleccao": "Casa", "odd": 2.0, "inicio": antigo, "estado": "pendente", "vencedor": None}]
    assert pal.liquidar(palp, {}, AGORA) == 1
    assert palp[0]["estado"] == "void"


def test_registar_guarda_stake_e_instante_de_registo():
    palp = []
    pal.registar_do_dia(palp, [_analise("a", [_sel("Casa", 2.0, 0.05)])], "2026-10-18", AGORA)
    assert palp[0]["stake"] == 2.0
    assert palp[0]["registado_em"] == AGORA.isoformat(timespec="minutes")
    assert palp[0]["fechado_em"] is None


def test_resumo_lucro_e_roi():
    palp = [
        {"estado": "green", "odd": 3.0},
        {"estado": "red", "odd": 2.0},
        {"estado": "pendente", "odd": 2.0},
    ]
    r = pal.resumo(palp)
    assert r["green"] == 1 and r["red"] == 1 and r["pendentes"] == 1
    assert r["lucro_unidades"] == 1.0
    assert r["roi"] == 0.5
    assert r["taxa_acerto"] == 0.5


def test_resumo_vazio():
    r = pal.resumo([])
    assert r["taxa_acerto"] is None and r["roi"] is None
