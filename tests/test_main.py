from datetime import date, datetime, timezone
from types import SimpleNamespace

import main


def test_dia_alvo_usa_amanha_em_hora_de_lisboa():
    args = SimpleNamespace(dia_jogo=None, preparar_amanha=True)
    agora = datetime(2026, 10, 18, 23, 30, tzinfo=timezone.utc)
    assert main._dia_alvo(args, agora) == "2026-10-20"


def test_dia_alvo_respeita_data_explicita():
    args = SimpleNamespace(dia_jogo=date(2026, 10, 19), preparar_amanha=False)
    agora = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
    assert main._dia_alvo(args, agora) == "2026-10-19"


def test_dia_alvo_por_padrao_e_hoje_em_lisboa():
    args = SimpleNamespace(dia_jogo=None, preparar_amanha=False)
    agora = datetime(2026, 10, 18, 23, 30, tzinfo=timezone.utc)
    assert main._dia_alvo(args, agora) == "2026-10-19"
