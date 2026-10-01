"""Çok ürün ve çok dönem sonuçlarını okunabilir site bölümüne aktarır."""

from pathlib import Path
import json

ROOT = Path(__file__).parent
report = json.loads((ROOT / "data/analysis/robustness_report.json").read_text(encoding="utf-8"))
payload = json.dumps(report, ensure_ascii=False).replace("<", "\\u003c")
section = f"""<section class="method-section" id="robustness" aria-labelledby="robustness-title">
<p class="eyebrow">04 / TEK ÖRNEKTEN ÖTESİ</p><h2 id="robustness-title">Başka bir rafta da çalışıyor mu?</h2>
<p>{report['pair_count']} ürün–mağaza çifti. Art arda {report['period_count']} ayrı 28 günlük dönem.
Toplam {report['case_count']} eşleştirilmiş deneme ve {report['comparison_count']} maliyet/senaryo karşılaştırması.
Her test dönemi başlamadan önce, yalnız o tarihten önceki 364 günle kararlar kuruldu.</p>
<div class="decision-controls">
<label for="robust-cost">Birim maliyet / satış fiyatı<select id="robust-cost"><option value="0.3">%30</option><option value="0.5" selected>%50</option><option value="0.7">%70</option><option value="0.9">%90</option></select></label>
<label for="robust-salvage">Kalan değer / birim maliyet<select id="robust-salvage"><option value="0">%0</option><option value="0.25" selected>%25</option><option value="0.5">%50</option></select></label>
<label for="robust-support">Senaryo sınırları<select id="robust-support"><option value="full">Gözlenen bütün satışlar</option><option value="central">%5–%95 sınırlarına kırpılmış</option></select></label>
</div><p id="robustness-observation" class="takeaway" aria-live="polite"></p>
<div class="table-scroll"><table><caption>30 denemede özet · Her ürün–dönem eşit ağırlıklı</caption>
<thead><tr><th>Kural</th><th>Tek başına birincilik</th><th>Eşit birincilik</th><th>Zarar edilen deneme</th><th>Ort. kâr / referans gelir</th><th>Ort. pişmanlık / referans gelir</th></tr></thead><tbody id="robustness-summary"></tbody></table></div>
<p>Referans gelir = 100 × gözlenen satış adedi. Oranlar önce her denemede hesaplanıp sonra ortalanır;
yüksek satış hacmine sahip tek ürün özeti belirlemez. Negatif kâr oranı mümkündür.
Sıfır toplam satış varsa oran tanımsızdır ve ortalamaya katılmaz. Eşit birincilikler tabloda ayrı gösterilir.
Az satışlı bir üründe fazla sipariş zararı, referans gelirden büyük olabilir; bu nedenle oran −%100'ün altına inebilir.</p>
<details><summary>30 denemenin tüm sonuçlarını aç</summary><div class="table-scroll"><table>
<caption>28 günlük kâr toplamları · Normalleştirilmiş para birimi, TL değil</caption>
<thead><tr><th>Ürün / mağaza</th><th>Test dönemi</th><th>Satış adedi</th><th>Maximax</th><th>Maximin</th><th>Minimax pişmanlık</th><th>Beklenen değer</th><th>Bu dönemin birincisi</th></tr></thead><tbody id="robustness-cases"></tbody></table></div></details>
<details><summary>Ürünleri nasıl seçtik?</summary><p>FOODS_1_001, HOBBIES_1_001 ve HOUSEHOLD_1_001;
her biri CA_1, TX_1 ve WI_1 mağazalarında. Buna ilk deneydeki FOODS_3_090 / CA_1 eklendi.
Seçim kimliklerle sabitlendi; yüksek satış veya iyi sonuç veren ürün filtresi kullanılmadı.
Kimlikler anonimdir: ürünün gerçek adını bilmiyoruz. Bu liste bütün M5 ürünlerini temsil eden rastgele örneklem değildir.</p>
<p>Son 84 gün üç test bloğuna ayrıldı. Her blok başında dağılımlar yeniden geçmişten kuruldu;
o blok boyunca değişmedi. Sonraki blokta önceki blok satışları artık geçmiş olduğu için kullanılabilir.
Doğrulamada parametre aramadık; aynı önceden belirlenen 24 ayarı raporladık.</p></details>
<div class="source-note"><strong>Bu genişletme neyi gösterir?</strong><p>Sonucun seçilen ürün ve döneme duyarlılığını gösterir.
İlk ürünün son test sonucu zaten görülmüştü; bu genişletme keşif amaçlı geriye dönük karşılaştırmadır.
Eğitim pencereleri örtüşür ve ürünler aynı takvim günlerini paylaşır; 720 karşılaştırma bağımsız 720 kanıt değildir.
Güven aralığı veya istatistiksel üstünlük iddiası yoktur. Kararlar hâlâ geçmiş satış dağılımına dayanır;
<a href="#forecast-decision">Tahminle bağlantılı kararları ayrı katmanda karşılaştır</a>. Varsayımsal maliyetler ve satış–talep ayrımı geçerlidir.</p></div>
<script type="application/json" id="robustness-data">{payload}</script></section>"""
template = ROOT / "web/template.html"
html = template.read_text(encoding="utf-8")
start, end = "<!-- ROBUSTNESS_START -->", "<!-- ROBUSTNESS_END -->"
if start in html:
    before, rest = html.split(start, 1)
    _, after = rest.split(end, 1)
    html = before + start + section + end + after
else:
    html = html.replace("  </main>", start + section + end + "\n  </main>")
template.write_text(html, encoding="utf-8")
