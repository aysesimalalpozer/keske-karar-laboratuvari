"""Okunabilir kaynakları tek HTML çıktısında birleştirir. Harici paket gerekmez."""

from pathlib import Path

web_directory = Path(__file__).parent / "web"
html = (web_directory / "template.html").read_text(encoding="utf-8")
html = html.replace(
    "<!-- JOURNEY_SCENE -->", (web_directory / "journey.svg").read_text(encoding="utf-8")
)
css = (web_directory / "styles.css").read_text(encoding="utf-8-sig")
model = (web_directory / "decision-model.js").read_text(encoding="utf-8-sig")
app = (web_directory / "app.js").read_text(encoding="utf-8-sig")
experiment = (web_directory / "decision-experiment.js").read_text(encoding="utf-8")
robustness = (web_directory / "robustness.js").read_text(encoding="utf-8")
linked = (web_directory / "forecast-decisions.js").read_text(encoding="utf-8")

# Model dışa aktarımlarını kaldır; tek module script içinde erişilebilir kalır.
model = model.replace("export const ", "const ").replace("export function ", "function ")
app = app.replace("import { scenario, analyze, calculateOutcome } from './decision-model.js';", "")
html = html.replace('<link rel="stylesheet" href="styles.css">', "<style>\n" + css + "\n</style>")
html = html.replace('<script type="module" src="app.js"></script>', "")
html = html.replace(
    "</body>",
    '<script type="module">\n'
    + model
    + "\n"
    + app
    + "\n"
    + experiment
    + "\n"
    + robustness
    + "\n"
    + linked
    + "\n</script>\n</body>",
)
(web_directory / "index.html").write_text(html, encoding="utf-8")
print("Tek dosyalık index.html oluşturuldu.")
