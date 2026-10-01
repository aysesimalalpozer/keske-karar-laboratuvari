const linkedReport = JSON.parse(document.getElementById('linked-data').textContent);
const linkedNames = {...ruleNames, forecast_point: 'Tahmin kadar sipariş', forecast_distribution: 'Tahmin + hata dağılımı + maliyet'};
const linkedModelNames = {seasonal_naive:'Geçen haftanın aynı günü',past_28_mean:'Son 28 gün ortalaması',lag_regression:'Geçmiş satış + takvim regresyonu'};
const linkedControls = ['linked-case','linked-cost','linked-salvage'].map(id => document.getElementById(id));
function renderLinkedDecisions() {
  const [sampleIndex,cost,salvage] = linkedControls.map(control => control.value);
  const sample = linkedReport.cases[Number(sampleIndex)];
  const config = sample.configurations.find(c => c.cost_ratio === Number(cost) && c.salvage_ratio === Number(salvage));
  document.getElementById('linked-protocol').textContent = `Seçilen tahmin: ${linkedModelNames[sample.selected_model]}. Test MAE: ${numberFormat.format(sample.test_mae)} ürün. Model eğitimi sonu ${sample.fit_end}; model seçimi sonu ${sample.selection_end}; hata kalibrasyonu sonu ${sample.calibration_end}. Test: ${sample.test_start} – ${sample.test_end}.`;
  document.getElementById('linked-results').innerHTML = Object.entries(config.summary).map(([rule,result]) => `<tr><th scope="row">${linkedNames[rule]}</th><td>${numberFormat.format(result.mean_quantity)}</td><td>${numberFormat.format(result.profit)}</td><td>${result.remaining}</td><td>${result.uncovered_reference}</td><td>${numberFormat.format(result.regret)}</td></tr>`).join('');
  let wins=0,ties=0,losses=0;
  for (const entry of linkedReport.cases) {
    const c=entry.configurations.find(c => c.cost_ratio === Number(cost) && c.salvage_ratio === Number(salvage));
    const difference=c.summary.forecast_distribution.profit-c.summary.forecast_point.profit;
    if (difference>1e-8) wins++; else if(difference < -1e-8) losses++; else ties++;
  }
  document.getElementById('linked-observation').textContent = `Bu maliyet ayarında, 30 ürün–dönemde dağılımlı kararın doğrudan tahmin kadar siparişe göre kârı: ${wins} daha yüksek, ${ties} eşit, ${losses} daha düşük. Tahmini maliyete bağlamak her dönemde iyileşme garantisi vermez.`;
  document.getElementById('linked-daily').innerHTML = config.daily.forecast_distribution.map((row,index) => `<tr><th scope="row">${row.date}</th><td>${numberFormat.format(row.forecast)}</td><td>${config.daily.forecast_point[index].quantity}</td><td>${row.quantity}</td><td>${row.sales_reference}</td><td>${numberFormat.format(row.profit)}</td></tr>`).join('');
}
linkedControls.forEach(control => control.addEventListener('change', renderLinkedDecisions));
renderLinkedDecisions();
