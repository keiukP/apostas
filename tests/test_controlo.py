from datetime import datetime, timezone

import controlo


def test_estado_por_defeito_e_ativo(tmp_path):
    assert controlo.estado(tmp_path / "controlo.json") == {"ativo": True, "ultimo_ciclo": None}


def test_definir_ativo_persiste(tmp_path):
    ficheiro = tmp_path / "controlo.json"
    controlo.definir_ativo(False, ficheiro)
    assert controlo.estado(ficheiro)["ativo"] is False
    controlo.definir_ativo(True, ficheiro)
    assert controlo.estado(ficheiro)["ativo"] is True


def test_registar_ciclo_mantem_ativo(tmp_path):
    ficheiro = tmp_path / "controlo.json"
    controlo.definir_ativo(False, ficheiro)
    agora = datetime(2026, 10, 18, 3, 0, tzinfo=timezone.utc)
    controlo.registar_ciclo(agora, ficheiro)
    e = controlo.estado(ficheiro)
    assert e["ativo"] is False
    assert e["ultimo_ciclo"] == "2026-10-18T03:00:00+00:00"
