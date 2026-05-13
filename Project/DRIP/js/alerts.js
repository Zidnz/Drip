/* ============================================
   DRIP — alerts.js
   Render: alertas, sensores IoT
   ============================================ */

function renderAlertas() {
  const list = document.getElementById('alert-list');
  if (!list || list.children.length) return;

  const cfg = {
    alta:  { icon: 'alert-octagon',  icBg: 'rgba(212,91,58,0.12)',  icC: '#D45B3A', pillCls: 'badge--danger'  },
    media: { icon: 'alert-triangle', icBg: 'rgba(232,168,56,0.12)', icC: '#E8A838', pillCls: 'badge--warning' },
    baja:  { icon: 'info',           icBg: 'rgba(123,155,53,0.12)', icC: '#7B9B35', pillCls: 'badge--success' },
  };

  const labels = { alta: 'ALTA', media: 'MEDIA', baja: 'BAJA' };

  ALERTAS.forEach((a, idx) => {
    const p = PARCELAS.find(x => x.id === a.pid);
    const { icon, icBg, icC, pillCls } = cfg[a.p];
    const el = document.createElement('article');
    el.className = `alert-card ${a.p}${a.atendida ? ' atendida' : ''}`;
    el.dataset.alerta = idx;
    el.innerHTML = `
      <div class="alert-card__icon" style="background:${icBg};">
        ${ic(icon, 18, icC)}
      </div>
      <div class="alert-card__body">
        <div class="alert-card__title">
          ${ic('leaf', 12, p?.color ?? '#7B9B35')} ${a.tipo} · ${p?.nombre}
        </div>
        <p class="alert-card__msg">${a.msg}</p>
        <div class="alert-card__footer">
          ${ic('clock', 10, 'var(--gray-soft)')} ${a.hora}
          ${a.atendida ? `<span class="alert-card__atendida">${ic('check', 10, 'var(--green-primary)')} Atendida</span>` : ''}
        </div>
      </div>
      <div class="alert-card__actions">
        <span class="badge ${pillCls}">${labels[a.p]}</span>
        ${!a.atendida
          ? `<button class="btn btn--primary btn--sm" onclick="atenderAlerta(${idx})">${ic('check', 12, '#fff')} Atender</button>`
          : ''}
      </div>`;
    list.appendChild(el);
  });

  featherReplace();
}

// ── Sensores ──────────────────────────────────────────────────────────────────
function renderSensores() {
  const list = document.getElementById('sens-list');
  if (!list || list.children.length) return;

  const statusCfg = {
    activo:       { icon: 'check-circle', color: 'var(--green-primary)', label: 'Activo'       },
    bateria_baja: { icon: 'battery',      color: 'var(--color-warning)', label: 'Batería baja' },
    offline:      { icon: 'wifi-off',     color: 'var(--color-danger)',  label: 'Offline'      },
  };

  SENSORES.forEach(s => {
    const p   = PARCELAS.find(x => x.id === s.parc);
    const sc  = statusCfg[s.estado];
    const bc  = s.bat > 50 ? '#7B9B35' : s.bat > 20 ? '#E8A838' : '#D45B3A';
    const sensorIcon = s.tipo.includes('climática') ? 'thermometer'
                     : s.tipo.includes('Caudal')    ? 'activity'
                     : 'droplet';

    const div = document.createElement('div');
    div.className = 'sens-card';
    div.innerHTML = `
      <div class="sens-ic">${ic(sensorIcon, 20, '#7C9CA8')}</div>
      <div class="sens-info">
        <div class="sens-name">${s.id} · ${s.tipo}</div>
        <div class="sens-meta">
          ${s.modelo} · ${ic('leaf', 10, p?.color ?? '#7B9B35')} ${p?.nombre ?? '–'} · ${s.zona}
          ${s.prof ? ` · ${s.prof} cm prof.` : ''}
        </div>
        ${s.hum
          ? `<div class="sens-readings">
               <span>${ic('droplet', 11, '#7C9CA8')} <strong>${s.hum}%</strong></span>
               <span>${ic('thermometer', 11, '#E8A838')} <strong>${s.temp}°C</strong></span>
               ${s.ce ? `<span>${ic('zap', 11, '#A8BE6D')} <strong>${s.ce} dS/m</strong></span>` : ''}
             </div>`
          : `<div class="sens-meta" style="margin-top:4px;">Lecturas en tiempo real</div>`
        }
      </div>
      <div class="sens-status">
        <span class="sens-status__label" style="color:${sc.color};">
          ${ic(sc.icon, 12, sc.color)} ${sc.label}
        </span>
        <span class="sens-status__bat">Bat. ${s.bat}%</span>
        <div class="bat-bar">
          <div class="bat-fill" style="width:${s.bat}%;background:${bc};"></div>
        </div>
        <span class="sens-status__time">
          ${ic('clock', 10, 'var(--gray-soft)')} hace 5 min
        </span>
      </div>`;
    list.appendChild(div);
  });

  featherReplace();
}
