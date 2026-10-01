"""Deney verisi ve açıklamalı kontrolleri site şablonuna yerleştirir."""

from pathlib import Path
import json

ROOT = Path(__file__).parent
data = json.loads((ROOT / "data/analysis/decision_experiment.json").read_text(encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
section = f"""<section class="method-section" id="decision-lab" aria-labelledby="decision-title">
<p class="eyebrow">03 / KARARIN MALİYETİ</p><h2 id="decision-title">Aynı geçmiş. Farklı cesaret.</h2>
<p>Maliyet değişince hangi karar ayakta kalıyor? Dört kural aynı satış geçmişini görür,
aynı 28 test gününde sınanır. Aşağıdaki varsayımları değiştir.</p>
<div class="decision-controls">
<label>Birim maliyet / satış fiyatı<select id="cost-ratio"><option value="0.3">%30</option><option value="0.5" selected>%50</option><option value="0.7">%70</option><option value="0.9">%90</option></select></label>
<label>Kalan değer / birim maliyet<select id="salvage-ratio"><option value="0">%0</option><option value="0.25" selected>%25</option><option value="0.5">%50</option></select></label>
<label>Senaryo sınırları<select id="scenario-support"><option value="full">Gözlenen bütün satışlar</option><option value="central">%5–%95 sınırlarına kırpılmış</option></select></label>
</div><p id="decision-assumptions" role="status" aria-live="polite"></p>
<div class="table-scroll"><table><caption>28 gün toplamı · Kâr ve pişmanlık normalleştirilmiş para biriminde</caption>
<thead><tr><th>Kural</th><th>Ort. sipariş</th><th>Kâr</th><th>Kalan adet</th><th>Karşılanmayan satış referansı</th><th>Gerçekleşen pişmanlık</th></tr></thead><tbody id="decision-results"></tbody></table></div>
<div id="decision-chart"></div><div id="decision-legend" class="decision-legend"></div>
<p id="decision-observation" class="takeaway" aria-live="polite"></p>
<details><summary>Her gün hangi miktar seçildi?</summary><div class="table-scroll"><table>
<caption>Eğitim geçmişinden sabitlenen haftanın günü politikaları</caption><thead><tr><th>Gün</th><th>Örnek sayısı</th><th>Senaryo aralığı</th><th>Maximax</th><th>Maximin</th><th>Minimax pişmanlık</th><th>Beklenen değer</th></tr></thead><tbody id="weekday-decisions"></tbody></table></div></details>
<details><summary>Deney nasıl kuruldu?</summary><p>Eğitim döneminin son {data['history_days']} günü
({data['history_start']} – {data['history_end']}) kullanıldı. Pazartesi için geçmiş pazartesiler gibi,
her haftanın gününe ayrı ampirik satış dağılımı kuruldu. Olasılıklar gözlem frekanslarıdır.
Alternatifler 0–{data['quantity_max']} tam sayı sipariş; sınır eğitim satışlarından belirlendi.
Politikalar testte güncellenmedi. Eşit optimumlarda en düşük sipariş uygulandı.</p>
<p>%5–%95 seçeneğinde eğitim satışları her gün grubunun yüzdelik sınırlarına kırpılır;
uç gözlemler silinmez, olasılıkları sınırlarda toplanır. Bu bir duyarlılık deneyi, geleceğin güven aralığı değildir.</p>
<p>Kâr = min(sipariş, satış referansı) × fiyat + kalan × kalan değer − sipariş × maliyet.
Gerçekleşen pişmanlık, aynı alternatif kümesinde satış önceden bilinse elde edilebilecek en iyi kâr ile aradaki farktır.
Minimax karar verirken bu gelecekteki satışları görmez.</p></details>
<div class="source-note"><strong>Sonuçları nasıl okumalı?</strong><p>Bu, geçmiş satış dağılımıyla başlangıç deneyidir. <a href="#forecast-decision">Tahminle bağlantılı kararları da incele</a>.
Gerçek satışları talep referansı kabul ediyoruz; stok yokluğunda kaybedilmiş gerçek talep bilinmiyor.
Gün sonunda kalan ürünün değeri tahsil edilir; ertesi güne stok taşınmaz. Her gün bağımsız tek dönemdir.
Sabit gider, teslim süresi ve ek stok yokluğu cezası yoktur. Fiyat değiştirerek müşteri tepkisi modellemiyoruz.
Testte en yüksek kârı görmek, gelecekte en iyi yöntemi bulduğumuz anlamına gelmez.</p>
<p>Teknik dayanak: <a href="https://ocw.mit.edu/courses/15-772j-d-lab-supply-chains-fall-2014/resources/mit15_772jf14_newsboy/">MIT · Newsvendor Inventory Problem</a>.</p></div>
<script type="application/json" id="decision-experiment-data">{payload}</script>
</section>"""
template = ROOT / "web/template.html"
html = template.read_text(encoding="utf-8")
start, end = "<!-- DECISIONS_START -->", "<!-- DECISIONS_END -->"
if start in html:
    before, rest = html.split(start, 1)
    _, after = rest.split(end, 1)
    html = before + start + section + end + after
else:
    html = html.replace("  </main>", start + section + end + "\n  </main>")
template.write_text(html, encoding="utf-8")
