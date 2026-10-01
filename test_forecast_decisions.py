import unittest
import numpy as np
import pandas as pd
from model import Scenario, analyze
from tahminden_karara import forecast_before_test, demand_scenarios, cost_aware_quantity


class ForecastDecisionTest(unittest.TestCase):
    def test_future_sales_do_not_change_model_calibration_or_current_forecast(self):
        series = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=600),
                "sales": [index % 17 for index in range(600)],
            }
        )
        changed = series.copy()
        changed.loc[560:, "sales"] = 1000
        before = forecast_before_test(series, 560)
        after = forecast_before_test(changed, 560)
        self.assertEqual(before["selected"], after["selected"])
        self.assertEqual(before["selection_mae"], after["selection_mae"])
        np.testing.assert_array_equal(before["errors"], after["errors"])
        self.assertEqual(before["forecasts"][0], after["forecasts"][0])
        self.assertEqual(len(before["errors"]), 56)
        self.assertLess(before["fit_end"], before["selection_end"])
        self.assertLess(before["selection_end"], before["calibration_end"])
        self.assertLess(before["calibration_end"], str(series.date.iloc[560].date()))

    def test_critical_quantile_matches_exhaustive_profit_and_tie_rule(self):
        demands = np.array([0, 0, 1, 2, 2, 9, 12, 30])
        for cost in [0.3, 0.5, 0.7, 0.9]:
            for salvage in [0, 0.25, 0.5]:
                for cap in [0, 5, 40]:
                    expected = analyze(
                        Scenario(
                            tuple(range(cap + 1)),
                            tuple(demands),
                            tuple([1 / len(demands)] * len(demands)),
                            100,
                            100 * cost,
                            100 * cost * salvage,
                        )
                    )
                    self.assertEqual(
                        cost_aware_quantity(demands, cost, salvage, cap),
                        min(expected["choices"]["expected_value"]),
                    )

    def test_scenarios_clip_negative_sales_and_round_half_up(self):
        np.testing.assert_array_equal(demand_scenarios(2.5, np.array([-10, 0, 2])), [0, 3, 5])


if __name__ == "__main__":
    unittest.main()
