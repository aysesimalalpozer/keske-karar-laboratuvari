###############################################################
# KEŞKE — Hata Tanıları ve Pencere Duyarlılığı
###############################################################
# İş Problemi: Geçmiş tahmin hatalarının senaryo olarak kullanılması ne kadar
# savunulabilir? Başlangıç pencere seçimleri sonuçları ne kadar etkiliyor?
# Bu denetim mevcut testleri tekrar kullanır; yeni dış doğrulama değildir.

from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import levene
from statsmodels.stats.diagnostic import acorr_ljungbox
from tahminden_karara import forecast_before_test, evaluate_linked_case

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data/analysis"
TRAINING_WINDOWS = [182, 364, 728]
CALIBRATION_WINDOWS = [28, 56, 84]


###############################################################
# GÖREV 1: Yalnız test öncesi hata havuzunu incelemek
###############################################################
def diagnose_errors(errors):
    errors = np.asarray(errors, dtype=float)
    if len(errors) < 28 or not np.isfinite(errors).all():
        raise ValueError("Tanılar en az 28 sonlu hata gözlemi gerektirir.")
    if np.ptp(errors) == 0:
        return {
            "mean_error": float(errors.mean()),
            "constant_errors": True,
            "ljung_box_p_7": None,
            "ljung_box_p_14": None,
            "variance_shift_p": None,
            "warnings": ["Sabit hata: bağımlılık/varyans testleri tanımsız."],
        }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        lb = acorr_ljungbox(errors, lags=[7, 14], model_df=0, return_df=True)
        split = len(errors) // 2
        variance = levene(errors[:split], errors[split:], center="median")

    def finite_or_none(value):
        return float(value) if np.isfinite(value) else None

    return {
        "mean_error": float(errors.mean()),
        "constant_errors": False,
        "ljung_box_p_7": finite_or_none(lb.loc[7, "lb_pvalue"]),
        "ljung_box_p_14": finite_or_none(lb.loc[14, "lb_pvalue"]),
        "variance_shift_p": finite_or_none(variance.pvalue),
        "warnings": [str(w.message) for w in caught],
    }


###############################################################
# GÖREV 2: Aynı test ve maliyetlerde pencere seçimlerini değiştirmek
###############################################################
def main():
    panel = pd.read_csv(OUTPUT / "robustness_panel.csv", parse_dates=["date"])
    baseline = json.loads((OUTPUT / "robustness_report.json").read_text(encoding="utf-8"))
    diagnostics = []
    sensitivity = []
    for sample in baseline["cases"]:
        series = panel.loc[
            (panel.item_id == sample["item"]) & (panel.store_id == sample["store"])
        ].reset_index(drop=True)
        test_start = int(series.index[series.date == pd.Timestamp(sample["test_start"])][0])
        fitted = forecast_before_test(series, test_start)
        diagnostics.append(
            {
                "item": sample["item"],
                "store": sample["store"],
                "period": sample["period"],
                "selected_model": fitted["selected"],
                "training_rank": fitted["training_rank"],
                "training_columns": fitted["training_columns"],
                **diagnose_errors(fitted["errors"]),
            }
        )
        for training in TRAINING_WINDOWS:
            for calibration in CALIBRATION_WINDOWS:
                linked = evaluate_linked_case(series, test_start, sample, training, calibration)
                for config in linked["configurations"]:
                    point = config["summary"]["forecast_point"]["profit"]
                    distribution = config["summary"]["forecast_distribution"]["profit"]
                    sensitivity.append(
                        {
                            "item": sample["item"],
                            "store": sample["store"],
                            "period": sample["period"],
                            "training_days": training,
                            "calibration_days": calibration,
                            "selected_model": linked["selected_model"],
                            "cost_ratio": config["cost_ratio"],
                            "salvage_ratio": config["salvage_ratio"],
                            "profit_difference": distribution - point,
                        }
                    )
        print("Denetlendi:", sample["item"], sample["store"], sample["period"], flush=True)
    summaries = []
    for training in TRAINING_WINDOWS:
        for calibration in CALIBRATION_WINDOWS:
            for cost in [0.3, 0.5, 0.7, 0.9]:
                for salvage in [0, 0.25, 0.5]:
                    rows = [
                        row
                        for row in sensitivity
                        if row["training_days"] == training
                        and row["calibration_days"] == calibration
                        and row["cost_ratio"] == cost
                        and row["salvage_ratio"] == salvage
                    ]
                    summaries.append(
                        {
                            "training_days": training,
                            "calibration_days": calibration,
                            "cost_ratio": cost,
                            "salvage_ratio": salvage,
                            "higher": sum(row["profit_difference"] > 1e-8 for row in rows),
                            "equal": sum(abs(row["profit_difference"]) <= 1e-8 for row in rows),
                            "lower": sum(row["profit_difference"] < -1e-8 for row in rows),
                        }
                    )
    audit = {
        "diagnostics": diagnostics,
        "sensitivity": summaries,
        "case_count": len(diagnostics),
        "window_pairs": 9,
        "comparison_count": len(sensitivity),
        "notes": [
            "Ljung-Box tests calibration forecast errors, not raw sales.",
            "model_df=0: frozen model fitted in preceding disjoint training block; nominal screening p-values.",
            "Levene/Brown-Forsythe compares first/second calibration halves; dependence affects its nominal p-value.",
            "No multiple-testing correction or proof of independent identically distributed errors.",
            "Sensitivity is exploratory, not hyperparameter tuning or external validation.",
        ],
    }
    (OUTPUT / "technical_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    print("Denetim tamamlandı; karşılaştırma:", len(sensitivity))


if __name__ == "__main__":
    main()
