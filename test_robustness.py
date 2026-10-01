"""Geriye dönük tekrar deneyinin zaman ve eşitlik kontrolleri."""

import unittest
import pandas as pd
from saglamlik_deneyi import evaluate_period, aggregate_cases


class RobustnessTest(unittest.TestCase):
    def make_series(self):
        return pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=448),
                "sales": [index % 9 for index in range(448)],
            }
        )

    def test_future_sales_cannot_change_order_policy(self):
        original = self.make_series()
        changed = original.copy()
        changed.loc[392:, "sales"] = 1000
        before = evaluate_period(original, 392)
        after = evaluate_period(changed, 392)
        self.assertEqual(before["quantity_max"], after["quantity_max"])
        self.assertLess(before["history_end"], before["test_start"])
        for initial, altered in zip(before["configurations"], after["configurations"]):
            for rule in initial["summary"]:
                self.assertEqual(
                    initial["summary"][rule]["mean_quantity"],
                    altered["summary"][rule]["mean_quantity"],
                )

    def test_zero_sales_ratios_are_undefined_and_ties_are_shared(self):
        series = self.make_series()
        series["sales"] = 0
        result = evaluate_period(series, 392)
        aggregate = aggregate_cases([result])
        for config in aggregate:
            self.assertAlmostEqual(
                sum(metric["fractional_wins"] for metric in config["metrics"].values()), 1
            )
            for metric in config["metrics"].values():
                self.assertEqual(metric["shared_wins"], 1)
                self.assertEqual(metric["sole_wins"], 0)
                self.assertEqual(metric["ratio_case_count"], 0)
                self.assertIsNone(metric["mean_profit_reference_ratio"])

    def test_equal_case_weighting_does_not_pool_volume(self):
        a = evaluate_period(self.make_series(), 392)
        b = evaluate_period(self.make_series(), 420)
        result = aggregate_cases([a, b])
        for position, config in enumerate(result):
            for rule, metric in config["metrics"].items():
                ratio_a = a["configurations"][position]["summary"][rule]["profit_reference_ratio"]
                ratio_b = b["configurations"][position]["summary"][rule]["profit_reference_ratio"]
                self.assertAlmostEqual(
                    metric["mean_profit_reference_ratio"], (ratio_a + ratio_b) / 2
                )
            self.assertAlmostEqual(
                sum(metric["fractional_wins"] for metric in config["metrics"].values()), 2
            )

    def test_incomplete_training_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_period(self.make_series(), 100)


if __name__ == "__main__":
    unittest.main()
