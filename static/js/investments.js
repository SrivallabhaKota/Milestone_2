/* ═══════════════════════════════════════════════════════════════════════════
   investments.js — Live P&L Preview on investment form
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  const investedInput = document.getElementById('invested_amount');
  const currentInput  = document.getElementById('current_value');

  const prevInvested = document.getElementById('prev-invested');
  const prevCurrent  = document.getElementById('prev-current');
  const prevPl       = document.getElementById('prev-pl');
  const prevReturn   = document.getElementById('prev-return');
  const prevBadge    = document.getElementById('prev-status-badge');

  if (!investedInput || !currentInput) return;

  function fmt(n) {
    return '₹' + Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  function update() {
    const invested = parseFloat(investedInput.value) || 0;
    const current  = parseFloat(currentInput.value) || 0;
    const pl       = current - invested;
    const retPct   = invested > 0 ? ((pl / invested) * 100).toFixed(2) : 0;

    if (prevInvested) prevInvested.textContent = invested ? fmt(invested) : '—';
    if (prevCurrent)  prevCurrent.textContent  = current  ? fmt(current)  : '—';

    if (prevPl) {
      prevPl.textContent = invested
        ? (pl >= 0 ? '+' : '-') + fmt(pl)
        : '—';
      prevPl.style.color = pl > 0 ? 'var(--success)' : pl < 0 ? 'var(--danger)' : 'var(--text-primary)';
    }

    if (prevReturn) {
      prevReturn.textContent = invested ? (retPct >= 0 ? '+' : '') + retPct + '%' : '—';
      prevReturn.style.color = retPct > 0 ? 'var(--success)' : retPct < 0 ? 'var(--danger)' : 'var(--text-primary)';
    }

    if (prevBadge) {
      const label = pl > 0 ? 'Profit' : pl < 0 ? 'Loss' : 'No Change';
      const cls   = pl > 0 ? 'success' : pl < 0 ? 'danger' : 'secondary';
      prevBadge.innerHTML = invested
        ? `<span class="badge badge-${cls}" style="font-size:14px;padding:6px 16px;">${label}</span>`
        : '';
    }
  }

  investedInput.addEventListener('input', update);
  currentInput.addEventListener('input', update);
  update();
});
