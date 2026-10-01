"""Karar deneyinin kritik oran, muhasebe ve bilgi sınırı kontrolleri."""

import unittest
import pandas as pd
from model import Scenario, analyze
from karar_deneyi import make_distribution, run_experiment


class DecisionExperimentTest(unittest.TestCase):
    def test_expected_value_matches_newsvendor_critical_fractile(self):
        # (p-c)/(p-s)=0.5; dağılımın en küçük 0.5 kantili 2.
        scenario = Scenario(tuple(range(6)), (0, 2, 5), (0.2, 0.5, 0.3), 100, 60, 20)
        self.assertEqual(analyze(scenario)["choices"]["expected_value"], [2])

    def test_clipping_preserves_probability_mass(self):
        values = pd.Series([0] * 10 + [10] * 80 + [100] * 10)
        demands, probabilities, _, _ = make_distribution(values, "central")
        self.assertAlmostEqual(sum(probabilities), 1)
        self.assertEqual(len(demands), len(probabilities))

    def test_test_sales_do_not_change_policies_and_regret_reconciles(self):
        series = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=420),
                "sales": [index % 11 for index in range(420)],
            }
        )
        changed = series.copy()
        changed.loc[392:, "sales"] = 900
        before = run_experiment(series, 364)
        after = run_experiment(changed, 364)
        self.assertEqual(before["quantity_max"], after["quantity_max"])
        for original, altered in zip(before["configurations"], after["configurations"]):
            self.assertEqual(original["weekday_policies"], altered["weekday_policies"])
            benchmark_totals = []
            for rule, summary in original["summary"].items():
                self.assertGreaterEqual(summary["regret"], -1e-9)
                benchmark_totals.append(summary["profit"] + summary["regret"])
                for day in original["daily"][rule]:
                    self.assertEqual(
                        day["quantity"] - day["remaining"],
                        day["sales_reference"] - day["uncovered_reference"],
                    )
            self.assertTrue(
                all(abs(value - benchmark_totals[0]) < 1e-9 for value in benchmark_totals)
            )


if __name__ == "__main__":
    unittest.main()
