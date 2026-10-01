#############################################
# KEŞKE: Tek Dönemlik Üretim Kararı
#############################################
# İş Problemi:
# Talep gerçekleşmeden üretim miktarını seçmek ve farklı karar kurallarının
# aynı koşullarda hangi miktarı önerdiğini karşılaştırmak.
# Rakamlar eğitim amaçlı kurgusaldır. Para birimi TL'dir.
# Kaynakların kapsamı ve sınırlamalar: KAYNAKLAR.txt
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Scenario:
    quantities: tuple[int, ...] = (100, 200, 300)
    demands: tuple[int, ...] = (100, 200, 300)
    probabilities: tuple[float, ...] = (0.3, 0.4, 0.3)
    price: float = 60
    unit_cost: float = 30
    salvage_value: float = 10

    def validate(self):
        values = (
            *self.quantities,
            *self.demands,
            *self.probabilities,
            self.price,
            self.unit_cost,
            self.salvage_value,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("Parametreler sonlu sayılar olmalıdır.")
        if len(self.demands) != len(self.probabilities) or not self.demands:
            raise ValueError("Her talep için bir olasılık gerekir.")
        if any(p < 0 for p in self.probabilities) or abs(sum(self.probabilities) - 1) > 1e-9:
            raise ValueError("Olasılıklar negatif olamaz ve toplamları 1 olmalıdır.")
        if not self.quantities or any(q < 0 for q in (*self.quantities, *self.demands)):
            raise ValueError("Miktarlar negatif olamaz; en az bir karar gerekir.")
        if not 0 <= self.salvage_value <= self.unit_cost <= self.price:
            raise ValueError("Bu senaryoda 0 ≤ kalan ürün değeri ≤ maliyet ≤ fiyat olmalıdır.")


#############################################
# GÖREV 1: Bir kararın kârını hesaplamak
#############################################
def profit(quantity, demand, scenario):
    """Satılan ve kalan ürün gelirinden bütün üretim maliyetini çıkarır."""
    sold = min(quantity, demand)
    remaining = quantity - sold
    return (
        sold * scenario.price + remaining * scenario.salvage_value - quantity * scenario.unit_cost
    )


#############################################
# GÖREV 2: Kâr ve pişmanlık tablolarını oluşturmak
# GÖREV 3: Karar kurallarını karşılaştırmak
#############################################
def analyze(scenario=Scenario()):
    """Bütün alternatifleri karşılaştırır; eşit skorda bütün kararları döndürür."""
    scenario.validate()
    matrix = []
    for quantity in scenario.quantities:
        profit_row = []
        for demand in scenario.demands:
            profit_row.append(profit(quantity, demand, scenario))
        matrix.append(profit_row)

    # Her sütun aynı talep durumunu temsil eder.
    best_by_state = []
    for demand_index in range(len(scenario.demands)):
        state_profits = [row[demand_index] for row in matrix]
        best_by_state.append(max(state_profits))

    regrets = []
    for profit_row in matrix:
        regret_row = []
        for demand_index, realized_profit in enumerate(profit_row):
            opportunity_loss = best_by_state[demand_index] - realized_profit
            regret_row.append(opportunity_loss)
        regrets.append(regret_row)

    expected_values = []
    for profit_row in matrix:
        expected_profit = 0
        for state_profit, probability in zip(profit_row, scenario.probabilities):
            expected_profit += state_profit * probability
        expected_values.append(expected_profit)
    scores = {
        "maximax": [max(row) for row in matrix],
        "maximin": [min(row) for row in matrix],
        "minimax_regret": [max(row) for row in regrets],
        "expected_value": expected_values,
    }
    # Eşit skorda bütün kazananları gösteririz; gizli bir tercih yapmayız.
    choices = {}
    for rule, values in scores.items():
        best = min(values) if rule == "minimax_regret" else max(values)
        choices[rule] = [
            q for q, score in zip(scenario.quantities, values) if abs(score - best) < 1e-9
        ]
    perfect_information_value = sum(v * p for v, p in zip(best_by_state, scenario.probabilities))
    return {
        "profit_matrix": matrix,
        "regret_matrix": regrets,
        "scores": scores,
        "choices": choices,
        "evpi": perfect_information_value - max(scores["expected_value"]),
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(analyze(), sort_dicts=False)
