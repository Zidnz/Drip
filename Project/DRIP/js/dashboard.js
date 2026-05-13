/* ============================================
   DRIP — dashboard.js
   Render: KPIs, tabla cultivos, pronóstico
   ============================================ */

function renderDashboard() {
  // ── Greeting ──────────────────────────────────────────────────────────────
  const greetEl = document.getElementById('dash-greeting');
  if (greetEl) greetEl.textContent = greeting() + ', Danae';

  // ── KPI counters animation ─────────────────────────────────────────────────
  animateAllCounters();

  // ── Tabla resumen cultivos ─────────────────────────────────────────────────
  const tb = document.getElementById('t-cultivos');
  if (tb) {
    tb.innerHTML = '';
    PARCELAS.forEach(p => {
      const hc = humColorHex(p.humedad);
      tb.innerHTML += `
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="width:28px;height:28px;border-radius:8px;background:${p.color}20;
                display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                ${ic('leaf', 14, p.color, 2)}
              </span>
              <strong style="font-size:13px;">${p.nombre}</strong>
            </div>
          </td>
          <td><span class="badge badge--info">${p.etapa} · Día ${p.dia}</span></td>
          <td>${estadoBadge(p.estado)}</td>
          <td>
            <div style="display:flex;align-items:center;gap:6px;">
              <div style="flex:1;height:5px;border-radius:3px;background:var(--beige-light);min-width:60px;overflow:hidden;">
                <div style="height:100%;border-radius:3px;background:${hc};width:${p.humedad}%;"></div>
              </div>
              <span style="font-weight:700;color:${hc};min-width:34px;font-size:12px;">${p.humedad}%</span>
            </div>
          </td>
          <td style="font-size:12px;">${p.etc} mm</td>
          <td style="font-size:12px;">${p.estado === 'estres_hidrico'
            ? `<span style="color:var(--color-danger);font-weight:700;display:flex;align-items:center;gap:4px;">${ic('alert-circle',12,'#D45B3A')} Hoy</span>`
            : 'En 2 días'}</td>
          <td style="font-size:12px;font-weight:700;">${p.wue}</td>
        </tr>`;
    });
  }

  // ── Gráfica humedad ────────────────────────────────────────────────────────
  const p001 = PARCELAS.find(p => p.id === 'P001');
  if (p001) renderChartHumedad('ch-hum', p001);

  featherReplace();
}

// ── Riego recommendation card ─────────────────────────────────────────────────
function iniciarRiego() {
  showToast('Riego iniciado en Frijol – Lote 5', 'success');
}
