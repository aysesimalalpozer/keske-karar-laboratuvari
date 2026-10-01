import assert from 'node:assert/strict';
import { analyze, calculateOutcome, scenario } from './decision-model.js';
const result = analyze();
assert.deepEqual(result.payoffMatrix, [[3000,3000,3000],[1000,6000,6000],[-1000,4000,9000]]);
assert.deepEqual(result.choices, {maximax:[300],maximin:[100],minimaxRegret:[200],expectedValue:[200]});
assert.deepEqual(result.scores.expectedValue, [3000,4500,4000]);
assert.equal(result.evpi,1500);
assert.equal(calculateOutcome(100,0).profit,-2000);
assert.equal(calculateOutcome(100,1000).profit,3000);
assert.deepEqual(analyze({...scenario, probabilities:[0.1,0.2,0.7]}).choices.expectedValue,[300]);
assert.throws(() => analyze({...scenario, price:NaN}), RangeError);
assert.throws(() => analyze({...scenario, probabilities:[0.2,0.2,0.2]}), RangeError);
assert.throws(() => analyze({...scenario, quantities:[]}), RangeError);
console.log('Karar tablosu, kurallar, EVPI, uç durumlar ve duyarlılık kontrolleri geçti.');

