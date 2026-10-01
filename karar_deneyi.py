"""Gerçek satış referansında, varsayımsal maliyetlerle karar karşılaştırması."""

from pathlib import Path
from collections import Counter
import json
import pandas as pd
from model import Scenario, analyze, profit

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "analysis"
RULES = ["maximax", "maximin", "minimax_regret", "expected_value"]
PRICE = 100  # Normalleştirilmiş para birimi; gerçek fiyat veya TL değildir.
WINDOW = 364


def make_distribution(values, support):
    """Gözlenen frekanslardan olasılık üret; kırpma yalnız duyarlılık deneyi."""
    low, high = 0, int(values.max())
    if support == "central":
        low = int(values.quantile(0.05))
        high = int(values.quantile(0.95))
        values = values.clip(low, high)
    counts = Counter(int(value) for value in values)
    demands = tuple(sorted(counts))
    probabilities = tuple(counts[demand] / len(values) for demand in demands)
    return demands, probabilities, low, high


def evaluate_config(history, test, quantities, cost_ratio, salvage_ratio, support):
    """Kurallar aynı eğitim bilgisi ve aynı günlük satış referansını kullanır."""
    cost = PRICE * cost_ratio
    salvage = cost * salvage_ratio
    policies = {}
    for weekday in range(7):
        observations = history.loc[history.date.dt.dayofweek == weekday, "sales"]
        demands, probabilities, low, high = make_distribution(observations, support)
        scenario = Scenario(quantities, demands, probabilities, PRICE, cost, salvage)
        decision = analyze(scenario)
        policies[weekday] = {
            "choices": decision["choices"],
            "sample_size": len(observations),
            "min_scenario": min(demands),
            "max_scenario": max(demands),
            "clip_low": low,
            "clip_high": high,
        }
    outcomes = {rule: [] for rule in RULES}
    for row in test.itertuples():
        weekday = row.date.dayofweek
        # Eşit optimum varsa en düşük miktarı uygula; tüm eşit seçimleri ayrıca sakla.
        scenario = Scenario(price=PRICE, unit_cost=cost, salvage_value=salvage)
        hindsight = max(profit(quantity, int(row.sales), scenario) for quantity in quantities)
        for rule in RULES:
            quantity = min(policies[weekday]["choices"][rule])
            realized = profit(quantity, int(row.sales), scenario)
            outcomes[rule].append(
                {
                    "date": str(row.date.date()),
                    "quantity": quantity,
                    "sales_reference": int(row.sales),
                    "profit": realized,
                    "remaining": max(0, quantity - int(row.sales)),
                    "uncovered_reference": max(0, int(row.sales) - quantity),
                    "regret": hindsight - realized,
                }
            )
    summaries = {}
    for rule, rows in outcomes.items():
        summaries[rule] = {
            metric: sum(row[metric] for row in rows)
            for metric in ["profit", "remaining", "uncovered_reference", "regret"]
        }
        summaries[rule]["mean_quantity"] = sum(row["quantity"] for row in rows) / len(rows)
    return {
        "cost_ratio": cost_ratio,
        "salvage_ratio": salvage_ratio,
        "support": support,
        "cost": cost,
        "salvage": salvage,
        "weekday_policies": policies,
        "summary": summaries,
        "daily": outcomes,
    }


def run_experiment(series, train_end):
    history = series.iloc[:train_end].tail(WINDOW)
    test = series.iloc[train_end + 28 :]
    # Alternatif kümesi test satışları görülmeden belirlenir; 0 sipariş mümkündür.
    quantities = tuple(range(int(history.sales.max()) + 1))
    configurations = []
    for cost_ratio in [0.3, 0.5, 0.7, 0.9]:
        for salvage_ratio in [0, 0.25, 0.5]:
            for support in ["full", "central"]:
                configurations.append(
                    evaluate_config(history, test, quantities, cost_ratio, salvage_ratio, support)
                )
    return {
        "price": PRICE,
        "unit": "normalleştirilmiş para birimi",
        "history_days": len(history),
        "history_start": str(history.date.iloc[0].date()),
        "history_end": str(history.date.iloc[-1].date()),
        "test_days": len(test),
        "quantity_min": 0,
        "quantity_max": max(quantities),
        "tie_policy": "Tüm eşit optimumlar saklanır; uygulamada en düşük miktar seçilir.",
        "configurations": configurations,
    }


if __name__ == "__main__":
    series = pd.read_csv(OUTPUT / "selected_sales.csv", parse_dates=["date"])
    report = json.loads((OUTPUT / "report.json").read_text(encoding="utf-8"))
    result = run_experiment(series, report["training_days"])
    (OUTPUT / "decision_experiment.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("24 maliyet/senaryo birleşimi hesaplandı. Test günleri:", result["test_days"])
    default = next(
        config
        for config in result["configurations"]
        if config["cost_ratio"] == 0.5
        and config["salvage_ratio"] == 0.25
        and config["support"] == "full"
    )
    print(json.dumps(default["summary"], indent=2))
