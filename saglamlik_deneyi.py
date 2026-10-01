"""Önceden sabitlenen ürün ve dönemlerde karar kurallarını tekrar sınar."""

from pathlib import Path
import json
import pandas as pd
from karar_deneyi import evaluate_config, RULES, PRICE, WINDOW

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "analysis"
PRODUCTS = ["FOODS_1_001", "HOBBIES_1_001", "HOUSEHOLD_1_001"]
STORES = ["CA_1", "TX_1", "WI_1"]
# Kimliklerden seçildi; başarı, satış miktarı veya test sonuçları kullanılmadı.
PAIRS = [(item, store) for item in PRODUCTS for store in STORES] + [("FOODS_3_090", "CA_1")]
TEST_LENGTH = 28
PERIOD_COUNT = 3


def load_panel():
    """Görev 1: Sabit 10 çift için günlük paneli oluştur."""
    selected = []
    wanted = set(PAIRS)
    for chunk in pd.read_csv(ROOT / "data/raw/sales_train_validation.csv", chunksize=1000):
        mask = [(item, store) in wanted for item, store in zip(chunk.item_id, chunk.store_id)]
        selected.append(chunk.loc[mask])
    wide = pd.concat(selected, ignore_index=True)
    if len(wide) != len(wanted) or wide.duplicated(["item_id", "store_id"]).any():
        raise ValueError("Sabit ürün-mağaza listesi tekil ve eksiksiz olmalı.")
    days = [column for column in wide if column.startswith("d_")]
    if wide[days].isna().any().any() or (wide[days] < 0).any().any():
        raise ValueError("Eksik veya negatif satış var.")
    calendar = pd.read_csv(ROOT / "data/raw/calendar.csv", parse_dates=["date"])
    panel = wide.melt(
        id_vars=["item_id", "store_id"], value_vars=days, var_name="d", value_name="sales"
    )
    panel = panel.merge(calendar[["d", "date"]], on="d", validate="many_to_one")
    return panel.sort_values(["item_id", "store_id", "date"]).reset_index(drop=True)


def evaluate_period(series, test_start):
    """Görev 2: Her test başlangıcında yalnız önceki 52 haftayı kullan."""
    history = series.iloc[max(0, test_start - WINDOW) : test_start].copy()
    test = series.iloc[test_start : test_start + TEST_LENGTH].copy()
    if len(history) != WINDOW or len(test) != TEST_LENGTH:
        raise ValueError("52 haftalık geçmiş ve 28 günlük test gerekiyor.")
    if history.date.max() >= test.date.min():
        raise ValueError("Eğitim ve test zamanları kesişiyor.")
    if not series.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Düzenli günlük seri gerekiyor.")
    quantities = tuple(range(int(history.sales.max()) + 1))
    reference_revenue = float(test.sales.sum() * PRICE)
    configurations = []
    for cost in [0.3, 0.5, 0.7, 0.9]:
        for salvage in [0, 0.25, 0.5]:
            for support in ["full", "central"]:
                result = evaluate_config(history, test, quantities, cost, salvage, support)
                summaries = result["summary"]
                best_profit = max(summary["profit"] for summary in summaries.values())
                winners = [
                    rule for rule in RULES if abs(summaries[rule]["profit"] - best_profit) < 1e-8
                ]
                for summary in summaries.values():
                    # Referans gelir, fiyat × gözlenen satış; gerçekleşen işletme geliri değil.
                    summary["profit_reference_ratio"] = (
                        summary["profit"] / reference_revenue if reference_revenue else None
                    )
                    summary["regret_reference_ratio"] = (
                        summary["regret"] / reference_revenue if reference_revenue else None
                    )
                configurations.append(
                    {
                        "cost_ratio": cost,
                        "salvage_ratio": salvage,
                        "support": support,
                        "summary": summaries,
                        "winners": winners,
                    }
                )
    return {
        "history_start": str(history.date.iloc[0].date()),
        "history_end": str(history.date.iloc[-1].date()),
        "test_start": str(test.date.iloc[0].date()),
        "test_end": str(test.date.iloc[-1].date()),
        "quantity_max": max(quantities),
        "test_sales": int(test.sales.sum()),
        "history_zero_fraction": float(history.sales.eq(0).mean()),
        "configurations": configurations,
    }


def aggregate_cases(cases):
    """Görev 3: Ürün hacminden bağımsız, eşit ağırlıklı betimsel karşılaştırma."""
    aggregate = []
    for position in range(24):
        configurations = [case["configurations"][position] for case in cases]
        first = configurations[0]
        metrics = {}
        for rule in RULES:
            ratios = [
                config["summary"][rule]["profit_reference_ratio"] for config in configurations
            ]
            ratios = [value for value in ratios if value is not None]
            regrets = [
                config["summary"][rule]["regret_reference_ratio"] for config in configurations
            ]
            regrets = [value for value in regrets if value is not None]
            metrics[rule] = {
                "sole_wins": sum(config["winners"] == [rule] for config in configurations),
                "shared_wins": sum(
                    rule in config["winners"] and len(config["winners"]) > 1
                    for config in configurations
                ),
                "fractional_wins": sum(
                    1 / len(config["winners"])
                    for config in configurations
                    if rule in config["winners"]
                ),
                "loss_cases": sum(
                    config["summary"][rule]["profit"] < -1e-8 for config in configurations
                ),
                "mean_profit_reference_ratio": sum(ratios) / len(ratios) if ratios else None,
                "mean_regret_reference_ratio": sum(regrets) / len(regrets) if regrets else None,
                "ratio_case_count": len(ratios),
            }
        aggregate.append(
            {
                "cost_ratio": first["cost_ratio"],
                "salvage_ratio": first["salvage_ratio"],
                "support": first["support"],
                "metrics": metrics,
            }
        )
    return aggregate


def main():
    panel = load_panel()
    cases = []
    for item, store in PAIRS:
        series = panel.loc[(panel.item_id == item) & (panel.store_id == store)].reset_index(
            drop=True
        )
        for period in range(PERIOD_COUNT):
            test_start = len(series) - (PERIOD_COUNT - period) * TEST_LENGTH
            result = evaluate_period(series, test_start)
            result.update({"item": item, "store": store, "period": period + 1})
            cases.append(result)
        print("Tamamlandı:", item, store, flush=True)
    report = {
        "pair_count": len(PAIRS),
        "period_count": PERIOD_COUNT,
        "case_count": len(cases),
        "configuration_count": 24,
        "comparison_count": len(cases) * 24,
        "pairs": PAIRS,
        "selection": "Fixed identifiers; no filtering on sales or performance.",
        "history_days": WINDOW,
        "test_days_per_period": TEST_LENGTH,
        "cases": cases,
        "aggregate": aggregate_cases(cases),
        "limitations": [
            "Descriptive extension; original item/test results were already observed.",
            "Products are not a random representative sample of M5.",
            "Shared dates and overlapping histories imply dependent comparisons.",
            "No confidence intervals or statistical superiority claim.",
            "Observed sales proxy, hypothetical costs; forecast regression not linked.",
        ],
    }
    (OUTPUT / "robustness_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    panel.to_csv(OUTPUT / "robustness_panel.csv", index=False)
    print(json.dumps(report["aggregate"][8], indent=2))


if __name__ == "__main__":
    main()
