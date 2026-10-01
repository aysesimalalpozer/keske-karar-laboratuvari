from pathlib import Path
import json

ROOT = Path(__file__).parent
report = json.loads((ROOT / "data/analysis/forecast_decisions.json").read_text(encoding="utf-8"))
options = "".join(
    f'<option value="{index}" {"selected" if index == 29 else ""}>{case["item"]} / {case["store"]} · Dönem {case["period"]}</option>'
    for index, case in enumerate(report["cases"])
)
payload = json.dumps(report, ensure_ascii=False).replace("<", "\\u003c")
section = f"""<section class="method-section" id="forecast-decision" aria-labelledby="linked-title">
<p class="eyebrow">05 / TAHMİNDEN KARARA</p><h2 id="linked-title">Tahmin aynı. Sipariş neden farklı?</h2>
<p>50 ürün satılacağını tahmin etmek, mutlaka 50 ürün sipariş etmek demek mi?
Fazla ürünün maliyeti ve eksik ürünün kaçırdığı gelir farklıysa karar da farklı olabilir.</p>
<div class="decision-controls">
<label for="linked-case">Ürün ve dönem<select id="linked-case">{options}</select></label>
<label for="linked-cost">Birim maliyet / satış fiyatı<select id="linked-cost"><option value="0.3">%30</option><option value="0.5" selected>%50</option><option value="0.7">%70</option><option value="0.9">%90</option></select></label>
<label for="linked-salvage">Kalan değer / maliyet<select id="linked-salvage"><option value="0">%0</option><option value="0.25" selected>%25</option><option value="0.5">%50</option></select></label>
</div><p id="linked-protocol"></p><p id="linked-observation" class="takeaway" role="status" aria-live="polite"></p>
<div class="table-scroll"><table><caption>Aynı 28 test gününde altı yaklaşım · Para birimi normalleştirilmiştir, TL değildir</caption>
<thead><tr><th>Yöntem</th><th>Ort. sipariş</th><th>Kâr</th><th>Kalan adet</th><th>Karşılanmayan referans</th><th>Pişmanlık</th></tr></thead><tbody id="linked-results"></tbody></table></div>
<details><summary>Gün gün tahmin ve siparişleri gör</summary><div class="table-scroll"><table>
<caption>Bir gün ileri tahmin; siparişler gelecekteki satışı görmez</caption><thead><tr><th>Tarih</th><th>Tahmin</th><th>Tahmin kadar sipariş</th><th>Maliyete göre sipariş</th><th>Satış referansı</th><th>Maliyete göre kâr</th></tr></thead><tbody id="linked-daily"></tbody></table></div></details>
<details><summary>Tahmin nasıl siparişe dönüştü?</summary><p>Önce 364 günle regresyon eğitildi.
Sonraki 28 günde üç tahmin adayının MAE'si karşılaştırılıp model seçildi.
Ayrı sonraki 56 günde, seçilen modelin bir gün ileri tahmin hataları saklandı.
Sonraki 28 gün testtir. Test satışları model seçimine veya hata dağılımına katılmaz.</p>
<p>Her test gününde: satış senaryosu = o günün tahmini + geçmişteki bir hata.
Negatif senaryolar sıfıra kırpılır ve tam sayıya yuvarlanır. 56 hata eşit olasılıklıdır.
Sipariş, bu senaryolarda beklenen kârı en büyük yapan miktardır.
Newsvendor kritik oranı (fiyat − maliyet) / (fiyat − kalan değer) kullanılır.
Alternatif üst sınırı testten önceki 364 günlük en yüksek satıştır; bütün yöntemler aynı sınırı kullanır.</p>
<p>Doğrudan tahmin yaklaşımı yalnız tahmini yuvarlayıp sipariş verir; maliyetle miktarı değiştirmez.
Diğer dört kural önceki bölümün aynı ürün, tarih ve tam senaryo desteğindeki sonuçlarıdır.
Sonraki gün tahmininde artık gerçekleşmiş önceki satışlar kullanılabilir; 28 gün tek seferde tahmin edilmez.</p></details>
<div class="source-note"><strong>Bu yaklaşımın sınırı</strong><p>Geçmiş hataları aynı havuzda kullanıyoruz;
hatanın günlere göre değişen büyüklüğü ve seri bağımlılığı bütünüyle modellenmiyor. Bu senaryolar garantili tahmin aralığı değildir.
Tahmin modeli MAE ile seçildi; kârı optimize eden model seçimi yapılmadı. Önceden incelenen test dönemlerinde keşif amaçlı değerlendirmedir.
Satış gerçek talebin tamamını göstermeyebilir; maliyetler varsayım, kalan stok ertesi güne taşınmaz.</p>
<p>Dayanak: <a href="https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/6c8fec8f99bcf7059b73b82e96d43901_MIT2_854F16_Inventory.pdf">MIT · Newsvendor kritik oranı</a>.</p></div>
<script type="application/json" id="linked-data">{payload}</script></section>"""
path = ROOT / "web/template.html"
html = path.read_text(encoding="utf-8")
start, end = "<!-- LINKED_START -->", "<!-- LINKED_END -->"
if start in html:
    before, rest = html.split(start, 1)
    _, after = rest.split(end, 1)
    html = before + start + section + end + after
else:
    html = html.replace("  </main>", start + section + end + "\n  </main>")
# Eski bölümlerin tarihsel açıklamasını güncel bağlantıyla tamamla.
html = html.replace(
    "tahmin regresyonu bu katmana henüz bağlanmadı.",
    'Bu başlangıç katmanından ayrı olarak <a href="#forecast-decision">tahminle bağlantılı kararları karşılaştır</a>.',
)
html = html.replace(
    "Bu, tahmin regresyonundan ayrı bir başlangıç karar deneyidir.",
    'Bu, geçmiş satış dağılımıyla başlangıç deneyidir. <a href="#forecast-decision">Tahminle bağlantılı kararları da incele</a>.',
)
path.write_text(html, encoding="utf-8")
