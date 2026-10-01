"""Tahmin değişkenlerine gelecekteki satışların sızmadığını kontrol eder."""

import unittest
import numpy as np
import pandas as pd
from satis_analizi import regression_design


class SalesAnalysisTest(unittest.TestCase):
    def test_future_sales_do_not_change_available_predictors(self):
        original = pd.DataFrame(
            {"date": pd.date_range("2020-01-01", periods=50), "sales": np.arange(50)}
        )
        changed = original.copy()
        changed.loc[30:, "sales"] = 9999
        before = regression_design(original)
        after = regression_design(changed)
        pd.testing.assert_frame_equal(before.iloc[:31], after.iloc[:31])
        self.assertEqual(before.loc[10, "past_7_mean"], 6)
        self.assertEqual(before.loc[10, "lag_7"], 3)


if __name__ == "__main__":
    unittest.main()
