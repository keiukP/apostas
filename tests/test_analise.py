import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analise import backtest, expected_value, find_value_bets, implied_probs, kelly_fraction  # noqa: E402


class ImpliedProbsTests(unittest.TestCase):
    def test_removes_overround(self):
        probs = implied_probs([2.0, 3.0, 4.0])
        self.assertAlmostEqual(sum(probs), 1.0)
        self.assertGreater(probs[0], probs[1])

    def test_rejects_invalid_odds(self):
        with self.assertRaises(ValueError):
            implied_probs([1.0, 2.0])


class ExpectedValueTests(unittest.TestCase):
    def test_fair_bet_has_zero_ev(self):
        self.assertAlmostEqual(expected_value(0.5, 2.0), 0.0)

    def test_positive_ev_when_prob_above_implied(self):
        self.assertGreater(expected_value(0.6, 2.0), 0)


class KellyTests(unittest.TestCase):
    def test_negative_edge_gives_zero(self):
        self.assertEqual(kelly_fraction(0.4, 2.0), 0.0)

    def test_is_capped(self):
        self.assertEqual(kelly_fraction(0.9, 3.0, cap=0.05), 0.05)


class ValueBetTests(unittest.TestCase):
    def test_only_selections_with_edge_are_returned(self):
        bets = find_value_bets({"casa": 0.55, "empate": 0.25, "fora": 0.20},
                               {"casa": 2.0, "empate": 3.5, "fora": 4.0}, min_edge=0.03)
        self.assertEqual([b["selection"] for b in bets], ["casa"])

    def test_ignores_selections_without_odds(self):
        self.assertEqual(find_value_bets({"casa": 0.9}, {}), [])


class BacktestTests(unittest.TestCase):
    def test_reports_losses_too(self):
        result = backtest([{"odds": 2.0, "won": True}, {"odds": 2.0, "won": False}])
        self.assertEqual(result["profit"], 0.0)
        self.assertEqual(result["hit_rate_pct"], 50.0)

    def test_empty_history(self):
        self.assertEqual(backtest([])["n"], 0)


if __name__ == "__main__":
    unittest.main()
