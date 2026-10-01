###############################################################
# KEŞKE — Teknik Denetimi Görünür Kılmak
###############################################################
from pathlib import Path
import json

ROOT = Path(__file__).parent


def main():
    audit = json.loads((ROOT / "data/analysis/technical_audit.json").read_text(encoding="utf-8"))
    diagnostics = audit["diagnostics"]
    flagged = sum(
        row["ljung_box_p_7"] is not None and row["ljung_box_p_7"] < 0.05 for row in diagnostics
    )
    shifted = sum(
        row["variance_shift_p"] is not None and row["variance_shift_p"] < 0.05
        for row in diagnostics
    )
    sensitivity = [
        row
        for row in audit["sensitivity"]
        if row["cost_ratio"] == 0.5 and row["salvage_ratio"] == 0.25
    ]
    rows = "".join(
        f'<tr><th scope="row">{row["training_days"]}</th><td>{row["calibration_days"]}</td><td>{row["higher"]}</td><td>{row["equal"]}</td><td>{row["lower"]}</td></tr>'
        for row in sensitivity
    )

    def pvalue(value):
        return "Tanımsız" if value is None else f"{value:.4f}"

    diagnostic_rows = "".join(
        f'<tr><th scope="row">{row["item"]} / {row["store"]} · {row["period"]}</th><td>{row["mean_error"]:.2f}</td><td>{pvalue(row["ljung_box_p_7"])}</td><td>{pvalue(row["ljung_box_p_14"])}</td><td>{pvalue(row["variance_shift_p"])}</td></tr>'
        for row in diagnostics
    )
    section = f"""<section class="method-section" id="technical-audit" aria-labelledby="audit-title">
<p class="eyebrow">06 / VARSAYIMLARI SINAMAK</p><h2 id="audit-title">Sonuç ne kadar sağlam?</h2>
<p>Model çalışıyor diye varsayımlar otomatik doğru olmaz. Test öncesindeki 30 hata havuzunu ve
9 eğitim/kalibrasyon penceresini inceledik. Toplam 3.240 maliyet–pencere karşılaştırması.</p>
<p class="takeaway">Yedi gecikmeli Ljung–Box taramasında {flagged}/30 hata havuzu için nominal p &lt; 0,05;
iki yarının varyans karşılaştırmasında {shifted}/30. Hataların her yerde bağımsız ve aynı dağılımdan geldiğini kabul edemeyiz.
Bu yöntem ampirik bir yaklaşım; garantili tahmin dağılımı veya üretim sistemi değildir.</p>
<div class="table-scroll"><table><caption>Maliyet/fiyat %50, kalan değer/maliyet %25 · Dağılımlı siparişin doğrudan tahmin kadar siparişe göre kârı</caption>
<thead><tr><th>Eğitim günü</th><th>Hata kalibrasyonu günü</th><th>Daha yüksek</th><th>Eşit</th><th>Daha düşük</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Pencereyi değiştirince sonuç da değişiyor. En iyi satırı seçip aynı testte başarı iddiası yapmıyoruz;
364/56 başlangıç ayarı korunuyor. Bu karşılaştırma keşif amaçlı duyarlılık analizidir.</p>
<details><summary>Hata tanılarının bütün sonuçlarını aç</summary><div class="table-scroll"><table>
<caption>Yalnız test öncesi kalibrasyon hataları · p-değerleri nominal tarama değerleridir</caption>
<thead><tr><th>Ürün / mağaza / dönem</th><th>Ort. hata</th><th>Ljung–Box 7 p</th><th>Ljung–Box 14 p</th><th>Varyans p</th></tr></thead><tbody>{diagnostic_rows}</tbody></table></div></details>
<div class="source-note"><strong>Bu testler neyi kanıtlamaz?</strong><p>Çoklu test düzeltmesi yapılmadı;
30 dönem bağımsız değil. Ljung–Box'ta model_df=0 kullanıldı: model ayrı eğitim bloğunda sabitlenmişti.
Varyans karşılaştırması iki kalibrasyon yarısına medyan merkezli Levene/Brown–Forsythe testidir;
seri bağımlılığı nominal p-değerini etkileyebilir. Büyük p-değeri varsayımın doğru olduğunu kanıtlamaz.
Bu tanılar modele onay vermek için değil, sınırlamalarını göstermek için raporlanır.</p>
<p>Kaynaklar: <a href="https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html">Ljung–Box</a> ·
<a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.levene.html">Levene/Brown–Forsythe</a> ·
<a href="https://otexts.com/fpp3/prediction-intervals.html">Tahmin belirsizliği</a>.</p></div></section>"""
    path = ROOT / "web/template.html"
    html = path.read_text(encoding="utf-8")
    start, end = "<!-- AUDIT_START -->", "<!-- AUDIT_END -->"
    if start in html:
        before, rest = html.split(start, 1)
        _, after = rest.split(end, 1)
        html = before + start + section + end + after
    else:
        html = html.replace("  </main>", start + section + end + "\n  </main>")
    # Başlık bütün gerçek veri/karar katmanlarını kapsar.
    html = html.replace("KEŞKE — Üç karar, aynı gelecek", "KEŞKE — Satıştan karara")
    path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
