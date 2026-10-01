"""Geçmişte seçilen tahmin + ayrı hata kalibrasyonu + maliyete göre sipariş."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from satis_analizi import regression_design
from model import Scenario, profit

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data/analysis"
MODEL_NAMES = ["seasonal_naive", "past_28_mean", "lag_regression"]


def forecast_before_test(series, test_start, training_days=364, calibration_days=56):
    """Geçmiş eğitim, 28 gün seçim, ayrı hata kalibrasyonu ve 28 gün test."""
    if training_days < 100 or calibration_days < 14:
        raise ValueError("Eğitim en az 100, hata kalibrasyonu en az 14 gün olmalı.")
    fit_end = test_start - calibration_days - 28
    design = regression_design(series)
    fitting = design.iloc[max(7, fit_end - training_days) : fit_end].dropna()
    if len(fitting) != training_days or test_start + 28 > len(series):
        raise ValueError("Yeterli eğitim ve test geçmişi gerekiyor.")
    model = sm.OLS(series.loc[fitting.index, "sales"].astype(float), fitting).fit()
    candidates = pd.DataFrame(
        {
            "seasonal_naive": series.sales.shift(7),
            "past_28_mean": series.sales.shift(1).rolling(28).mean(),
            "lag_regression": model.predict(design).clip(lower=0),
        }
    )
    selection = slice(fit_end, fit_end + 28)
    scores = {
        name: float((series.sales.iloc[selection] - candidates[name].iloc[selection]).abs().mean())
        for name in MODEL_NAMES
    }
    selected = min(MODEL_NAMES, key=lambda name: scores[name])
    calibration = slice(fit_end + 28, test_start)
    errors = (series.sales.iloc[calibration] - candidates[selected].iloc[calibration]).to_numpy(
        float
    )
    test_forecasts = candidates[selected].iloc[test_start : test_start + 28].to_numpy(float)
    return {
        "selected": selected,
        "selection_mae": scores,
        "errors": errors,
        "forecasts": test_forecasts,
        "calibration_forecasts": candidates[selected].iloc[calibration].to_numpy(float),
        "training_rank": int(np.linalg.matrix_rank(fitting.to_numpy())),
        "training_columns": len(fitting.columns),
        "fit_end": str(series.date.iloc[fit_end - 1].date()),
        "selection_end": str(series.date.iloc[fit_end + 27].date()),
        "calibration_end": str(series.date.iloc[test_start - 1].date()),
    }


def demand_scenarios(forecast, errors):
    """Her geçmiş hata eşit ağırlıklı; negatif senaryolar sıfıra kırpılır."""
    errors = np.asarray(errors, dtype=float)
    if not np.isfinite(forecast) or errors.size == 0 or not np.isfinite(errors).all():
        raise ValueError("Tahmin ve hata havuzu sonlu ve boş olmayan sayılar olmalı.")
    return np.floor(np.maximum(0, forecast + errors) + 0.5).astype(int)


def cost_aware_quantity(demands, cost_ratio, salvage_ratio, quantity_max):
    """Newsvendor ampirik kritik kantili; eşit optimumda küçük miktar."""
    demands = np.asarray(demands, dtype=float)
    if not 0 < cost_ratio < 1 or not 0 <= salvage_ratio < 1:
        raise ValueError("Bu deneyde 0 < maliyet/fiyat < 1 ve 0 ≤ kalan/maliyet < 1 olmalı.")
    if quantity_max < 0 or int(quantity_max) != quantity_max:
        raise ValueError("Sipariş sınırı negatif olmayan tam sayı olmalı.")
    if demands.size == 0 or not np.isfinite(demands).all() or (demands < 0).any():
        raise ValueError("Senaryolar sonlu, negatif olmayan ve boş olmayan sayılar olmalı.")
    if not np.equal(demands, np.floor(demands)).all():
        raise ValueError("Sipariş deneyinin satış senaryoları tam sayı olmalı.")
    price = 100
    cost = price * cost_ratio
    salvage = cost * salvage_ratio
    critical_ratio = (price - cost) / (price - salvage)
    quantity = int(np.quantile(demands, critical_ratio, method="inverted_cdf"))
    return min(quantity_max, max(0, quantity))


def evaluate_linked_case(series, test_start, baseline_case, training_days=364, calibration_days=56):
    fitted = forecast_before_test(series, test_start, training_days, calibration_days)
    test = series.iloc[test_start : test_start + 28]
    cap = int(series.sales.iloc[test_start - 364 : test_start].max())
    results = []
    for baseline in baseline_case["configurations"]:
        if baseline["support"] != "full":
            continue
        cost, salvage = baseline["cost_ratio"], baseline["salvage_ratio"]
        scenario = Scenario(price=100, unit_cost=100 * cost, salvage_value=100 * cost * salvage)
        outcomes = {"forecast_point": [], "forecast_distribution": []}
        for position, row in enumerate(test.itertuples()):
            forecast = float(fitted["forecasts"][position])
            demands = demand_scenarios(forecast, fitted["errors"])
            point_quantity = min(cap, int(np.floor(forecast + 0.5)))
            adaptive_quantity = cost_aware_quantity(demands, cost, salvage, cap)
            perfect_profit = profit(min(cap, int(row.sales)), int(row.sales), scenario)
            for name, quantity in [
                ("forecast_point", point_quantity),
                ("forecast_distribution", adaptive_quantity),
            ]:
                realized = profit(quantity, int(row.sales), scenario)
                outcomes[name].append(
                    {
                        "date": str(row.date.date()),
                        "forecast": forecast,
                        "quantity": quantity,
                        "sales_reference": int(row.sales),
                        "profit": realized,
                        "remaining": max(0, quantity - int(row.sales)),
                        "uncovered_reference": max(0, int(row.sales) - quantity),
                        "regret": perfect_profit - realized,
                    }
                )
        summaries = dict(baseline["summary"])
        reference_revenue = float(test.sales.sum() * 100)
        for name, rows in outcomes.items():
            summary = {
                metric: sum(row[metric] for row in rows)
                for metric in ["profit", "remaining", "uncovered_reference", "regret"]
            }
            summary["mean_quantity"] = sum(row["quantity"] for row in rows) / len(rows)
            summary["profit_reference_ratio"] = (
                summary["profit"] / reference_revenue if reference_revenue else None
            )
            summaries[name] = summary
        results.append(
            {"cost_ratio": cost, "salvage_ratio": salvage, "summary": summaries, "daily": outcomes}
        )
    return {
        "item": baseline_case["item"],
        "store": baseline_case["store"],
        "period": baseline_case["period"],
        "test_start": baseline_case["test_start"],
        "test_end": baseline_case["test_end"],
        "selected_model": fitted["selected"],
        "selection_mae": fitted["selection_mae"],
        "test_mae": float(np.mean(np.abs(test.sales.to_numpy() - fitted["forecasts"]))),
        "calibration_size": len(fitted["errors"]),
        "quantity_max": cap,
        "fit_end": fitted["fit_end"],
        "selection_end": fitted["selection_end"],
        "calibration_end": fitted["calibration_end"],
        "configurations": results,
    }


if __name__ == "__main__":
    panel = pd.read_csv(OUTPUT / "robustness_panel.csv", parse_dates=["date"])
    baseline = json.loads((OUTPUT / "robustness_report.json").read_text(encoding="utf-8"))
    cases = []
    for sample in baseline["cases"]:
        series = panel.loc[
            (panel.item_id == sample["item"]) & (panel.store_id == sample["store"])
        ].reset_index(drop=True)
        test_start = int(series.index[series.date == pd.Timestamp(sample["test_start"])][0])
        cases.append(evaluate_linked_case(series, test_start, sample))
    report = {
        "cases": cases,
        "case_count": len(cases),
        "cost_configuration_count": 12,
        "protocol": "364 fit / 28 model selection / 56 residual calibration / 28 rolling one-day test",
        "limitations": [
            "Residuals are pooled; serial dependence and conditional error changes are not modeled.",
            "Scenarios are empirical approximations, not guaranteed predictive intervals.",
            "Previously inspected test periods; exploratory evaluation, not fresh external validation.",
        ],
    }
    (OUTPUT / "forecast_decisions.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    selected = [case["configurations"][4] for case in cases]
    print("30 ürün-dönemde tahmin, senaryo ve maliyete göre karar hesaplandı.")
    print(
        "Dağılımlı karar, doğrudan tahminden daha yüksek kâr:",
        sum(
            config["summary"]["forecast_distribution"]["profit"]
            > config["summary"]["forecast_point"]["profit"] + 1e-8
            for config in selected
        ),
    )
