import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from relatorio import AVISO, TELEGRAM_LIMITE, html_site, texto_resumo  # noqa: E402
from valor import analisar_evento  # noqa: E402


def _evento(precos_por_casa, home="Benfica", away="Porto"):
    casas = []
    for titulo, (h, d, a) in precos_por_casa.items():
        casas.append({
            "title": titulo,
            "markets": [{"key": "h2h", "outcomes": [
                {"name": home, "price": h},
                {"name": "Draw", "price": d},
                {"name": away, "price": a},
            ]}],
        })
    return {"home_team": home, "away_team": away, "commence_time": "2026-10-20T19:00:00Z", "bookmakers": casas}


def _selecao(analise, nome):
    return next(s for s in analise["selecoes"] if s["seleccao"] == nome)


class AnalisarEventoTests(unittest.TestCase):
    def test_casas_iguais_nao_dao_valor(self):
        precos = {f"Casa{i}": (2.0, 3.4, 3.8) for i in range(6)}
        analise = analisar_evento(_evento(precos))
        self.assertFalse(any(s["valor"] for s in analise["selecoes"]))

    def test_odd_acima_do_consenso_dá_valor(self):
        precos = {f"Casa{i}": (2.0, 3.4, 3.8) for i in range(5)}
        precos["Outra"] = (2.25, 3.4, 3.8)
        analise = analisar_evento(_evento(precos))
        selecao = _selecao(analise, "Benfica")
        self.assertEqual(selecao["casa"], "Outra")
        self.assertGreater(selecao["vantagem"], 0.02)
        self.assertTrue(selecao["valor"])

    def test_poucas_casas_nao_dao_valor(self):
        precos = {"Casa1": (2.0, 3.4, 3.8), "Casa2": (2.0, 3.4, 3.8), "Outra": (2.25, 3.4, 3.8)}
        analise = analisar_evento(_evento(precos), min_casas=5)
        self.assertFalse(_selecao(analise, "Benfica")["valor"])

    def test_odd_isolada_muito_alta_e_marcada_como_suspeita(self):
        precos = {f"Casa{i}": (2.0, 3.4, 3.8) for i in range(5)}
        precos["Erro"] = (3.0, 3.4, 3.8)
        analise = analisar_evento(_evento(precos))
        selecao = _selecao(analise, "Benfica")
        self.assertTrue(selecao["odd_suspeita"])
        self.assertFalse(selecao["valor"])

    def test_evento_sem_casas_devolve_none(self):
        self.assertIsNone(analisar_evento(_evento({})))


class RelatorioTests(unittest.TestCase):
    def test_resumo_sem_valor_diz_que_nao_ha_sinais(self):
        texto = texto_resumo([], "2026-10-18")
        self.assertIn("nenhuma seleção", texto)
        self.assertIn(AVISO, texto)

    def test_resumo_respeita_limite_do_telegram(self):
        precos = {f"Casa{i}": (2.0, 3.4, 3.8) for i in range(5)}
        precos["Outra"] = (2.25, 3.4, 3.8)
        analises = [analisar_evento(_evento(precos, home="A" * 5000))]
        self.assertLessEqual(len(texto_resumo(analises, "2026-10-18")), TELEGRAM_LIMITE)

    def test_html_escapa_nomes_das_equipas(self):
        precos = {f"Casa{i}": (2.0, 3.4, 3.8) for i in range(5)}
        analise = analisar_evento(_evento(precos, home="<script>x</script>"))
        pagina = html_site({"soccer_epl": [analise]}, "2026-10-18")
        self.assertNotIn("<script>x</script>", pagina)
        self.assertIn("&lt;script&gt;", pagina)

    def test_html_sem_jogos_mostra_mensagem(self):
        pagina = html_site({"soccer_epl": []}, "2026-10-18")
        self.assertIn("Sem jogos com odds disponíveis", pagina)


if __name__ == "__main__":
    unittest.main()
