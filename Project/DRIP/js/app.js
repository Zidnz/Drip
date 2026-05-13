/* ============================================
   DRIP — app.js
   Entry point: init, login, splash, perfil,
   reportes y arranque de la app
   ============================================ */

// ── Render reportes ───────────────────────────────────────────────────────────
function renderReportes() {
  renderChartAhorro('ch-ahorro');
  renderChartRendimiento('ch-rend');
  renderChartET0('ch-et0');
  featherReplace();
}

// ── Render perfil ─────────────────────────────────────────────────────────────
function renderPerfil() {
  featherReplace();
}

// ── Login logic ───────────────────────────────────────────────────────────────
function handleLogin(e) {
  e.preventDefault();
  const emailEl = document.getElementById('login-email');
  const passEl  = document.getElementById('login-pass');
  const btn     = document.getElementById('login-btn');

  const email = emailEl?.value?.trim();
  const pass  = passEl?.value?.trim();

  if (!email || !pass) {
    shakeElement(document.getElementById('login-form'));
    return;
  }

  // Demo: any credentials work
  btn.textContent = 'Ingresando...';
  btn.disabled = true;

  setTimeout(() => {
    showAppScreens();
    btn.textContent = 'Ingresar';
    btn.disabled = false;
  }, 900);
}

function togglePasswordVisibility() {
  const passEl = document.getElementById('login-pass');
  if (!passEl) return;
  passEl.type = passEl.type === 'password' ? 'text' : 'password';
}

// ── App screens ───────────────────────────────────────────────────────────────
function showLoginScreen() {
  document.getElementById('screen-splash')?.classList.remove('active');
  document.getElementById('screen-login')?.classList.add('active');
  document.getElementById('screen-app')?.classList.remove('active');
}

function showAppScreens() {
  document.getElementById('screen-login')?.classList.remove('active');
  document.getElementById('screen-app')?.classList.add('active');
  navigateTo('dashboard');
}

function logout() {
  document.getElementById('screen-app')?.classList.remove('active');
  document.getElementById('screen-login')?.classList.add('active');
  // Reset renders
  Object.keys(RENDERED).forEach(k => delete RENDERED[k]);
  // Clear renderings
  ['grid-parc', 'alert-list', 'sens-list', 't-cultivos', 't-riegos'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });
}

// ── Splash → Login ────────────────────────────────────────────────────────────
function initSplash() {
  const splash = document.getElementById('screen-splash');
  if (!splash) return;
  splash.classList.add('active');

  // Después de 2.4s → ir a login
  setTimeout(() => {
    splash.style.opacity = '0';
    splash.style.transition = 'opacity 0.5s ease';
    setTimeout(showLoginScreen, 500);
  }, 2400);
}

// ── Init app ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Init feather icons
  featherReplace();

  // Init UI (nav, tabs, etc.)
  initUI();

  // Init animations
  initAnimations();

  // Splash → Login
  initSplash();

  // Login form
  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  // Topbar alert bell
  const bellBtn = document.getElementById('topbar-bell');
  if (bellBtn) bellBtn.addEventListener('click', () => navigateTo('alertas'));

  // Topbar avatar → perfil
  const avatarBtn = document.getElementById('topbar-avatar');
  if (avatarBtn) avatarBtn.addEventListener('click', () => navigateTo('perfil'));
});
