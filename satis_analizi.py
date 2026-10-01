"""Görev sırasıyla M5 veri denetimi ve yalnızca eğitim verisinde tanılar."""

from pathlib import Path
import json
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss, acf
from statsmodels.tsa.seasonal import STL
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "analysis"
# Ürün seçimi test sonuçları görülmeden sabitlendi.
ITEM = "FOODS_3_090"
STORE = "CA_1"
HOLDOUT_DAYS = 56


def load_sales():
    """Görev 1: Geniş satış tablosunu denetle, tek seriyi çıkar."""
    selected = []
    row_count = 0
    missing_count = 0
    keys = set()
    for chunk in pd.read_csv(RAW / "sales_train_validation.csv", chunksize=1000):
        days = [column for column in chunk if column.startswith("d_")]
        row_count += len(chunk)
        missing_count += int(chunk[days].isna().sum().sum())
        for key in zip(chunk["item_id"], chunk["store_id"]):
            if key in keys:
                raise ValueError("Tekrarlanan ürün-mağaza anahtarı.")
            keys.add(key)
        if (chunk[days] < 0).any().any():
            raise ValueError("Negatif satış bulundu.")
        selected.append(chunk.loc[(chunk.item_id == ITEM) & (chunk.store_id == STORE)])
    product = pd.concat(selected)
    if len(product) != 1:
        raise ValueError("Önceden seçilen ürün-mağaza bulunamadı veya tekil değil.")
    series = product.melt(value_vars=days, var_name="d", value_name="sales")
    calendar = pd.read_csv(RAW / "calendar.csv", parse_dates=["date"])
    series = series.merge(calendar[["d", "date", "wm_yr_wk"]], on="d", validate="one_to_one")
    prices = []
    for chunk in pd.read_csv(RAW / "sell_prices.csv", chunksize=100000):
        prices.append(chunk.loc[(chunk.item_id == ITEM) & (chunk.store_id == STORE)])
    prices = pd.concat(prices)
    series = series.merge(
        prices[["wm_yr_wk", "sell_price"]], on="wm_yr_wk", how="left", validate="many_to_one"
    )
    series = series.sort_values("date").reset_index(drop=True)
    if not series.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Günlük tarih aralığında boşluk var.")
    audit = {
        "units": row_count,
        "days_per_unit": len(days),
        "missing_sales_cells": missing_count,
        "observed_grid_balanced": missing_count == 0,
        "note": "Dengeli kayıt ızgarası, her ürünün her gün satışta veya stokta olduğunu göstermez.",
        "selected_item": ITEM,
        "selected_store": STORE,
        "missing_price_days": int(series.sell_price.isna().sum()),
    }
    return series, audit


def diagnose(train):
    """Görev 2: Sabit ve trendli testleri birlikte raporla."""
    results = {}
    for specification in ["c", "ct"]:
        adf = adfuller(train.sales, regression=specification, autolag="AIC", result_object=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            stationarity = kpss(
                train.sales, regression=specification, nlags="auto", result_object=False
            )
        results[specification] = {
            "adf_statistic": float(adf[0]),
            "adf_p": float(adf[1]),
            "adf_lags": int(adf[2]),
            "kpss_statistic": float(stationarity[0]),
            "kpss_p": float(stationarity[1]),
            "kpss_lags": int(stationarity[2]),
            "kpss_warnings": [str(w.message) for w in caught],
        }
    correlations = acf(train.sales, nlags=28, fft=True)
    decomposition = STL(train.sales.to_numpy(dtype=float), period=7, robust=True).fit()
    denominator = np.var(decomposition.seasonal + decomposition.resid)
    strength = max(0.0, 1 - np.var(decomposition.resid) / denominator) if denominator else 0.0
    return {
        "tests": results,
        "acf_lag_1": float(correlations[1]),
        "acf_lag_7": float(correlations[7]),
        "weekly_stl_strength": float(strength),
        "zero_sales_fraction": float(train.sales.eq(0).mean()),
    }, decomposition


def regression_design(series):
    """Görev 3: Bugünün satışını kullanmadan açıklayıcı değişken üret."""
    design = pd.DataFrame(index=series.index)
    design["lag_1"] = series.sales.shift(1)
    design["lag_7"] = series.sales.shift(7)
    design["past_7_mean"] = series.sales.shift(1).rolling(7).mean()
    weekdays = pd.Categorical(series.date.dt.dayofweek, categories=range(7))
    dummies = pd.get_dummies(weekdays, prefix="weekday", drop_first=True, dtype=float)
    return sm.add_constant(pd.concat([design, dummies], axis=1)).astype(float)


def compare_forecasts(series, train_end):
    """Görev 4: Bir gün ileri tahmin; geçmiş günler gerçekleşince güncellenir."""
    design = regression_design(series)
    valid_train = design.iloc[:train_end].dropna()
    fitted = sm.OLS(series.loc[valid_train.index, "sales"].astype(float), valid_train).fit()
    vif = {
        column: float(variance_inflation_factor(valid_train.to_numpy(), position))
        for position, column in enumerate(valid_train.columns)
        if column != "const"
    }
    predictions = pd.DataFrame(
        {
            "date": series.date,
            "actual": series.sales,
            "seasonal_naive": series.sales.shift(7),
            "past_28_mean": series.sales.shift(1).rolling(28).mean(),
            "lag_regression": fitted.predict(design).clip(lower=0),
        }
    )
    scores = {}
    for name in ["seasonal_naive", "past_28_mean", "lag_regression"]:
        scores[name] = {}
        for label, start, end in [
            ("validation", train_end, train_end + 28),
            ("test", train_end + 28, len(series)),
        ]:
            sample = predictions.iloc[start:end]
            scores[name][label + "_mae"] = float((sample.actual - sample[name]).abs().mean())
    winner = min(scores, key=lambda name: scores[name]["validation_mae"])
    return predictions.iloc[train_end:], {
        "mae": scores,
        "selected_on_validation": winner,
        "vif_training_only": vif,
        "protocol": "Rolling one-day-ahead; coefficients fitted on training only.",
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    series, audit = load_sales()
    train_end = len(series) - HOLDOUT_DAYS
    train = series.iloc[:train_end]
    diagnostics, decomposition = diagnose(train)
    predictions, comparison = compare_forecasts(series, train_end)
    report = {
        "audit": audit,
        "training_days": len(train),
        "training_end": str(train.date.iloc[-1].date()),
        "validation_days": 28,
        "test_days": 28,
        "diagnostics": diagnostics,
        "comparison": comparison,
        "limitations": [
            "Observed sales are not uncensored demand.",
            "Costs are not provided by M5; decision profits will require explicit assumptions.",
            "Weekly STL does not test annual seasonality.",
            "ADF/KPSS alone do not select a forecasting model.",
        ],
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    predictions.to_csv(OUTPUT / "holdout_predictions.csv", index=False)
    series.to_csv(OUTPUT / "selected_sales.csv", index=False)
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), constrained_layout=True)
    axes[0].plot(train.date, train.sales, alpha=0.4, linewidth=0.6, label="Daily sales")
    axes[0].plot(train.date, train.sales.rolling(28).mean(), color="#2b3a30", label="28-day mean")
    axes[0].set_title(f"{ITEM} / {STORE} — training data only")
    axes[0].legend()
    correlations = acf(train.sales, nlags=28, fft=True)
    axes[1].stem(range(1, 29), correlations[1:])
    axes[1].set(title="Autocorrelation (descriptive)", xlabel="Lag in days")
    axes[2].plot(train.date.iloc[-84:], decomposition.seasonal[-84:], color="#2b3a30")
    axes[2].set_title("Weekly STL component — final 12 training weeks")
    fig.savefig(OUTPUT / "sales_diagnostics.png", dpi=150)
    plt.close(fig)
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
