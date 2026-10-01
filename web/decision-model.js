/////////////////////////////////////////////
// İş Problemi: Talep bilinmeden üretim miktarı seçmek.
// Python modelinin tarayıcıdaki karşılığı. DOM veya animasyon içermez.
/////////////////////////////////////////////
export const scenario = Object.freeze({
  quantities: Object.freeze([100, 200, 300]),
  demands: Object.freeze([100, 200, 300]),
  probabilities: Object.freeze([0.3, 0.4, 0.3]),
  price: 60,
  unitCost: 30,
  salvageValue: 10,
});

// GÖREV 1: Gelir ve maliyeti ayrı ayrı hesaplamak.
export function calculateOutcome(quantity, demand, parameters = scenario) {
  const sold = Math.min(quantity, demand);
  const remaining = quantity - sold;
  const unmetDemand = Math.max(demand - quantity, 0);
  const revenue = sold * parameters.price;
  const salvageRevenue = remaining * parameters.salvageValue;
  const productionCost = quantity * parameters.unitCost;
  const profit = revenue + salvageRevenue - productionCost;
  return { quantity, demand, sold, remaining, unmetDemand, revenue, salvageRevenue, productionCost, profit };
}

// GÖREV 2: Alternatifleri aynı talep durumlarında karşılaştırmak.
export function analyze(parameters = scenario) {
  const { quantities, demands, probabilities, price, unitCost, salvageValue } = parameters;
  if (!quantities.length || !demands.length || probabilities.length !== demands.length ||
      [...quantities, ...demands, ...probabilities, price, unitCost, salvageValue]
        .some(value => !Number.isFinite(value)) ||
      [...quantities, ...demands, ...probabilities].some(value => value < 0) ||
      Math.abs(probabilities.reduce((total, value) => total + value, 0) - 1) > 1e-9 ||
      !(0 <= salvageValue && salvageValue <= unitCost && unitCost <= price)) {
    throw new RangeError('Miktar, olasılık veya maliyet varsayımları geçersiz.');
  }
  const payoffMatrix = parameters.quantities.map(quantity =>
    parameters.demands.map(demand => calculateOutcome(quantity, demand, parameters).profit));
  const bestByState = parameters.demands.map((_, index) =>
    Math.max(...payoffMatrix.map(row => row[index])));
  const regretMatrix = payoffMatrix.map(row =>
    row.map((profit, index) => bestByState[index] - profit));
  const expectedValues = payoffMatrix.map(row =>
    row.reduce((total, profit, index) => total + profit * parameters.probabilities[index], 0));
  const scores = {
    maximax: payoffMatrix.map(row => Math.max(...row)),
    maximin: payoffMatrix.map(row => Math.min(...row)),
    minimaxRegret: regretMatrix.map(row => Math.max(...row)),
    expectedValue: expectedValues,
  };
  const choices = {};
  for (const [rule, values] of Object.entries(scores)) {
    const bestScore = rule === 'minimaxRegret' ? Math.min(...values) : Math.max(...values);
    choices[rule] = parameters.quantities.filter((_, index) => Math.abs(values[index] - bestScore) < 1e-9);
  }
  const perfectInformationValue = bestByState.reduce((total, profit, index) =>
    total + profit * parameters.probabilities[index], 0);
  return { payoffMatrix, regretMatrix, scores, choices,
    evpi: perfectInformationValue - Math.max(...expectedValues) };
}
