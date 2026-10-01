// Python'da hesaplanan deneyi gösterir; tarayıcı yeni istatistik üretmez.
const experimentData = JSON.parse(document.getElementById('decision-experiment-data').textContent);
const ruleNames = {maximax: 'Maximax', maximin: 'Maximin', minimax_regret: 'Minimax pişmanlık', expected_value: 'Beklenen değer'};
const ruleColors = ['#8a5d44', '#727d78', '#b1914b', '#2b3a30'];
const numberFormat = new Intl.NumberFormat('tr-TR', {maximumFractionDigits: 1});
const controls = ['cost-ratio', 'salvage-ratio', 'scenario-support'].map(id => document.getElementById(id));

function renderDecisionExperiment() {
  const [cost, salvage, support] = controls.map(control => control.value);
  const config = experimentData.configurations.find(config => config.cost_ratio === Number(cost) && config.salvage_ratio === Number(salvage) && config.support === support);
  document.getElementById('decision-assumptions').textContent = `Satış fiyatı 100 · Maliyet ${numberFormat.format(config.cost)} · Kalan ürün değeri ${numberFormat.format(config.salvage)}. Para birimi normalleştirilmiştir; TL değildir.`;
  document.getElementById('decision-results').innerHTML = Object.entries(config.summary).map(([rule, result]) => `<tr><th scope="row">${ruleNames[rule]}</th><td>${numberFormat.format(result.mean_quantity)}</td><td>${numberFormat.format(result.profit)}</td><td>${result.remaining}</td><td>${result.uncovered_reference}</td><td>${numberFormat.format(result.regret)}</td></tr>`).join('');
  const paths = Object.entries(config.daily).map(([rule, rows]) => {
    let cumulative = 0;
    return {rule, values: [0, ...rows.map(row => cumulative += row.profit)]};
  });
  const allValues = paths.flatMap(path => path.values);
  const min = Math.min(0, ...allValues), max = Math.max(1, ...allValues);
  const y = value => 210 - (value - min) / (max - min) * 170;
  const x = index => 75 + index / experimentData.test_days * 600;
  const lines = paths.map((path, index) => `<polyline points="${path.values.map((value, day) => `${x(day)},${y(value)}`).join(' ')}" fill="none" stroke="${ruleColors[index]}" stroke-width="2.5"/>`).join('');
  document.getElementById('decision-chart').innerHTML = `<svg viewBox="0 0 720 255" role="img" aria-labelledby="decision-chart-title"><title id="decision-chart-title">28 test gününde biriken varsayımsal kâr. Sayısal sonuçlar yukarıdaki tabloda.</title><line x1="75" x2="675" y1="${y(0)}" y2="${y(0)}" stroke="#aab3a3"/><text x="5" y="40" font-size="12">${numberFormat.format(max)}</text><text x="5" y="210" font-size="12">${numberFormat.format(min)}</text>${lines}<text x="75" y="242" font-size="12">Başlangıç</text><text x="625" y="242" font-size="12">28. gün</text></svg>`;
  document.getElementById('decision-legend').innerHTML = paths.map((path, index) => `<span style="color:${ruleColors[index]}">● ${ruleNames[path.rule]}</span>`).join(' ');
  const dayNames = ['Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi','Pazar'];
  document.getElementById('weekday-decisions').innerHTML = Object.entries(config.weekday_policies).map(([day, policy]) => `<tr><th scope="row">${dayNames[day]}</th><td>${policy.sample_size}</td><td>${policy.min_scenario}–${policy.max_scenario}</td>${Object.keys(ruleNames).map(rule => `<td>${Math.min(...policy.choices[rule])}</td>`).join('')}</tr>`).join('');
  const zeroPolicy = Object.values(config.weekday_policies).every(policy => Math.min(...policy.choices.maximin) === 0);
  document.getElementById('decision-observation').textContent = zeroPolicy ? 'Bu senaryo kümesinde her gün için sıfır satış olasılığı bulunuyor. Maximin, elde kalan ürün zararından kaçınmak için 0 sipariş seçiyor. Bu, modelin uç durumlara verdiği cevaptır; işletme önerisi değildir.' : 'Senaryo uçlarını değiştirince özellikle en kötü duruma odaklanan kuralların miktarları değişebilir. Sonuçlar aynı 28 test gününde karşılaştırılıyor.';
}
controls.forEach(control => control.addEventListener('change', renderDecisionExperiment));
renderDecisionExperiment();
