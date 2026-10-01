import unittest
from model import Scenario, analyze, profit


class DecisionModelTests(unittest.TestCase):
    def test_hand_calculated_scenario(self):
        result = analyze()
        self.assertEqual(
            result["profit_matrix"], [[3000, 3000, 3000], [1000, 6000, 6000], [-1000, 4000, 9000]]
        )
        self.assertEqual(
            result["choices"],
            {"maximax": [300], "maximin": [100], "minimax_regret": [200], "expected_value": [200]},
        )
        self.assertEqual(result["scores"]["expected_value"], [3000, 4500, 4000])
        self.assertAlmostEqual(result["evpi"], 1500)

    def test_no_demand_and_excess_demand(self):
        self.assertEqual(profit(100, 0, Scenario()), -2000)
        self.assertEqual(profit(100, 1000, Scenario()), 3000)

    def test_ties_are_visible(self):
        result = analyze(Scenario(quantities=(100, 100)))
        self.assertEqual(result["choices"]["maximax"], [100, 100])

    def test_invalid_probabilities(self):
        with self.assertRaises(ValueError):
            analyze(Scenario(probabilities=(0.3, 0.3, 0.3)))


if __name__ == "__main__":
    unittest.main()
