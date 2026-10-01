import unittest
import numpy as np
from teknik_denetim import diagnose_errors
from model import Scenario, analyze
from tahminden_karara import demand_scenarios, cost_aware_quantity


class TechnicalAuditTest(unittest.TestCase):
    def test_constant_errors_are_not_reported_as_passing_independence(self):
        result = diagnose_errors(np.zeros(56))
        self.assertTrue(result["constant_errors"])
        self.assertIsNone(result["ljung_box_p_7"])
        self.assertIsNone(result["variance_shift_p"])

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            analyze(Scenario(probabilities=(float("nan"), 0.4, 0.6)))
        with self.assertRaises(ValueError):
            demand_scenarios(10, [])
        with self.assertRaises(ValueError):
            cost_aware_quantity([0, 1], 1, 0, 5)
        with self.assertRaises(ValueError):
            diagnose_errors([float("nan")] * 56)

    def test_persistent_errors_are_detected_in_a_controlled_fixture(self):
        # Uzun pozitif/negatif bloklar: zaman bağımlılığı açık olan kontrollü örnek.
        errors = np.repeat([1.0, -1.0, 1.0, -1.0], 14)
        result = diagnose_errors(errors)
        self.assertLess(result["ljung_box_p_7"], 0.01)


if __name__ == "__main__":
    unittest.main()
