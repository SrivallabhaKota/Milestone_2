/* ═══════════════════════════════════════════════════════════════════════════
   goals.js — Live calculation preview on Goal Planning / Edit Goal form
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('goalForm');
  if (!form) return;

  const targetInput   = document.getElementById('target_amount');
  const currentInput  = document.getElementById('current_amount');
  const targetDateIn  = document.getElementById('target_date');
  const startDateIn   = document.getElementById('start_date');

  const prevTarget    = document.getElementById('prev-target');
  const prevCurrent   = document.getElementById('prev-current');
  const prevRemaining = document.getElementById('prev-remaining');
  const prevProgress  = document.getElementById('prev-progress');
  const prevMonths    = document.getElementById('prev-months');
  const prevMonthly   = document.getElementById('prev-monthly');
  const prevWeekly    = document.getElementById('prev-weekly');
  const prevBar       = document.getElementById('prev-bar');
  const prevBarLabel  = document.getElementById('prev-bar-label');

  function fmt(n) {
    return '₹' + n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  function updatePreview() {
    const target  = parseFloat(targetInput?.value)  || 0;
    const current = parseFloat(currentInput?.value) || 0;
    const targetDateStr = targetDateIn?.value;

    const remaining   = Math.max(target - current, 0);
    const progressPct = target > 0 ? Math.min((current / target) * 100, 100) : 0;

    // Months left
    let monthsLeft = null;
    if (targetDateStr) {
      const tDate = new Date(targetDateStr);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const diffDays = Math.max((tDate - today) / (1000 * 60 * 60 * 24), 0);
      monthsLeft = diffDays / 30.44;
    }

    const monthlyNeeded = (monthsLeft != null && monthsLeft > 0)
      ? remaining / monthsLeft : 0;
    const weeklyNeeded  = monthlyNeeded / 4.33;

    // Update DOM
    if (prevTarget)    prevTarget.textContent    = target  ? fmt(target)   : '—';
    if (prevCurrent)   prevCurrent.textContent   = current ? fmt(current)  : '₹0';
    if (prevRemaining) prevRemaining.textContent = fmt(remaining);
    if (prevProgress)  prevProgress.textContent  = progressPct.toFixed(1) + '%';
    if (prevMonths)    prevMonths.textContent    = monthsLeft != null
      ? monthsLeft.toFixed(1) + ' months' : '—';
    if (prevMonthly)   prevMonthly.textContent   = monthlyNeeded
      ? fmt(monthlyNeeded) + '/mo' : '—';
    if (prevWeekly)    prevWeekly.textContent    = weeklyNeeded
      ? fmt(weeklyNeeded) + '/wk' : '—';

    // Progress bar
    if (prevBar) {
      prevBar.style.width = progressPct + '%';
      prevBar.classList.remove('green', 'orange', 'red');
      if (progressPct >= 100) prevBar.classList.add('green');
    }
    if (prevBarLabel) {
      prevBarLabel.textContent = progressPct.toFixed(1) + '% complete';
    }
  }

  // Attach listeners
  [targetInput, currentInput, targetDateIn, startDateIn].forEach(el => {
    el?.addEventListener('input', updatePreview);
    el?.addEventListener('change', updatePreview);
  });

  // Initial call
  updatePreview();

  // ─── Form Validation ────────────────────────────────────────────────
  form.addEventListener('submit', e => {
    const target  = parseFloat(targetInput?.value) || 0;
    const current = parseFloat(currentInput?.value) || 0;
    const goalName = document.getElementById('goal_name')?.value.trim();
    const targetDate = targetDateIn?.value;
    const startDate  = startDateIn?.value;

    let errors = [];

    if (!goalName) errors.push('Goal name is required.');
    if (target <= 0) errors.push('Target amount must be greater than zero.');
    if (current < 0) errors.push('Current amount cannot be negative.');
    if (current > target) errors.push('Current amount cannot exceed target amount.');
    if (targetDate && startDate && targetDate <= startDate) {
      errors.push('Target date must be after start date.');
    }

    if (errors.length > 0) {
      e.preventDefault();
      // Show inline error
      let container = document.getElementById('jsErrorContainer');
      if (!container) {
        container = document.createElement('div');
        container.id = 'jsErrorContainer';
        form.insertBefore(container, form.firstChild);
      }
      container.innerHTML = errors.map(err =>
        `<div class="alert alert-danger">
           <i class="fas fa-exclamation-circle"></i> ${err}
           <button class="alert-close" onclick="this.parentElement.remove()">&times;</button>
         </div>`
      ).join('');
      container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
});
