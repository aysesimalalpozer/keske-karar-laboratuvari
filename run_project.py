###############################################################
# KEŞKE — Tek Komutla Yeniden Üretim
###############################################################
# İş Problemi: Aynı veriyle analiz, karar deneyleri, denetim ve siteyi yeniden
# oluşturmak. Gerçek veri indirme adımı isteğe bağlı ve ayrı tutulur.
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).parent
ANALYSIS_STEPS = [
    "satis_analizi.py",
    "karar_deneyi.py",
    "saglamlik_deneyi.py",
    "tahminden_karara.py",
    "teknik_denetim.py",
]
PUBLISH_STEPS = [
    "publish_analysis.py",
    "publish_decisions.py",
    "publish_robustness.py",
    "publish_forecast_decisions.py",
    "publish_audit.py",
    "build.py",
]


def main():
    parser = argparse.ArgumentParser(description="KEŞKE deneylerini ve sitesini oluştur.")
    parser.add_argument("--download", action="store_true", help="Önce M5 dosyalarını indir.")
    parser.add_argument(
        "--build-only", action="store_true", help="Mevcut raporlarla siteyi oluştur."
    )
    arguments = parser.parse_args()
    steps = []
    if arguments.download:
        steps.append("download_m5.py")
    if not arguments.build_only:
        steps.extend(ANALYSIS_STEPS)
    steps.extend(PUBLISH_STEPS)
    for step in steps:
        print("Çalıştırılıyor:", step, flush=True)
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / step)], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
