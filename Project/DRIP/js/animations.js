/* ============================================
   DRIP — animations.js
   Fade-in, hover, transiciones, microinteracciones
   ============================================ */

// ── Intersection Observer: fade-in al entrar en viewport ─────────────────────
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('anim-visible');
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -20px 0px' });

function initFadeAnimations() {
  document.querySelectorAll('.anim-fade').forEach(el => {
    fadeObserver.observe(el);
  });
}

// ── KPI counter animation ─────────────────────────────────────────────────────
function animateCounter(el, from, to, duration = 800, suffix = '') {
  const start = performance.now();
  const isFloat = String(to).includes('.');
  const decimals = isFloat ? String(to).split('.')[1].length : 0;

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = from + (to - from) * eased;
    el.textContent = current.toFixed(decimals) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function animateAllCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const to = parseFloat(el.dataset.counter);
    const suffix = el.dataset.suffix || '';
    animateCounter(el, 0, to, 900, suffix);
  });
}

// ── Progress bar animated fill ────────────────────────────────────────────────
function animateProgressBars() {
  document.querySelectorAll('.progress-bar__fill[data-width]').forEach(el => {
    el.style.width = '0%';
    setTimeout(() => {
      el.style.width = el.dataset.width + '%';
    }, 100);
  });
}

// ── Ripple effect on buttons ──────────────────────────────────────────────────
function initRipple() {
  document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const ripple = document.createElement('span');
      ripple.className = 'btn-ripple';
      ripple.style.cssText = `left:${x}px;top:${y}px;`;
      this.appendChild(ripple);
      ripple.addEventListener('animationend', () => ripple.remove());
    });
  });
}

// ── Screen transition helper ──────────────────────────────────────────────────
function pageTransition(el) {
  el.style.opacity = '0';
  el.style.transform = 'translateY(10px)';
  requestAnimationFrame(() => {
    el.style.transition = 'opacity 0.28s ease, transform 0.28s ease';
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });
}

// ── Shake animation for validation errors ────────────────────────────────────
function shakeElement(el) {
  el.classList.add('anim-shake');
  el.addEventListener('animationend', () => el.classList.remove('anim-shake'), { once: true });
}

// ── Init all animations ───────────────────────────────────────────────────────
function initAnimations() {
  initFadeAnimations();
  initRipple();
}
