/* ============================================
   DRIP — ui.js
   Modals, tabs, navegación inferior, estados
   ============================================ */

// ── Bottom nav click handlers ─────────────────────────────────────────────────
function initBottomNav() {
  document.querySelectorAll('.nav-bottom__item').forEach(item => {
    item.addEventListener('click', () => {
      const view = item.dataset.view;
      if (view) navigateTo(view);
    });
  });
}

// ── Modal open / close ────────────────────────────────────────────────────────
function openModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (!overlay) return;
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';

  // Cerrar al hacer click en el overlay
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal(modalId);
  }, { once: true });
}

function closeModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (!overlay) return;
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function initTabs(containerSelector) {
  const containers = document.querySelectorAll(containerSelector);
  containers.forEach(container => {
    container.querySelectorAll('.tab-item').forEach(tab => {
      tab.addEventListener('click', () => {
        container.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        const targetId = tab.dataset.tab;
        const panel = document.getElementById(targetId);
        if (panel) {
          panel.parentElement.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
          panel.classList.add('active');
        }
      });
    });
  });
}

// ── Period selector for charts ────────────────────────────────────────────────
function initPeriodBtns() {
  document.querySelectorAll('.chart-period-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const group = this.closest('.chart-card__period');
      group?.querySelectorAll('.chart-period-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
    });
  });
}

// ── Notification badge ────────────────────────────────────────────────────────
function updateAlertBadge() {
  const count = ALERTAS.filter(a => !a.atendida).length;
  const badge = document.getElementById('alert-badge');
  if (badge) {
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  }
}

// ── Toast notification ────────────────────────────────────────────────────────
function showToast(msg, type = 'success', duration = 3000) {
  const existing = document.getElementById('drip-toast');
  if (existing) existing.remove();

  const colors = {
    success: 'var(--green-primary)',
    warning: 'var(--color-warning)',
    danger:  'var(--color-danger)',
    info:    'var(--blue-gray)',
  };

  const toast = document.createElement('div');
  toast.id = 'drip-toast';
  toast.style.cssText = `
    position: fixed;
    bottom: calc(var(--nav-bottom-height) + 16px);
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: ${colors[type] || colors.success};
    color: #fff;
    padding: 10px 20px;
    border-radius: var(--radius-full);
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    z-index: 999;
    white-space: nowrap;
    opacity: 0;
    transition: all 0.3s ease;
    max-width: calc(var(--app-max-width) - 40px);
    text-align: center;
  `;
  toast.textContent = msg;
  document.getElementById('app').appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(-50%) translateY(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Atender alerta ────────────────────────────────────────────────────────────
function atenderAlerta(idx) {
  if (ALERTAS[idx]) {
    ALERTAS[idx].atendida = true;
    const card = document.querySelector(`[data-alerta="${idx}"]`);
    if (card) card.classList.add('atendida');
    updateAlertBadge();
    showToast('Alerta atendida correctamente', 'success');
  }
}

// ── Init UI ───────────────────────────────────────────────────────────────────
function initUI() {
  initBottomNav();
  initTabs('.tabs');
  initPeriodBtns();
  updateAlertBadge();
}
