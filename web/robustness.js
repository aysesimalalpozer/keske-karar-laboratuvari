// Önceden hesaplanan eşleştirilmiş karşılaştırmaları gösterir.
const robustnessReport = JSON.parse(document.getElementById('robustness-data').textContent);
const robustnessControls = ['robust-cost', 'robust-salvage', 'robust-support'].map(id => document.getElementById(id));
function renderRobustness() {
  const [cost, salvage, support] = robustnessControls.map(control => control.value);
  const matches = config => config.cost_ratio === Number(cost) && config.salvage_ratio === Number(salvage) && config.support === support;
  const aggregate = robustnessReport.aggregate.find(matches);
  const percentage = value => value === null ? '—' : `${numberFormat.format(value * 100)}%`;
  document.getElementById('robustness-summary').innerHTML = Object.entries(aggregate.metrics).map(([rule, metrics]) => `<tr><th scope="row">${ruleNames[rule]}</th><td>${metrics.sole_wins}</td><td>${metrics.shared_wins}</td><td>${metrics.loss_cases}</td><td>${percentage(metrics.mean_profit_reference_ratio)}</td><td>${percentage(metrics.mean_regret_reference_ratio)}</td></tr>`).join('');
  document.getElementById('robustness-cases').innerHTML = robustnessReport.cases.map(sample => {
    const config = sample.configurations.find(matches);
    return `<tr><th scope="row">${sample.item} / ${sample.store}</th><td>${sample.test_start} → ${sample.test_end}</td><td>${sample.test_sales}</td>${Object.keys(ruleNames).map(rule => `<td>${numberFormat.format(config.summary[rule].profit)}</td>`).join('')}<td>${config.winners.map(rule => ruleNames[rule]).join(' / ')}</td></tr>`;
  }).join('');
  const bestCount = Math.max(...Object.values(aggregate.metrics).map(metrics => metrics.fractional_wins));
  const leaders = Object.entries(aggregate.metrics).filter(([, metrics]) => Math.abs(metrics.fractional_wins - bestCount) < 1e-8).map(([rule]) => ruleNames[rule]);
  document.getElementById('robustness-observation').textContent = `Bu ayarda, eşit birincilik paylaştırıldığında en çok birinci olan: ${leaders.join(' / ')} (${numberFormat.format(bestCount)} / ${robustnessReport.case_count}). Bu, gelecekteki üstünlüğün kanıtı değildir. Aynı ürün farklı dönemlerde farklı sonuç verebilir.`;
}
robustnessControls.forEach(control => control.addEventListener('change', renderRobustness));
renderRobustness();
