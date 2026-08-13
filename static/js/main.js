/* ═══════════════════════════════════════════════════════════════════════════
   main.js — Sidebar, delete modal, flash auto-dismiss
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ─── Sidebar Toggle (Desktop collapse) ────────────────────────────────
  const sidebar      = document.getElementById('sidebar');
  const mainWrapper  = document.getElementById('mainWrapper');
  const toggleBtn    = document.getElementById('sidebarToggle');
  const topbarBtn    = document.getElementById('topbarMenuBtn');
  const overlay      = document.getElementById('sidebarOverlay');

  // Restore collapsed state
  const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (isCollapsed && window.innerWidth > 768) {
    sidebar?.classList.add('collapsed');
    mainWrapper?.classList.add('expanded');
  }

  toggleBtn?.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      openMobileSidebar();
    } else {
      sidebar?.classList.toggle('collapsed');
      mainWrapper?.classList.toggle('expanded');
      localStorage.setItem('sidebarCollapsed', sidebar?.classList.contains('collapsed'));
    }
  });

  // Mobile open via topbar button
  topbarBtn?.addEventListener('click', openMobileSidebar);

  function openMobileSidebar() {
    sidebar?.classList.add('mobile-open');
    overlay?.classList.add('visible');
    document.body.style.overflow = 'hidden';
  }

  function closeMobileSidebar() {
    sidebar?.classList.remove('mobile-open');
    overlay?.classList.remove('visible');
    document.body.style.overflow = '';
  }

  overlay?.addEventListener('click', closeMobileSidebar);

  // Close mobile sidebar on nav link click
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 768) closeMobileSidebar();
    });
  });

  // ─── Flash Message Auto-Dismiss ─────────────────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      alert.style.transition = 'opacity .3s, transform .3s';
      setTimeout(() => alert.remove(), 350);
    }, 5000);
  });

});

// ─── Delete Modal (global helpers) ──────────────────────────────────────
window.closeDeleteModal = function () {
  const modal = document.getElementById('deleteModal');
  if (modal) modal.style.display = 'none';
};

// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop, .panel-backdrop').forEach(el => {
      if (el.style.display !== 'none') el.style.display = 'none';
    });
  }
});
