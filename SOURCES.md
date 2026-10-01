# Teknik dayanak ve deney seçimleri

İlk kod klasik yöntemlerle oluşturuldu; aşağıdaki kaynaklarla karşılaştırıldı. Proje tek makalenin birebir replikasyonu değildir. Bir kaynağın yöntem tanımını desteklemesi, burada seçilen pencere ve değişkenlerin en iyi olduğunu kanıtlamaz.

| Parça | Teknik dayanak | Projedeki seçim ve sınır |
|---|---|---|
| Veri | [M5 orijinal yarışma](https://www.kaggle.com/competitions/m5-forecasting-accuracy), [Zenodo arşiv kopyası](https://zenodo.org/records/10203108) | Gerçek satış; tam talep veya maliyet değil. Ham veriler depoda yok. |
| Mevsimsel naïve | [FPP3, basit yöntemler](https://otexts.com/fpp3/simple-methods.html) | Günlük seri için haftalık m=7; kıyas noktası. |
| Hareketli ortalama | Önceki 28 satışın aritmetik ortalaması | 28 gün bize ait başlangıç seçimi; kitabın ortalama yönteminin birebir aynı uygulaması diye sunulmaz. |
| Gecikmeli OLS | [FPP3 zaman serisi regresyonu](https://otexts.com/fpp3/regression.html), [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) | Lag1, lag7, geçmiş7 ortalama, 6 gün göstergesi. Nedensellik veya katsayı anlamlılığı iddiası yok. |
| Zaman ayrımı | [FPP3 zaman sıralı değerlendirme](https://otexts.com/fpp3/tscv.html) | 364 eğitim, 28 seçim, 56 hata, 28 test; süreler deney seçimi. Test önceden görülmüş. |
| STL ve mevsimsel güç | [FPP3 STL özellikleri](https://otexts.com/fpp3/stlfeatures.html) | period=7, robust=True; yıllık örüntü testi değil. |
| ADF / KPSS | [ADF](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html), [KPSS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html) | c/ct, ADF AIC gecikme, KPSS auto; sadece ilk seride. |
| VIF | [statsmodels VIF](https://www.statsmodels.org/stable/generated/statsmodels.stats.outliers_influence.variance_inflation_factor.html) | İlk serinin regresyon girdileri; otomatik silme kuralı değil. |
| Maximax/maximin/pişmanlık/EMV | [FGCU karar analizi ders notu](https://ruby.fgcu.edu/Courses/ekirche/MSci/modules/6603/m1_notes.htm) | Aynı alternatifler, kâr tablosu ve bilgi sınırı. Eşit optimumda küçük miktar. |
| Newsvendor ve kritik oran | [MIT 2.854 Inventory](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/6c8fec8f99bcf7059b73b82e96d43901_MIT2_854F16_Inventory.pdf), [MIT 15.772J Newsvendor](https://ocw.mit.edu/courses/15-772j-d-lab-supply-chains-fall-2014/resources/mit15_772jf14_newsboy/) | (p-c)/(p-s) kantili; tek dönem, p>c>s, sansürlenmiş satış referansı. Simpleks kullanılmadı. |
| Ampirik hata senaryosu | [FPP3 dağılımsal tahmin](https://otexts.com/fpp3/prediction-intervals.html) | Tahmine ayrı kalibrasyon hataları eklenir; negatifleri sıfıra kırpma ve yuvarlama bize ait seçim. Tam bootstrap veya garantili aralık değil. |
| Ljung–Box | [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html) | Test öncesi hatalar, 7/14 gecikme, model_df=0. Nominal tarama; çoklu test düzeltmesi yok. |
| Levene/Brown–Forsythe | [SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.levene.html) | Hata havuzunun iki yarısı, center=median. Bağımlılık p-değerlerini etkileyebilir. |

## Kaynak okumayı sayısal örneğe bağlama

Önce MIT kâr hesabını ve kritik oranı çalış. p=100, c=50, s=12,5 için oran 4/7'dir. 56 eşit ağırlıklı tam sayı senaryoda 32'nci sıralı senaryo seçilir; aynı sonucu bütün sipariş alternatiflerinin beklenen kârlarını hesaplayarak kontrol et. Sonra FPP3 basit tahmin ve hata inceleme bölümlerine geç. Formülün varsayımlarını söylemeden sadece isimlerini sıralama.
