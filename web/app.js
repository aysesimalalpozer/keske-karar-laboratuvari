import { scenario, analyze, calculateOutcome } from './decision-model.js';

// GÖREV: 16 saniyelik yolculuk; yürüyüş -> pusula -> geriye bakış -> devam.
// Saniyeler görsel koreografi parametreleridir, karar modeline ait değildir.
const scene = document.querySelector('.journey-scene');
const traveler = document.querySelector('#traveler');
const travelerBody = document.querySelector('#traveler-body');
const head = document.querySelector('#traveler-head');
const arm = document.querySelector('#compass-arm');
const frontLeg = document.querySelector('#front-leg');
const backLeg = document.querySelector('#back-leg');
const phaseLabel = document.querySelector('#journey-phase');
const motionButton = document.querySelector('#motion-toggle');
const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
let motionPaused = motionPreference.matches;
let sceneVisible = true;
let elapsed = 0;
let previousTime = null;
function updateMotion() {
  motionButton.textContent = motionPaused ? 'Hareketi başlat' : 'Hareketi durdur';
  motionButton.setAttribute('aria-pressed', String(motionPaused));
}
updateMotion();
motionButton.addEventListener('click', () => { motionPaused = !motionPaused; updateMotion(); });
motionPreference.addEventListener('change', event => { motionPaused = event.matches; updateMotion(); });
if ('IntersectionObserver' in window) {
  new IntersectionObserver(entries => { sceneVisible = entries[0].isIntersecting; }, { threshold: 0.15 }).observe(scene);
}
function animateJourney(timestamp) {
  const delta = previousTime === null ? 0 : Math.min(timestamp - previousTime, 100);
  previousTime = timestamp;
  if (!motionPaused && sceneVisible) elapsed += delta;
  const seconds = (elapsed / 1000) % 16;
  const walking = seconds < 5 || (seconds >= 10 && seconds < 15);
  const position = seconds < 5 ? 260 + seconds * 55 : seconds < 10 ? 535 : Math.min(850, 535 + (seconds - 10) * 63);
  const stride = walking ? Math.sin(seconds * 9) * 20 : 0;
  const bob = walking ? Math.abs(Math.sin(seconds * 9)) * 2 : 0;
  const lookingBack = seconds >= 7.5 && seconds < 10;
  const checkingCompass = seconds >= 5 && seconds < 7.5;
  traveler.setAttribute('transform', `translate(${position} 360)`);
  travelerBody.setAttribute('transform', `translate(0 ${-bob})`);
  frontLeg.setAttribute('transform', `rotate(${stride} 0 -66)`);
  backLeg.setAttribute('transform', `rotate(${-stride} 0 -66)`);
  head.setAttribute('transform', lookingBack ? 'translate(6 0) scale(-1 1)' : checkingCompass ? 'rotate(16 0 -132)' : 'rotate(0)');
  arm.setAttribute('transform', checkingCompass ? 'rotate(-18 8 -112)' : 'rotate(0)');
  phaseLabel.textContent = checkingCompass ? 'Dur. Yönünü kontrol et.' : lookingBack ? 'Bir kez de geride bıraktığın yola bak.' : seconds >= 10 ? 'Sonra, kararınla yola devam et.' : 'Her yol bir seçimle başlar.';
  requestAnimationFrame(animateJourney);
}
requestAnimationFrame(animateJourney);

/////////////////////////////////////////////
// GÖREV 1: Ekran durumunu tanımlamak.
// Önce karar verilir, sonra talep açılır. Hesaplar model modülündedir.
/////////////////////////////////////////////
const analysis = analyze();
const money = value => new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(value);
const form = document.querySelector('#decision-form');
const worlds = document.querySelector('#worlds');
const status = document.querySelector('#status');
let userQuantity = null;
const strategies = [
  { name: 'Senin atölyen', rule: 'Senin seçimin', description: 'Talebi görmeden verdiğin karar.', color: 'user' },
  { name: 'En iyiyi kovalayan', rule: 'Maximax', description: 'En yüksek mümkün kâra odaklanır.', quantity: analysis.choices.maximax[0], color: 'optimist' },
  { name: 'En kötüye hazırlanan', rule: 'Maximin', description: 'En kötü sonucu mümkün olduğunca iyileştirir.', quantity: analysis.choices.maximin[0], color: 'conservative' },
  { name: 'Pişmanlığı azaltan', rule: 'Minimax pişmanlık', description: 'En büyük kaçırılan kârı küçültür.', quantity: analysis.choices.minimaxRegret[0], color: 'regret' },
];

// GÖREV 2: Karar tablosunu modelden oluşturmak.
document.querySelector('#payoff-table').innerHTML = scenario.quantities.map((quantity, index) =>
  `<tr><th scope="row">${quantity} ürün</th>${analysis.payoffMatrix[index].map(value => `<td>${money(value)}</td>`).join('')}<td>${money(analysis.scores.expectedValue[index])}</td></tr>`).join('');

// Her kutu 10 ürünü temsil eder. Görsel temsil hesabı değiştirmez.
function stockBlocks(quantity, sold) {
  return Array.from({ length: quantity / 10 }, (_, index) =>
    `<span class="stock-block ${sold !== null && index < sold / 10 ? 'sold' : ''}" style="--block-index:${index}" aria-hidden="true"></span>`).join('');
}

function renderWorlds(demand = null) {
  const bestProfit = demand === null ? null : Math.max(...scenario.quantities.map(quantity => calculateOutcome(quantity, demand).profit));
  worlds.innerHTML = strategies.map(strategy => {
    const quantity = strategy.quantity ?? userQuantity;
    const outcome = demand === null ? null : calculateOutcome(quantity, demand);
    return `<article class="world-card ${strategy.color}">
      <p class="rule-label">${strategy.rule}</p><h3>${strategy.name}</h3><p class="strategy-description">${strategy.description}</p>
      <div class="stock-map" role="img" aria-label="${quantity} ürün üretildi${outcome ? `, ${outcome.sold} ürün satıldı` : ''}">${stockBlocks(quantity, outcome?.sold ?? null)}</div>
      <p class="production">${quantity} <span>ürün üretildi</span></p>
      ${outcome ? `<div class="result"><span>Dönem kârı</span><strong class="${outcome.profit < 0 ? 'negative' : ''}">${money(outcome.profit)}</strong></div>
      <dl><div><dt>Satılan</dt><dd>${outcome.sold} ürün</dd></div><div><dt>Kalan</dt><dd>${outcome.remaining} ürün</dd></div><div><dt>Karşılanamayan talep</dt><dd>${outcome.unmetDemand} ürün</dd></div><div><dt>Kaçırılan kâr</dt><dd>${money(bestProfit - outcome.profit)}</dd></div></dl>
      <details class="calculation"><summary>Hesabı gör</summary><p>${outcome.sold} × 60 + ${outcome.remaining} × 10 − ${quantity} × 30 = <strong>${money(outcome.profit)}</strong></p></details>` : '<p class="waiting">Karar verildi. Talep henüz belli değil.</p>'}
    </article>`;
  }).join('');
}

form.addEventListener('submit', event => {
  event.preventDefault();
  userQuantity = Number(new FormData(form).get('quantity'));
  if (!scenario.quantities.includes(userQuantity)) return;
  form.querySelector('fieldset').disabled = true;
  form.querySelector('button').disabled = true;
  document.querySelector('#reveal-panel').hidden = false;
  document.querySelector('#worlds-section').hidden = false;
  renderWorlds();
  status.textContent = `${userQuantity} ürün üretmeye karar verdin. Şimdi bir talep durumunu aç.`;
  document.querySelector('[data-demand]').focus();
});

document.querySelectorAll('[data-demand]').forEach(button => {
  button.addEventListener('click', () => {
    if (userQuantity === null) return;
    const demand = Number(button.dataset.demand);
    document.querySelectorAll('[data-demand]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    renderWorlds(demand);
    const outcome = calculateOutcome(userQuantity, demand);
    status.textContent = `Talep ${demand} ürün. Senin dönem kârın ${money(outcome.profit)}. Bütün atölyeler aynı taleple karşılaştı.`;
    const takeaway = document.querySelector('#takeaway');
    takeaway.hidden = false;
    takeaway.textContent = 'Bu turda en çok kazananı gördün. Bir yöntemin bütün olası durumlarda daha iyi olduğunu söylemek için tek tur yeterli değil. Diğer talep durumlarını da açıp karşılaştır.';
  });
});

document.querySelector('#reset').addEventListener('click', () => {
  userQuantity = null;
  form.reset();
  form.querySelector('fieldset').disabled = false;
  form.querySelector('button').disabled = false;
  document.querySelector('#reveal-panel').hidden = true;
  document.querySelector('#worlds-section').hidden = true;
  document.querySelector('#takeaway').hidden = true;
  document.querySelectorAll('[data-demand]').forEach(button => button.setAttribute('aria-pressed', 'false'));
  status.textContent = 'Önce üretim miktarını seç. Sonra aynı talepte sonuçları karşılaştır.';
  form.querySelector('input').focus();
});

