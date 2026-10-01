"""Hesaplanan sonuçları tek dosyalı siteye aktarır; sonuç uydurmaz."""

from pathlib import Path
import base64
import json

ROOT = Path(__file__).parent
report = json.loads((ROOT / "data/analysis/report.json").read_text(encoding="utf-8"))
image = base64.b64encode((ROOT / "data/analysis/sales_diagnostics.png").read_bytes()).decode()
names = {
    "seasonal_naive": "Geçen haftanın aynı günü",
    "past_28_mean": "Son 28 gün ortalaması",
    "lag_regression": "Geçmiş satış + takvim regresyonu",
}
rows = "".join(
    f'<tr><th scope="row">{names[name]}</th><td>{score["validation_mae"]:.2f}</td>'
    f'<td>{score["test_mae"]:.2f}</td></tr>'
    for name, score in report["comparison"]["mae"].items()
)
section = f"""<section class="method-section" id="real-data" aria-labelledby="data-title">
<p class="eyebrow">02 / GERÇEK SATIŞ GEÇMİŞİ</p><h2 id="data-title">Geçmiş ne söylüyor?</h2>
<p>M5 · FOODS_3_090 / CA_1. Tek ürünün tek mağazadaki 1.913 günlük satış geçmişi.
İlk 1.857 gün eğitim, sonraki 28 gün doğrulama, son 28 gün test.</p>
<img src="data:image/png;base64,{image}" alt="Eğitim satışları, gecikmelere göre otokorelasyon ve haftalık STL bileşeni" style="width:100%;height:auto">
<details><summary>Testler aynı şeyi mi söylüyor?</summary><p>Sabitli ADF p=0,0014: birim kök hipotezi reddediliyor.
Sabitli KPSS p=0,0251: durağanlık hipotezi de reddediliyor. Bu sonuçlarla seriye kesin olarak durağan diyemeyiz;
trend, yapısal değişim ve dönemlere göre davranışı ayrıca incelemeliyiz.</p>
<p>1 gün gecikmede ACF 0,731; 7 günde 0,624. Haftalık STL gücü 0,295.
Bu ölçüler nedensellik göstermez. Regresyonda önceki 7 gün ortalamasının VIF değeri 5,72;
gecikmeli değişkenlerle örtüşmesini sonraki karşılaştırmada inceleyeceğiz.</p></details>
<div class="table-scroll"><table><caption>Bir gün ileri tahmin · MAE (ürün adedi; düşük daha iyi)</caption>
<thead><tr><th>Yöntem</th><th>Doğrulama</th><th>Test</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Regresyon doğrulama sonucuyla seçildi. Her gün, o zamana kadar gerçekleşmiş satışlar kullanıldı;
28 gün bir kerede tahmin edilmedi. Bu sonuç tek ürün ve tek test dönemiyle sınırlı.</p>
<div class="source-note"><strong>Satıştan karara</strong><p>Satışlar gerçek veridir.
Maliyet ve kalan ürün değeri varsayımlarını <a href="#decision-lab">karar deneyinde değiştirerek karşılaştır</a>.
Gözlenen satış, karşılanmamış talebi içermez.</p>
<p>Kaynaklar: <a href="https://zenodo.org/records/10203108">M5 veri arşivi</a> ·
<a href="https://otexts.com/fpp3/stlfeatures.html">STL yöntemi</a> ·
<a href="https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html">ADF</a>.</p></div>
</section>"""
template = ROOT / "web/template.html"
html = template.read_text(encoding="utf-8")
start, end = "<!-- REAL_DATA_START -->", "<!-- REAL_DATA_END -->"
if start in html:
    before, rest = html.split(start, 1)
    _, after = rest.split(end, 1)
    html = before + start + section + end + after
else:
    html = html.replace("  </main>", start + section + end + "\n  </main>")
template.write_text(html, encoding="utf-8")
