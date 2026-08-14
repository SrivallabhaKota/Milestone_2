/* ═══════════════════════════════════════════════════════════════════════════
   charts.js — Dashboard Chart.js initializations (Goals + Investments)
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/dashboard-data')
    .then(r => r.json())
    .then(data => {
      initStatusChart(data.status_distribution);
      initCategoryChart(data.category_distribution);
      initInvTypeChart(data.investment_type_distribution);
      initInvVsCurrentChart(data.inv_vs_current);
      initTargetVsSaved(data.target_vs_saved);
      initTrendChart(data.monthly_trend);
    })
    .catch(err => console.warn('Chart data error:', err));
});

// ─── Shared Defaults ───────────────────────────────────────────────────────
const FF = "'Inter', system-ui, sans-serif";
Chart.defaults.font.family = FF;
Chart.defaults.color = '#64748B';

const PALETTE = ['#2563EB','#16A34A','#D97706','#DC2626','#7C3AED','#0D9488','#DB2777','#EA580C'];

function tip(extra = {}) {
  return {
    backgroundColor: '#0F172A', titleFont: { family: FF, size: 12, weight: '600' },
    bodyFont: { family: FF, size: 12 }, padding: 10, cornerRadius: 8, ...extra
  };
}

function noData(canvas) {
  const p = canvas.parentElement;
  canvas.style.display = 'none';
  const d = document.createElement('div');
  d.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#94A3B8;font-size:13px;gap:8px;';
  d.innerHTML = '<i class="fas fa-chart-bar" style="font-size:28px;opacity:.3;"></i><span>No data yet</span>';
  p.appendChild(d);
}

// ─── 1. Goal Status Donut ─────────────────────────────────────────────────
function initStatusChart(data) {
  const ctx = document.getElementById('statusChart');
  if (!ctx) return;
  const vals = Object.values(data);
  if (vals.reduce((a, b) => a + b, 0) === 0) { noData(ctx); return; }
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(data),
      datasets: [{ data: vals, backgroundColor: ['#2563EB','#16A34A','#6B7280'], borderColor: '#fff', borderWidth: 3, hoverOffset: 8 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { font: { family: FF, size: 12 }, padding: 16, usePointStyle: true } },
        tooltip: { ...tip(), callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } }
      }
    }
  });
}

// ─── 2. Category Bar ──────────────────────────────────────────────────────
function initCategoryChart(data) {
  const ctx = document.getElementById('categoryChart');
  if (!ctx) return;
  const labels = Object.keys(data), vals = Object.values(data);
  if (!labels.length) { noData(ctx); return; }
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Goals', data: vals,
        backgroundColor: labels.map((_, i) => PALETTE[i % PALETTE.length] + 'BB'),
        borderColor: labels.map((_, i) => PALETTE[i % PALETTE.length]),
        borderWidth: 1.5, borderRadius: 6, borderSkipped: false
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { ...tip(), callbacks: { label: c => ` ${c.parsed.y} goal${c.parsed.y !== 1 ? 's' : ''}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: FF, size: 11 } } },
        y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { stepSize: 1, font: { family: FF, size: 11 } } }
      }
    }
  });
}

// ─── 3. Investment Type Donut ─────────────────────────────────────────────
function initInvTypeChart(data) {
  const ctx = document.getElementById('invTypeChart');
  if (!ctx) return;
  const labels = Object.keys(data), vals = Object.values(data);
  if (!labels.length || vals.reduce((a, b) => a + b, 0) === 0) { noData(ctx); return; }
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: vals, backgroundColor: PALETTE, borderColor: '#fff', borderWidth: 3, hoverOffset: 8 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { font: { family: FF, size: 11 }, padding: 12, usePointStyle: true } },
        tooltip: { ...tip(), callbacks: { label: c => ` ${c.label}: ${c.parsed}` } }
      }
    }
  });
}

// ─── 4. Invested vs Current Value ─────────────────────────────────────────
function initInvVsCurrentChart(data) {
  const ctx = document.getElementById('invVsCurrentChart');
  if (!ctx) return;
  if (!data || !data.labels || !data.labels.length) { noData(ctx); return; }
  const labels = data.labels.map(l => l.length > 14 ? l.slice(0, 13) + '…' : l);
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Invested', data: data.invested, backgroundColor: '#2563EB33', borderColor: '#2563EB', borderWidth: 1.5, borderRadius: 5 },
        { label: 'Portfolio Value', data: data.current, backgroundColor: '#16A34A33', borderColor: '#16A34A', borderWidth: 1.5, borderRadius: 5 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { family: FF, size: 11 }, padding: 12, usePointStyle: true } },
        tooltip: { ...tip(), callbacks: { label: c => ` ${c.dataset.label}: ₹${c.parsed.y.toLocaleString('en-IN')}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: FF, size: 10 } } },
        y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { font: { family: FF, size: 10 }, callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v) } }
      }
    }
  });
}

// ─── 5. Goal Target vs Saved ──────────────────────────────────────────────
function initTargetVsSaved(data) {
  const ctx = document.getElementById('targetVsSavedChart');
  if (!ctx) return;
  if (!data || !data.labels || !data.labels.length) { noData(ctx); return; }
  const labels = data.labels.map(l => l.length > 14 ? l.slice(0, 13) + '…' : l);
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Target', data: data.target, backgroundColor: '#2563EB33', borderColor: '#2563EB', borderWidth: 1.5, borderRadius: 5 },
        { label: 'Saved', data: data.saved, backgroundColor: '#16A34A33', borderColor: '#16A34A', borderWidth: 1.5, borderRadius: 5 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { family: FF, size: 11 }, padding: 12, usePointStyle: true } },
        tooltip: { ...tip(), callbacks: { label: c => ` ${c.dataset.label}: ₹${c.parsed.y.toLocaleString('en-IN')}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: FF, size: 10 } } },
        y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { font: { family: FF, size: 10 }, callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v) } }
      }
    }
  });
}

// ─── 6. Monthly Savings Trend ─────────────────────────────────────────────
function initTrendChart(data) {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;
  if (!data || !data.length) { noData(ctx); return; }
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.label),
      datasets: [{
        label: 'Savings', data: data.map(d => d.amount),
        borderColor: '#2563EB', backgroundColor: 'rgba(37,99,235,.08)',
        borderWidth: 2, pointRadius: 4, pointBackgroundColor: '#2563EB',
        pointBorderColor: '#fff', pointBorderWidth: 2, fill: true, tension: 0.35
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { ...tip(), callbacks: { label: c => ` ₹${c.parsed.y.toLocaleString('en-IN')}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: FF, size: 11 } } },
        y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { font: { family: FF, size: 10 }, callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v) } }
      }
    }
  });
}
