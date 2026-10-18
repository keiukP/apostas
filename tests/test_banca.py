import banca as b


def _p(estado, stake, odd, inicio="2026-10-18T10:00:00+00:00", jogo="J"):
    return {"estado": estado, "stake": stake, "odd": odd, "inicio": inicio, "jogo": jogo}


def test_stake_dois_por_cento_com_minimo_e_maximo():
    assert b.stake_para(100) == 2.0
    assert b.stake_para(10) == 0.5
    assert b.stake_para(0) == 0.0
    assert b.stake_para(1000) == 20.0


def test_lucro_por_estado():
    assert b.lucro_palpite(_p("green", 2.0, 3.0)) == 4.0
    assert b.lucro_palpite(_p("red", 2.0, 3.0)) == -2.0
    assert b.lucro_palpite(_p("void", 2.0, 3.0)) == 0.0
    assert b.lucro_palpite(_p("pendente", 2.0, 3.0)) == 0.0


def test_banca_atual_soma_lucros():
    palp = [_p("green", 2.0, 3.0), _p("red", 2.0, 2.0)]
    assert b.banca_atual(palp) == 102.0


def test_stop_loss_a_meio_da_banca():
    assert b.stop_loss_ativo(50.0)
    assert not b.stop_loss_ativo(50.01)


def test_pode_apostar_respeita_exposicao_e_stop_loss():
    assert b.pode_apostar(2.0, 100.0, [])
    pendentes = [_p("pendente", 2.0, 2.0) for _ in range(5)]
    assert not b.pode_apostar(2.0, 100.0, pendentes)
    assert not b.pode_apostar(2.0, 40.0, [])


def test_curva_ordena_por_inicio_e_ignora_pendentes():
    palp = [
        _p("red", 2.0, 2.0, inicio="2026-10-18T12:00:00+00:00", jogo="B"),
        _p("green", 2.0, 3.0, inicio="2026-10-18T10:00:00+00:00", jogo="A"),
        _p("pendente", 2.0, 2.0, inicio="2026-10-18T14:00:00+00:00", jogo="C"),
    ]
    pontos = b.curva(palp)
    assert pontos == [("início", 100.0), ("A", 104.0), ("B", 102.0)]
