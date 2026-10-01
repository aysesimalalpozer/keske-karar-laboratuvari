# KEŞKE — Gerçek satış verisinden karar desteğine

**Amaç:** Belirsiz satışlarda, farklı maliyet ve karar anlayışlarının sipariş miktarını nasıl değiştirdiğini incelemek.

M5 verisiyle zaman sıralı tahmin karşılaştırması, klasik karar kuralları ve newsvendor yaklaşımını birleştiren interaktif araştırma prototipi. 10 ürün–mağaza çiftinde üç dönem, maliyet duyarlılığı ve hata tanıları incelenir.

**Teknikler:** Python, pandas, NumPy, statsmodels, OLS, mevsimsel naïve, hareketli ortalama, ACF/STL, ADF/KPSS/VIF, ampirik senaryolar, newsvendor kritik kantili, geriye dönük değerlendirme; HTML/CSS/JavaScript.

**Öğrenme:** Tahmin hatasını azaltmak ve ekonomik karar kalitesini artırmak farklı hedeflerdir. Maliyete duyarlı sipariş yaklaşımı başlangıç ayarında 30 denemenin 13'ünde daha yüksek, 10'unda eşit, 7'sinde daha düşük kâr verdi. Hata tanıları ve pencere duyarlılığı sınırları görünür kılar.

**Katkı:** Proje Ayşe Simal Alpözer'in portföy çalışmasıdır; kod geliştirme ve dokümantasyonda yapay zekâ desteği kullanıldı. Kişisel öğrenme için yedi ders ve elle hesaplanabilir örnek içerir. Miuul/Vahit Keskin onayı veya tamamıyla bağımsız yazılmış kod iddiası yoktur.

**Sunum cümlesi:** “Gerçek satış geçmişinde klasik karar kurallarını karşılaştırdım; ayrı geçmiş dönemdeki tahmin hatalarıyla senaryolar oluşturup newsvendor maliyet hesabını sipariş kararına bağladım. Sonuçları farklı ürün, dönem ve pencere seçimleriyle sınadım; üstünlük iddiası yerine varsayımları ve başarısız örnekleri de raporladım.”

**Sınır:** Keşif amaçlı prototip; gerçek maliyet, eksiksiz talep, stok mevcudiyeti veya üretim ortamında yeni doğrulama yok.
