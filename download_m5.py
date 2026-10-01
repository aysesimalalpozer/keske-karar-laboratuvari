"""M5'in Zenodo arşiv kopyasını indirir ve yayınlanan MD5 ile kontrol eder."""

from pathlib import Path
from urllib.request import urlopen
import hashlib
import json

DATA_DIRECTORY = Path(__file__).parent / "data" / "raw"
SOURCE = "https://zenodo.org/records/10203108"
FILES = {
    "calendar.csv": "3ffeab2991b0c8e861d008b39ea4c95c",
    "sales_train_validation.csv": "26a366a25beb57b0a8f4c7b148758f94",
    "sell_prices.csv": "08c591caa99e55daf3e0ccac913f7c85",
}

if __name__ == "__main__":
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for filename, expected_checksum in FILES.items():
        destination = DATA_DIRECTORY / filename
        if not destination.exists():
            temporary = destination.with_suffix(".part")
            url = f"{SOURCE}/files/{filename}?download=1"
            print("İndiriliyor:", filename, flush=True)
            with urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(destination)
        with destination.open("rb") as downloaded_file:
            checksum = hashlib.file_digest(downloaded_file, "md5").hexdigest()
        if checksum != expected_checksum:
            raise ValueError(f"{filename}: kaynak checksum değeriyle uyuşmuyor.")
        print("Doğrulandı:", filename, flush=True)
    (DATA_DIRECTORY.parent / "provenance.json").write_text(
        json.dumps(
            {
                "source": SOURCE,
                "original_source": "https://www.kaggle.com/competitions/m5-forecasting-accuracy",
                "files_md5": FILES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
