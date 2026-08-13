/* ═══════════════════════════════════════════════════════════════════════════
   charts.js — Dashboard Chart.js initializations
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  // Fetch chart data from the API
  fetch('/api/dashboard-data')
    .then(res => res.json())
    .then(data => {
      initStatusChart(data.status_distribution);
      initCategoryChart(data.category_distribution);
      initTargetVsSaved(data.target_vs_saved);
      initTrendChart(data.monthly_trend);
    })
    .catch(err => console.warn('Chart data fetch failed:', err));
});

// ─── Shared Defaults ─────────────────────────────────────────────────────
const fontFamily = "'Inter', system-ui, sans-serif";
Chart.defaults.font.family = fontFamily;
Chart.defaults.color = '#64748B';

function baseOptions(extras = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { font: { family: fontFamily, size: 12 }, padding: 16, usePointStyle: true },
      },
      tooltip: {
        backgroundColor: '#0F172A',
        titleFont: { family: fontFamily, size: 12, weight: '600' },
        bodyFont:  { family: fontFamily, size: 12 },
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: ctx => {
            const val = ctx.parsed.y ?? ctx.parsed;
            if (typeof val === 'number' && val > 100) {
              return ` ₹${val.toLocaleString('en-IN')}`;
            }
            return ` ${val}`;
          }
        }
      },
    },
    ...extras,
  };
}

// ─── 1. Goal Status Donut Chart ──────────────────────────────────────────
function initStatusChart(data) {
  const ctx = document.getElementById('statusChart');
  if (!ctx) return;

  const labels = Object.keys(data);
  const values = Object.values(data);
  const total  = values.reduce((a, b) => a + b, 0);

  if (total === 0) {
    showNoData(ctx); return;
  }

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: ['#2563EB', '#16A34A', '#6B7280'],
        borderColor: '#fff',
        borderWidth: 3,
        hoverOffset: 8,
      }],
    },
    options: {
      ...baseOptions(),
      plugins: {
        ...baseOptions().plugins,
        legend: { position: 'bottom', labels: { font: { family: fontFamily, size: 12 }, padding: 16, usePointStyle: true } },
        tooltip: {
          ...baseOptions().plugins.tooltip,
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed} (${((ctx.parsed / total) * 100).toFixed(0)}%)`,
          },
        },
      },
      cutout: '65%',
    },
  });
}

// ─── 2. Category Bar Chart ───────────────────────────────────────────────
function initCategoryChart(data) {
  const ctx = document.getElementById('categoryChart');
  if (!ctx) return;

  const labels = Object.keys(data);
  const values = Object.values(data);

  if (labels.length === 0) { showNoData(ctx); return; }

  const colors = [
    '#2563EB', '#16A34A', '#D97706', '#DC2626',
    '#7C3AED', '#0D9488', '#DB2777', '#EA580C'
  ];

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Goals',
        data: values,
        backgroundColor: labels.map((_, i) => colors[i % colors.length] + 'CC'),
        borderColor:     labels.map((_, i) => colors[i % colors.length]),
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      ...baseOptions({
        scales: {
          x: { grid: { display: false }, ticks: { font: { family: fontFamily, size: 11 } } },
          y: {
            beginAtZero: true, grid: { color: '#F1F5F9' },
            ticks: { stepSize: 1, font: { family: fontFamily, size: 11 } },
          },
        },
        plugins: {
          ...baseOptions().plugins,
          legend: { display: false },
          tooltip: {
            ...baseOptions().plugins.tooltip,
            callbacks: { label: ctx => ` ${ctx.parsed.y} goal${ctx.parsed.y !== 1 ? 's' : ''}` },
          },
        },
      }),
    },
  });
}

// ─── 3. Target vs Saved Grouped Bar Chart ────────────────────────────────
function initTargetVsSaved(data) {
  const ctx = document.getElementById('targetVsSavedChart');
  if (!ctx) return;

  if (!data.labels || data.labels.length === 0) { showNoData(ctx); return; }

  // Truncate long labels
  const labels = data.labels.map(l => l.length > 14 ? l.slice(0, 13) + '…' : l);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Target',
          data: data.target,
          backgroundColor: '#2563EB33',
          borderColor: '#2563EB',
          borderWidth: 1.5,
          borderRadius: 5,
        },
        {
          label: 'Saved',
          data: data.saved,
          backgroundColor: '#16A34A33',
          borderColor: '#16A34A',
          borderWidth: 1.5,
          borderRadius: 5,
        },
      ],
    },
    options: {
      ...baseOptions({
        scales: {
          x: { grid: { display: false }, ticks: { font: { family: fontFamily, size: 10 } } },
          y: {
            beginAtZero: true, grid: { color: '#F1F5F9' },
            ticks: {
              font: { family: fontFamily, size: 10 },
              callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v),
            },
          },
        },
        plugins: {
          ...baseOptions().plugins,
          legend: { position: 'bottom', labels: { font: { family: fontFamily, size: 12 }, padding: 16, usePointStyle: true } },
          tooltip: {
            ...baseOptions().plugins.tooltip,
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN')}`,
            },
          },
        },
      }),
    },
  });
}

// ─── 4. Monthly Savings Trend Line Chart ─────────────────────────────────
function initTrendChart(data) {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;

  if (!data || data.length === 0) { showNoData(ctx); return; }

  const labels  = data.map(d => d.label);
  const amounts = data.map(d => d.amount);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Savings',
        data: amounts,
        borderColor: '#2563EB',
        backgroundColor: 'rgba(37,99,235,.08)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#2563EB',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: true,
        tension: 0.35,
      }],
    },
    options: {
      ...baseOptions({
        scales: {
          x: { grid: { display: false }, ticks: { font: { family: fontFamily, size: 11 } } },
          y: {
            beginAtZero: true, grid: { color: '#F1F5F9' },
            ticks: {
              font: { family: fontFamily, size: 11 },
              callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v),
            },
          },
        },
        plugins: {
          ...baseOptions().plugins,
          legend: { display: false },
          tooltip: {
            ...baseOptions().plugins.tooltip,
            callbacks: { label: ctx => ` ₹${ctx.parsed.y.toLocaleString('en-IN')}` },
          },
        },
      }),
    },
  });
}

// ─── No Data Placeholder ─────────────────────────────────────────────────
function showNoData(canvas) {
  const parent = canvas.parentElement;
  canvas.style.display = 'none';
  const msg = document.createElement('div');
  msg.style.cssText = `display:flex;flex-direction:column;align-items:center;justify-content:center;
    height:100%;color:#94A3B8;font-size:13px;font-family:'Inter',sans-serif;gap:8px;`;
  msg.innerHTML = '<i class="fas fa-chart-bar" style="font-size:28px;opacity:.3;"></i><span>No data yet</span>';
  parent.appendChild(msg);
}
