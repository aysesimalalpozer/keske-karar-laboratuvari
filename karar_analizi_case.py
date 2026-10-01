#############################################
# KEŞKE — Karar Analizi Çalışma Dosyası
#############################################
# İş Problemi:
# Talep belli olmadan 100, 200 veya 300 ürün üretmek.
# Amaç: Aynı kâr tablosundan farklı karar kurallarıyla seçim yapmak.
# Veri Hikayesi: Gerçek veri yoktur; öğrenme amaçlı kurgusal senaryodur.
# Bu dosyayı bölüm bölüm inceleyebilir veya baştan sona çalıştırabilirsin.

from model import Scenario, analyze, profit

#############################################
# GÖREV 1: Parametreleri Tanımak
#############################################
# quantities: Bizim seçebildiğimiz üretim miktarları.
# demands: Kontrolümüz dışında gerçekleşen talep durumları.
# probabilities: Bu durumlara atadığımız olasılıklar; toplamları 1 olmalı.
# price: Bir ürünün satış fiyatı (TL/ürün).
# unit_cost: Bir ürünün üretim maliyeti (TL/ürün).
# salvage_value: Satılmayan ürünün dönem sonunda elde edilen değeri.

scenario = Scenario(
    quantities=(100, 200, 300),
    demands=(100, 200, 300),
    probabilities=(0.30, 0.40, 0.30),
    price=60,
    unit_cost=30,
    salvage_value=10,
)

#############################################
# GÖREV 2: Tek Bir Hesabı Kontrol Etmek
#############################################
# 200 üretip 100 satmak: 100*60 + 100*10 - 200*30 = 1000 TL.
example_profit = profit(quantity=200, demand=100, scenario=scenario)
print("Örnek kâr (TL):", example_profit)

#############################################
# GÖREV 3: Kâr ve Pişmanlık Tablolarını İncelemek
#############################################
results = analyze(scenario)
print("Talep sütunları:", scenario.demands)
for quantity, profit_row, regret_row in zip(
    scenario.quantities, results["profit_matrix"], results["regret_matrix"]
):
    print("Üretim:", quantity, "| Kârlar:", profit_row, "| Pişmanlıklar:", regret_row)

#############################################
# GÖREV 4: Kararları ve Skorları Yorumlamak
#############################################
for rule_name, selected_quantities in results["choices"].items():
    print(rule_name, "| Skorlar:", results["scores"][rule_name], "| Seçim:", selected_quantities)
print("Kusursuz bilginin beklenen değeri (TL):", results["evpi"])

#############################################
# GÖREV 5: Duyarlılık Deneyi
#############################################
# Yalnızca talep olasılıklarını değiştiriyoruz.
# Kâr tablosu sabit kalır; beklenen değer ve onun seçimi değişebilir.
high_demand_scenario = Scenario(probabilities=(0.10, 0.20, 0.70))
high_demand_results = analyze(high_demand_scenario)
print("Yeni beklenen kârlar:", high_demand_results["scores"]["expected_value"])
print("Yeni beklenen değer seçimi:", high_demand_results["choices"]["expected_value"])
