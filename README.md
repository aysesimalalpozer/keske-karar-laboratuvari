# KEŞKE — Satıştan Karara

**Gerçek satış geçmişinde, farklı maliyet varsayımları altında tahmin ve karar yöntemlerini karşılaştıran interaktif araştırma prototipi.**

İyi tahmin, iyi sipariş kararı demek mi? KEŞKE, aynı satış geçmişinde maximax, maximin, minimax pişmanlık ve beklenen değerin farklı miktarlar seçmesini gösterir. Daha sonra satış tahminini, ayrı geçmiş dönemdeki tahmin hataları ve newsvendor maliyet hesabıyla sipariş kararına bağlar.

**Durum:** Eğitim ve portföy için çalışan, yeniden üretilebilir prototip. Gerçek işletme maliyetleri, stok mevcudiyeti veya yeni dış doğrulama içermiyor. Performans üstünlüğü ve üretime hazır stok sistemi iddiası yok.

## Deney kapsamı

- M5: anonim ürünlerin günlük Walmart satışları; 30.490 ürün–mağaza × 1.913 gün.
- Ayrıntılı ilk seri: `FOODS_3_090 / CA_1`. ACF, haftalık STL, ADF/KPSS ve regresyon girdilerinde VIF.
- Tekrarlı deney: 10 sabit ürün–mağaza × üç ardışık 28 günlük dönem = 30 ürün–dönem.
- Karar kuralları: 24 maliyet/senaryo ayarı, toplam 720 karşılaştırma.
- Tahmin bağlantısı: 30 ürün–dönem × 12 maliyet ayarı. Mevsimsel naïve, 28 günlük hareketli ortalama ve gecikmeli OLS adayları.
- Teknik denetim: 9 eğitim/kalibrasyon penceresi × 30 ürün–dönem × 12 maliyet ayarı = 3.240 karşılaştırma.

## İlk sonuç ve karşı örnekler

Fiyat 100, maliyet 50, kalan ürün değeri 12,5 **normalleştirilmiş para birimi** altında, tahmin + hata dağılımı + maliyet yaklaşımı doğrudan tahmin kadar siparişe göre 13 denemede daha yüksek, 10'unda eşit, 7'sinde daha düşük kâr verdi. TL, gerçek fiyat veya finansal kazanç iddiası değildir.

Yedi gecikmeli nominal Ljung–Box taramasında 5/30 hata havuzu p<0,05 verdi. Pencere seçimleri sonucu değiştirdi: aynı maliyetlerde daha yüksek kâr görülen deneme sayısı 9 pencere birleşiminde 10–18 arasında değişti. Hata havuzlarının bağımsız/aynı dağılımlı olduğu veya yöntemin her zaman üstün olduğu kabul edilmez. Ayrıntılar [teknik denetim raporunda](data/analysis/technical_audit.json).

## Çalıştırma

Python 3.12 ve Node.js 20+ kullanılır. Statik demo için Python bağımlılıklarını kurmak gerekmez:

```bash
python -m http.server 8765 --directory web --bind 127.0.0.1
```

Tarayıcı: `http://127.0.0.1:8765/`. Dağıtılabilir demo `web/index.html` içindedir; CSS/JS ve raporlar gömülüdür. Google Fonts için internet gerekebilir; çevrimdışı sistem yazı tipine düşer. Python analizleri tarayıcıda çalışmaz; site önceden hesaplanmış sonuçları gösterir.

Analizi yeniden üretmek:

```bash
python -m venv .venv
```

Windows: `.venv\Scripts\activate`. macOS/Linux: `source .venv/bin/activate`.

```bash
pip install -r requirements-analysis.txt
python -X utf8 run_project.py --download
```

Ham veriler zaten varsa `python -X utf8 run_project.py`; yalnız raporlardan siteyi yenilemek için `python -X utf8 run_project.py --build-only`.

## Doğrulama

```bash
python -m unittest discover -s . -p "test_*.py"
node web/test-model.mjs
```

Testler kâr muhasebesi, eşit optimumlar, kritik kantilin bütün miktarları karşılaştıran çözüme eşitliği, zaman sızıntısı, sıfır satış ve geçersiz girdileri kontrol eder. Testlerin geçmesi istatistiksel varsayımların veya gerçek işletme uygunluğunun kanıtı değildir.

## Dosyaları hangi sırada okumalı?

1. `karar_analizi_case.py`: iş problemi ve elle anlaşılabilir kâr tablosu.
2. `satis_analizi.py`: veri denetimi, tanılar ve üç tahmin adayı.
3. `karar_deneyi.py`: geçmiş satış frekanslarıyla kararlar.
4. `saglamlik_deneyi.py`: başka ürün ve dönemlerde tekrar.
5. `tahminden_karara.py`: eğitim → model seçimi → ayrı hata havuzu → test.
6. `teknik_denetim.py`: hata tanıları ve pencere duyarlılığı.

Kod yazımı, kullanıcı tarafından sağlanan Miuul örneklerindeki **iş problemi → veri hikâyesi → görevler → açıklanmış fonksiyonlar** akışını izler. Miuul veya Vahit Keskin'in onayı/ortaklığı iddiası yoktur. Python hesaplama, HTML yapı, CSS görünüm, JavaScript etkileşim katmanıdır.

## Teknik sınırlar

- Gözlenen satış sansürlenmemiş talep değildir; sıfır satış stok yokluğunu gösterebilir.
- Ürün listesi kimliklerle sabitlendi; rastgele/temsili örneklem değildir.
- Test dönemleri önceden incelendi; çalışma keşif amaçlı geriye dönük değerlendirmedir.
- Örtüşen eğitimler ve ortak takvim, denemeleri bağımlı yapar; 720 bağımsız kanıt yoktur.
- İlk serideki ADF/KPSS/VIF sonuçları bütün ürünlere genellenmez; panel regresyon kullanılmaz.
- OLS'nin nedensel katsayı yorumu, güvenilir p-değerleri veya hata bağımsızlığı iddiası yoktur.
- Model MAE ile seçilir; kâr için model seçimi yapılmaz. 28/56/364 gün başlangıç parametreleridir.
- Hata senaryoları eşit ağırlıklıdır; koşullu varyans ve bağımlılık tam modellenmez. Garantili tahmin aralığı değildir.
- Günlük bağımsız tek dönemli stok hesabı: devreden stok, sabit gider, teslim süresi ve ek yokluk cezası yoktur.

## Kaynaklar, öğrenme ve katkı

[SOURCES.md](SOURCES.md) yöntem–kaynak–varsayım eşleştirmesini; [PORTFOLIO.md](PORTFOLIO.md) proje anlatımını içerir. Ders 01–07 dosyaları adım adım öğrenme içindir.

Proje Ayşe Simal Alpözer'in portföy çalışmasıdır. Kod geliştirme, araştırma ve dokümantasyonda yapay zekâ desteği kullanılmıştır. Tek bir makalenin birebir replikasyonu veya özgün algoritma iddiası yoktur.

Ham M5 dosyaları GitHub'a eklenmez; `download_m5.py` kaynak arşivden indirip yayımlanan MD5 değerleriyle indirme bütünlüğünü doğrular. Bu, verinin işletme gerçekliğini doğrulamak değildir. Veri kullanım koşulları için orijinal yarışma ve arşiv incelenmelidir.
