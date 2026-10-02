/**
 * GAES 3 - Sistema de Gestión y Control de Deserciones SENA
 * Frontend Application Logic (SPA)
 */

let appState = {
  currentTab: 'dashboard',
  casos: [],
  aprendices: [],
  usuarios: [],
  stats: null,
  activeFilter: 'TODOS',
  selectedCasoId: null,
  activeDrawerTab: 'actuaciones'
};

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initModals();
  initDrawer();
  loadInitialData();
});

// Navigation & Tab Switching
function initNavigation() {
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });

  // Filter tabs on Casos list
  document.querySelectorAll('#casos-filter-tabs .filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#casos-filter-tabs .filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      appState.activeFilter = btn.dataset.filter;
      renderCasosTable();
    });
  });

  // Search inputs
  document.getElementById('input-search-casos')?.addEventListener('input', () => {
    renderCasosTable();
  });

  document.getElementById('input-search-aprendices')?.addEventListener('input', () => {
    renderAprendicesTable();
  });
}

function switchTab(tabId) {
  appState.currentTab = tabId;

  // Sidebar item states
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  // Views display
  document.querySelectorAll('.view-section').forEach(view => {
    view.classList.remove('active');
  });

  const targetView = document.getElementById(`view-${tabId}`);
  if (targetView) targetView.classList.add('active');

  // Title update
  const titleMap = {
    dashboard: { t: 'Tablero de Control', s: 'Monitoreo integral y gestión de alertas tempranas del SENA' },
    casos: { t: 'Casos de Deserción', s: 'Seguimiento, trazabilidad y control de expedientes de aprendices' },
    aprendices: { t: 'Directorio de Aprendices', s: 'Base consolidada de aprendices matriculados y sus fichas' },
    alertas: { t: 'Alertas Tempranas', s: 'Casos críticos con más de 7 días sin actuación registrada' },
    auditoria: { t: 'Auditoría Inmutable', s: 'Bitácora general de trazabilidad y eventos del sistema' }
  };

  if (titleMap[tabId]) {
    document.getElementById('page-title').textContent = titleMap[tabId].t;
    document.getElementById('page-subtitle').textContent = titleMap[tabId].s;
  }

  // Reload or refresh view data
  if (tabId === 'dashboard') loadStats();
  if (tabId === 'casos') loadCasos();
  if (tabId === 'aprendices') loadAprendices();
  if (tabId === 'alertas') renderAlertasView();
}

// Initial Data Fetch
async function loadInitialData() {
  await Promise.all([
    loadStats(),
    loadCasos(),
    loadAprendices(),
    loadUsuarios()
  ]);
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) throw new Error('Error al cargar estadísticas');
    const data = await res.json();
    appState.stats = data;

    // Render KPI Cards
    document.getElementById('stat-total-casos').textContent = data.total_casos;
    document.getElementById('stat-casos-activos').textContent = data.casos_activos;
    document.getElementById('stat-retornos').textContent = data.retornos_exitosos;
    document.getElementById('stat-alertas').textContent = data.alertas_inactividad;

    document.getElementById('badge-total-casos').textContent = data.total_casos;
    document.getElementById('badge-alertas').textContent = data.alertas_inactividad;

    // Render Distribution by State
    renderDistributionBars(data.estados_dist, data.total_casos);
    renderProgramBars(data.programas_dist);
    renderDashboardRecentCases(data.recientes);
  } catch (err) {
    console.error(err);
    showToast(err.message, 'error');
  }
}

function renderDistributionBars(estadosDist, total) {
  const container = document.getElementById('distribution-bars');
  if (!container) return;
  container.innerHTML = '';

  const stateColors = {
    REGISTRADO: '#0284c7',
    ASIGNADO: '#4f46e5',
    EN_INVESTIGACION: '#d97706',
    EN_SEGUIMIENTO: '#0d9488',
    PROPUESTO_CIERRE: '#7e22ce',
    CERRADO: '#10b981',
    REABIERTO: '#e11d48',
    ANULADO: '#dc2626'
  };

  const stateNames = {
    REGISTRADO: 'Registrado (Inicial)',
    ASIGNADO: 'Asignado a Gestor',
    EN_INVESTIGACION: 'En Investigación',
    EN_SEGUIMIENTO: 'En Seguimiento / Acuerdos',
    PROPUESTO_CIERRE: 'Propuesto para Cierre',
    CERRADO: 'Cerrado Formalmente',
    REABIERTO: 'Reabierto',
    ANULADO: 'Anulado'
  };

  Object.entries(estadosDist).forEach(([estado, count]) => {
    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
    const color = stateColors[estado] || '#64748b';
    const label = stateNames[estado] || estado;

    const div = document.createElement('div');
    div.className = 'dist-item';
    div.innerHTML = `
      <div class="dist-header">
        <span>${label}</span>
        <span><strong>${count}</strong> (${pct}%)</span>
      </div>
      <div class="dist-bar-track">
        <div class="dist-bar-fill" style="width: ${pct}%; background-color: ${color};"></div>
      </div>
    `;
    container.appendChild(div);
  });
}

function renderProgramBars(progDist) {
  const container = document.getElementById('program-bars');
  if (!container) return;
  container.innerHTML = '';

  const total = Object.values(progDist).reduce((a, b) => a + b, 0);

  Object.entries(progDist).forEach(([prog, count]) => {
    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
    const div = document.createElement('div');
    div.className = 'dist-item';
    div.innerHTML = `
      <div class="dist-header">
        <span style="font-size: 0.8rem; max-width: 75%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${prog}">${prog}</span>
        <span><strong>${count} casos</strong></span>
      </div>
      <div class="dist-bar-track">
        <div class="dist-bar-fill" style="width: ${pct}%; background-color: var(--sena-green);"></div>
      </div>
    `;
    container.appendChild(div);
  });
}

function renderDashboardRecentCases(recientes) {
  const tbody = document.getElementById('dashboard-recent-cases');
  if (!tbody) return;

  if (!recientes || recientes.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4">No hay casos registrados aún.</td></tr>';
    return;
  }

  tbody.innerHTML = recientes.map(c => {
    const alertHtml = c.dias_sin_actuacion >= 7
      ? `<span class="alert-tag critical">⚠️ ${c.dias_sin_actuacion} días</span>`
      : `<span class="alert-tag normal">${c.dias_sin_actuacion}d</span>`;

    return `
      <tr>
        <td><strong>${c.numero_caso}</strong></td>
        <td>${c.aprendiz}</td>
        <td><span style="font-weight:600">${c.ficha}</span> - <span class="text-muted" style="font-size:0.78rem;">${c.programa}</span></td>
        <td><span class="badge badge-${c.estado}">${c.estado}</span></td>
        <td>${alertHtml}</td>
        <td class="text-muted">${c.fecha}</td>
        <td class="text-right">
          <button class="btn btn-sm btn-outline" onclick="openCasoDrawer(${c.id})">Gestionar</button>
        </td>
      </tr>
    `;
  }).join('');
}

// Casos Table
async function loadCasos() {
  try {
    const res = await fetch('/api/casos');
    if (!res.ok) throw new Error('Error al cargar casos');
    appState.casos = await res.json();
    renderCasosTable();
  } catch (err) {
    console.error(err);
    showToast(err.message, 'error');
  }
}

function renderCasosTable() {
  const tbody = document.getElementById('table-casos-body');
  if (!tbody) return;

  const query = (document.getElementById('input-search-casos')?.value || '').toLowerCase().trim();
  const filter = appState.activeFilter;

  let filtrados = appState.casos.filter(c => {
    // Filter by tab
    if (filter === 'ACTIVOS' && (c.estado === 'CERRADO' || c.estado === 'ANULADO')) return false;
    if (filter === 'ALERTAS' && (c.dias_sin_actuacion < 7 || c.estado === 'CERRADO' || c.estado === 'ANULADO')) return false;
    if (filter !== 'TODOS' && filter !== 'ACTIVOS' && filter !== 'ALERTAS' && c.estado !== filter) return false;

    // Search query
    if (query) {
      const matchNum = c.numero_caso.toLowerCase().includes(query);
      const matchNom = `${c.aprendiz.nombres} ${c.aprendiz.apellidos}`.toLowerCase().includes(query);
      const matchDoc = c.aprendiz.numero_documento.includes(query);
      const matchFicha = c.aprendiz.ficha.includes(query);
      const matchMotivo = c.motivo_desercion.toLowerCase().includes(query);
      return matchNum || matchNom || matchDoc || matchFicha || matchMotivo;
    }
    return true;
  });

  if (filtrados.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4">No se encontraron casos con los filtros aplicados.</td></tr>';
    return;
  }

  tbody.innerHTML = filtrados.map(c => {
    const alertHtml = c.dias_sin_actuacion >= 7
      ? `<span class="alert-tag critical">⚠️ ${c.dias_sin_actuacion} días</span>`
      : (c.dias_sin_actuacion >= 4 ? `<span class="alert-tag warn">${c.dias_sin_actuacion} días</span>` : `<span class="alert-tag normal">${c.dias_sin_actuacion}d</span>`);

    const gestorName = c.asignado_a ? c.asignado_a.nombre : '<em class="text-muted">Sin asignar</em>';

    return `
      <tr>
        <td><strong>${c.numero_caso}</strong></td>
        <td>
          <div style="font-weight:600">${c.aprendiz.nombres} ${c.aprendiz.apellidos}</div>
          <div class="text-muted" style="font-size:0.75rem;">${c.aprendiz.email}</div>
        </td>
        <td>${c.aprendiz.tipo_documento} ${c.aprendiz.numero_documento}</td>
        <td>
          <span style="font-weight:600">${c.aprendiz.ficha}</span>
          <div class="text-muted" style="font-size:0.74rem;">${c.aprendiz.programa}</div>
        </td>
        <td><span class="badge badge-${c.estado}">${c.estado}</span></td>
        <td>${gestorName}</td>
        <td>
          <span style="font-weight:600">${c.total_actuaciones}</span> act. / <span style="font-weight:600">${c.total_compromisos}</span> comp.
        </td>
        <td>${alertHtml}</td>
        <td class="text-right">
          <button class="btn btn-sm btn-outline" onclick="openCasoDrawer(${c.id})">
            Ver FSM &rarr;
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// Aprendices View
async function loadAprendices() {
  try {
    const res = await fetch('/api/aprendices');
    if (!res.ok) throw new Error('Error al cargar aprendices');
    appState.aprendices = await res.json();
    renderAprendicesTable();
    populateAprendicesSelect();
  } catch (err) {
    console.error(err);
  }
}

function renderAprendicesTable() {
  const tbody = document.getElementById('table-aprendices-body');
  if (!tbody) return;

  const query = (document.getElementById('input-search-aprendices')?.value || '').toLowerCase().trim();

  let list = appState.aprendices;
  if (query) {
    list = list.filter(a => {
      const full = `${a.nombres} ${a.apellidos}`.toLowerCase();
      return full.includes(query) || a.numero_documento.includes(query) || a.ficha.includes(query) || a.programa.toLowerCase().includes(query);
    });
  }

  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4">No se encontraron aprendices registrados.</td></tr>';
    return;
  }

  tbody.innerHTML = list.map(a => `
    <tr>
      <td>
        <div style="font-weight:600">${a.nombres} ${a.apellidos}</div>
        <div class="text-muted" style="font-size:0.75rem;">${a.email}</div>
      </td>
      <td><strong>${a.tipo_documento}</strong> ${a.numero_documento}</td>
      <td>${a.telefono}</td>
      <td><span class="badge" style="background:#e2e8f0; color:#334155;">${a.ficha}</span></td>
      <td>${a.programa}</td>
      <td>${a.jornada}</td>
      <td class="text-right">
        <button class="btn btn-sm btn-primary" onclick="iniciarCasoParaAprendiz(${a.id})">
          + Iniciar Caso
        </button>
      </td>
    </tr>
  `).join('');
}

function populateAprendicesSelect() {
  const sel = document.getElementById('select-caso-aprendiz');
  if (!sel) return;
  sel.innerHTML = '<option value="">-- Seleccionar aprendiz registrado --</option>';
  appState.aprendices.forEach(a => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = `${a.nombres} ${a.apellidos} (${a.tipo_documento} ${a.numero_documento} - Ficha ${a.ficha})`;
    sel.appendChild(opt);
  });
}

async function loadUsuarios() {
  try {
    const res = await fetch('/api/usuarios');
    if (!res.ok) throw new Error('Error al cargar usuarios');
    appState.usuarios = await res.json();
    populateUsuariosSelect();
  } catch (err) {
    console.error(err);
  }
}

function populateUsuariosSelect() {
  const sel1 = document.getElementById('select-caso-asignado');
  const sel2 = document.getElementById('select-fsm-asignar');

  if (sel1) {
    sel1.innerHTML = '<option value="">-- Dejar en asignación pendiente (REGISTRADO) --</option>';
    appState.usuarios.forEach(u => {
      const opt = document.createElement('option');
      opt.value = u.id;
      opt.textContent = `${u.nombre} (${u.rol})`;
      sel1.appendChild(opt);
    });
  }

  if (sel2) {
    sel2.innerHTML = '<option value="">-- Seleccionar gestor GAES --</option>';
    appState.usuarios.forEach(u => {
      const opt = document.createElement('option');
      opt.value = u.id;
      opt.textContent = `${u.nombre} (${u.rol})`;
      sel2.appendChild(opt);
    });
  }
}

// Alertas View
function renderAlertasView() {
  const tbody = document.getElementById('table-alertas-body');
  if (!tbody) return;

  const alertas = appState.casos.filter(c => c.dias_sin_actuacion >= 7 && c.estado !== 'CERRADO' && c.estado !== 'ANULADO');

  if (alertas.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4" style="color:var(--success); font-weight:600;">Excelente: No hay casos con alertas de inactividad mayores a 7 días.</td></tr>';
    return;
  }

  tbody.innerHTML = alertas.map(c => `
    <tr>
      <td><strong>${c.numero_caso}</strong></td>
      <td>${c.aprendiz.nombres} ${c.aprendiz.apellidos}</td>
      <td><strong>${c.aprendiz.ficha}</strong></td>
      <td><span class="alert-tag critical">⚠️ ${c.dias_sin_actuacion} días sin gestión</span></td>
      <td><span class="badge badge-${c.estado}">${c.estado}</span></td>
      <td>${c.asignado_a ? c.asignado_a.nombre : '<em class="text-muted">Sin gestor</em>'}</td>
      <td class="text-right">
        <button class="btn btn-sm btn-primary" onclick="openCasoDrawer(${c.id})">Intervenir Ahora</button>
      </td>
    </tr>
  `).join('');
}

// DRAWER & CASO DETAIL (FSM Management)
function initDrawer() {
  const drawer = document.getElementById('case-drawer');
  const overlay = document.getElementById('drawer-overlay');
  const closeBtn = document.getElementById('drawer-close-btn');

  overlay?.addEventListener('click', closeCasoDrawer);
  closeBtn?.addEventListener('click', closeCasoDrawer);

  // Drawer tabs
  document.querySelectorAll('.drawer-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.drawer-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.dtab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const dtab = btn.dataset.dtab;
      document.getElementById(`dtab-${dtab}`)?.classList.add('active');
    });
  });

  // Action buttons inside drawer
  document.getElementById('btn-open-modal-actuacion')?.addEventListener('click', () => {
    openModal('modal-nueva-actuacion');
  });

  document.getElementById('btn-open-modal-compromiso')?.addEventListener('click', () => {
    // Set default date to today + 5 days
    const d = new Date();
    d.setDate(d.getDate() + 5);
    document.getElementById('input-compromiso-fecha').value = d.toISOString().split('T')[0];
    openModal('modal-nuevo-compromiso');
  });
}

async function openCasoDrawer(casoId) {
  appState.selectedCasoId = casoId;
  const drawer = document.getElementById('case-drawer');
  const overlay = document.getElementById('drawer-overlay');

  try {
    const res = await fetch(`/api/casos/${casoId}`);
    if (!res.ok) throw new Error('Error al cargar detalle del caso');
    const c = await res.json();

    // Populate drawer header
    document.getElementById('drawer-caso-numero').textContent = c.numero_caso;
    document.getElementById('drawer-aprendiz-nombre').textContent = `${c.aprendiz.nombres} ${c.aprendiz.apellidos}`;
    
    const badgeEstado = document.getElementById('drawer-caso-estado');
    badgeEstado.className = `badge badge-${c.estado}`;
    badgeEstado.textContent = c.estado;

    // Stepper updates
    updateFSMStepper(c.estado);

    // Transition buttons
    renderFSMActionButtons(c.transiciones_permitidas, c.estado);

    // Tabs counts
    document.getElementById('count-drawer-actuaciones').textContent = c.actuaciones.length;
    document.getElementById('count-drawer-compromisos').textContent = c.compromisos.length;
    document.getElementById('count-drawer-auditoria').textContent = c.auditorias.length;

    // Render Actuaciones Timeline
    renderActuacionesTimeline(c.actuaciones);

    // Render Compromisos
    renderCompromisosList(c.compromisos);

    // Render Apprentice Info
    renderApprenticeInfo(c);

    // Render Auditoria Timeline
    renderAuditoriaTimeline(c.auditorias);

    // Open drawer
    overlay.classList.add('active');
    drawer.classList.add('active');
  } catch (err) {
    console.error(err);
    showToast(err.message, 'error');
  }
}

function closeCasoDrawer() {
  document.getElementById('case-drawer')?.classList.remove('active');
  document.getElementById('drawer-overlay')?.classList.remove('active');
}

function updateFSMStepper(estadoActual) {
  const stepsOrder = ['REGISTRADO', 'ASIGNADO', 'EN_INVESTIGACION', 'EN_SEGUIMIENTO', 'PROPUESTO_CIERRE', 'CERRADO'];
  const currentIndex = stepsOrder.indexOf(estadoActual);

  const stepper = document.getElementById('fsm-stepper');
  if (!stepper) return;

  const stepEls = stepper.querySelectorAll('.step');
  const lineEls = stepper.querySelectorAll('.step-line');

  stepEls.forEach((el, idx) => {
    el.classList.remove('completed', 'current');
    if (idx < currentIndex) {
      el.classList.add('completed');
    } else if (idx === currentIndex) {
      el.classList.add('current');
    }
  });

  lineEls.forEach((el, idx) => {
    el.classList.toggle('completed', idx < currentIndex);
  });
}

function renderFSMActionButtons(transiciones, estadoActual) {
  const container = document.getElementById('fsm-dynamic-buttons');
  if (!container) return;
  container.innerHTML = '';

  if (!transiciones || transiciones.length === 0) {
    container.innerHTML = '<span class="text-muted" style="font-size:0.8rem;">No hay transiciones adicionales disponibles (Estado Terminal).</span>';
    return;
  }

  const actionLabels = {
    ASIGNADO: { text: 'Asignar Caso a Gestor', cls: 'btn-primary' },
    EN_INVESTIGACION: { text: 'Iniciar Investigación', cls: 'btn-primary' },
    EN_SEGUIMIENTO: { text: 'Establecer Seguimiento', cls: 'btn-primary' },
    PROPUESTO_CIERRE: { text: 'Proponer Cierre de Caso', cls: 'btn-outline' },
    CERRADO: { text: 'Aprobar Cierre Formal', cls: 'btn-primary' },
    REABIERTO: { text: 'Reabrir Caso', cls: 'btn-outline' },
    ANULADO: { text: 'Anular Caso', cls: 'btn-ghost' }
  };

  transiciones.forEach(targetState => {
    const info = actionLabels[targetState] || { text: `Pasar a ${targetState}`, cls: 'btn-outline' };
    const btn = document.createElement('button');
    btn.className = `btn btn-sm ${info.cls}`;
    btn.textContent = info.text;
    btn.addEventListener('click', () => {
      openTransicionModal(targetState, estadoActual);
    });
    container.appendChild(btn);
  });
}

function renderActuacionesTimeline(actuaciones) {
  const container = document.getElementById('drawer-actuaciones-timeline');
  if (!container) return;

  if (!actuaciones || actuaciones.length === 0) {
    container.innerHTML = `
      <div class="timeline-empty" style="padding: 20px 0; color:var(--text-muted); font-size:0.84rem;">
        No hay actuaciones registradas aún. Haga clic en <strong>"Registrar Actuación"</strong> para agregar la primera llamada, citación o visita.
      </div>
    `;
    return;
  }

  container.innerHTML = actuaciones.map(a => {
    const formattedDate = new Date(a.fecha_actuacion).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
    const nextHtml = a.proxima_accion ? `<div class="timeline-next">→ Próximo paso: ${a.proxima_accion}</div>` : '';

    return `
      <div class="timeline-item">
        <div class="timeline-dot"></div>
        <div class="timeline-card">
          <div class="timeline-header">
            <span class="timeline-title">${a.tipo} • <span style="color:var(--sena-green);">${a.resultado}</span></span>
            <span class="timeline-date">${formattedDate}</span>
          </div>
          <p class="timeline-desc">${a.observaciones}</p>
          ${nextHtml}
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:6px;">Registrado por: ${a.usuario_nombre}</div>
        </div>
      </div>
    `;
  }).join('');
}

function renderCompromisosList(compromisos) {
  const container = document.getElementById('drawer-compromisos-list');
  if (!container) return;

  if (!compromisos || compromisos.length === 0) {
    container.innerHTML = `
      <div style="padding: 20px 0; color:var(--text-muted); font-size:0.84rem;">
        No hay compromisos pendientes. Registre compromisos adquiridos con el aprendiz para asegurar su retención.
      </div>
    `;
    return;
  }

  container.innerHTML = compromisos.map(cmp => {
    const isDone = cmp.estado === 'CUMPLIDO';
    const limitDate = new Date(cmp.fecha_limite).toLocaleDateString('es-CO', { dateStyle: 'medium' });

    return `
      <div class="compromiso-card ${isDone ? 'cumplido' : ''}">
        <input type="checkbox" class="compromiso-checkbox" ${isDone ? 'checked' : ''} onchange="toggleCompromisoEstado(${cmp.id}, this.checked)">
        <div class="compromiso-body">
          <div class="compromiso-desc">${cmp.descripcion}</div>
          <div class="compromiso-meta">
            <span>Responsable: <strong>${cmp.responsable}</strong></span>
            <span>Plazo: <strong>${limitDate}</strong></span>
            <span>Estado: <strong>${cmp.estado}</strong></span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function toggleCompromisoEstado(compromisoId, isChecked) {
  const nuevoEstado = isChecked ? 'CUMPLIDO' : 'PENDIENTE';
  try {
    const res = await fetch(`/api/compromisos/${compromisoId}/estado`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nuevo_estado: nuevoEstado })
    });
    if (!res.ok) throw new Error('Error al actualizar compromiso');
    showToast(`Compromiso marcado como ${nuevoEstado}`);
    // Reload active drawer
    openCasoDrawer(appState.selectedCasoId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderApprenticeInfo(c) {
  const container = document.getElementById('drawer-info-grid');
  if (!container) return;

  const a = c.aprendiz;
  container.innerHTML = `
    <div class="info-box">
      <div class="info-box-label">Aprendiz</div>
      <div class="info-box-val">${a.nombres} ${a.apellidos}</div>
    </div>
    <div class="info-box">
      <div class="info-box-label">Documento</div>
      <div class="info-box-val">${a.tipo_documento} ${a.numero_documento}</div>
    </div>
    <div class="info-box">
      <div class="info-box-label">Correo Institucional</div>
      <div class="info-box-val">${a.email}</div>
    </div>
    <div class="info-box">
      <div class="info-box-label">Teléfono de Contacto</div>
      <div class="info-box-val">${a.telefono}</div>
    </div>
    <div class="info-box">
      <div class="info-box-label">Código Ficha</div>
      <div class="info-box-val">${a.ficha}</div>
    </div>
    <div class="info-box">
      <div class="info-box-label">Jornada</div>
      <div class="info-box-val">${a.jornada}</div>
    </div>
    <div class="info-box" style="grid-column: span 2;">
      <div class="info-box-label">Programa de Formación</div>
      <div class="info-box-val">${a.programa}</div>
    </div>
    <div class="info-box" style="grid-column: span 2;">
      <div class="info-box-label">Motivo Inicial de Deserción</div>
      <div class="info-box-val">${c.motivo_desercion}</div>
    </div>
  `;
}

function renderAuditoriaTimeline(auditorias) {
  const container = document.getElementById('drawer-auditoria-timeline');
  if (!container) return;

  if (!auditorias || auditorias.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:0.84rem;">No hay registros de auditoría.</div>';
    return;
  }

  container.innerHTML = auditorias.map(aud => {
    const formatted = new Date(aud.fecha).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
    return `
      <div class="timeline-item">
        <div class="timeline-dot" style="border-color:var(--slate-700);"></div>
        <div class="timeline-card">
          <div class="timeline-header">
            <span class="timeline-title">${aud.accion}</span>
            <span class="timeline-date">${formatted}</span>
          </div>
          <p class="timeline-desc">${aud.detalle}</p>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">Usuario: ${aud.usuario_nombre}</div>
        </div>
      </div>
    `;
  }).join('');
}

// MODAL HANDLERS & FORMS
function initModals() {
  document.getElementById('btn-nuevo-caso')?.addEventListener('click', () => {
    openModal('modal-nuevo-caso');
  });

  document.getElementById('btn-nuevo-aprendiz')?.addEventListener('click', () => {
    openModal('modal-nuevo-aprendiz');
  });

  // Submit: Nuevo Caso
  document.getElementById('form-nuevo-caso')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const aprendizId = parseInt(document.getElementById('select-caso-aprendiz').value);
    const motivo = document.getElementById('input-caso-motivo').value.trim();
    const desc = document.getElementById('input-caso-descripcion').value.trim();
    const asignado = document.getElementById('select-caso-asignado').value;

    if (!aprendizId || !motivo) {
      showToast('Por favor complete los campos obligatorios', 'error');
      return;
    }

    try {
      const res = await fetch('/api/casos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aprendiz_id: aprendizId,
          motivo_desercion: motivo,
          descripcion_inicial: desc || null,
          asignado_a_id: asignado ? parseInt(asignado) : null
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al crear caso');
      }

      const data = await res.json();
      showToast(`Caso ${data.numero_caso} registrado exitosamente!`);
      closeModal('modal-nuevo-caso');
      document.getElementById('form-nuevo-caso').reset();
      
      await loadCasos();
      await loadStats();
      switchTab('casos');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Submit: Nueva Actuación
  document.getElementById('form-nueva-actuacion')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!appState.selectedCasoId) return;

    const tipo = document.getElementById('select-actuacion-tipo').value;
    const resultado = document.getElementById('select-actuacion-resultado').value;
    const obs = document.getElementById('input-actuacion-obs').value.trim();
    const prox = document.getElementById('input-actuacion-proxima').value.trim();

    try {
      const res = await fetch(`/api/casos/${appState.selectedCasoId}/actuaciones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tipo: tipo,
          resultado: resultado,
          observaciones: obs,
          proxima_accion: prox || null,
          usuario_nombre: 'Juan David Berroterán'
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al guardar actuación');
      }

      showToast('Actuación registrada con éxito');
      closeModal('modal-nueva-actuacion');
      document.getElementById('form-nueva-actuacion').reset();

      // Refresh drawer & general list
      await openCasoDrawer(appState.selectedCasoId);
      await loadCasos();
      await loadStats();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Submit: Nuevo Compromiso
  document.getElementById('form-nuevo-compromiso')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!appState.selectedCasoId) return;

    const desc = document.getElementById('input-compromiso-desc').value.trim();
    const resp = document.getElementById('input-compromiso-resp').value.trim();
    const fecha = document.getElementById('input-compromiso-fecha').value;

    try {
      const res = await fetch(`/api/casos/${appState.selectedCasoId}/compromisos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          descripcion: desc,
          responsable: resp,
          fecha_limite: new Date(fecha).toISOString()
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al crear compromiso');
      }

      showToast('Compromiso registrado');
      closeModal('modal-nuevo-compromiso');
      document.getElementById('form-nuevo-compromiso').reset();

      await openCasoDrawer(appState.selectedCasoId);
      await loadCasos();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Submit: Nuevo Aprendiz
  document.getElementById('form-nuevo-aprendiz')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const tdoc = document.getElementById('ap-tipo-doc').value;
    const ndoc = document.getElementById('ap-num-doc').value.trim();
    const nom = document.getElementById('ap-nombres').value.trim();
    const ape = document.getElementById('ap-apellidos').value.trim();
    const email = document.getElementById('ap-email').value.trim();
    const tel = document.getElementById('ap-telefono').value.trim();
    const ficha = document.getElementById('ap-ficha').value.trim();
    const prog = document.getElementById('ap-programa').value.trim();
    const jor = document.getElementById('ap-jornada').value;

    try {
      const res = await fetch('/api/aprendices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tipo_documento: tdoc,
          numero_documento: ndoc,
          nombres: nom,
          apellidos: ape,
          email: email,
          telefono: tel,
          ficha: ficha,
          programa: prog,
          jornada: jor
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al registrar aprendiz');
      }

      showToast('Aprendiz registrado con éxito');
      closeModal('modal-nuevo-aprendiz');
      document.getElementById('form-nuevo-aprendiz').reset();

      await loadAprendices();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Submit: Transición FSM
  document.getElementById('form-transicion-fsm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!appState.selectedCasoId) return;

    const nuevoEstado = document.getElementById('transicion-nuevo-estado').value;
    const justificacion = document.getElementById('input-fsm-justificacion').value.trim();
    const tipoCierre = document.getElementById('select-fsm-tipo-cierre')?.value;
    const asignadoA = document.getElementById('select-fsm-asignar')?.value;

    try {
      const res = await fetch(`/api/casos/${appState.selectedCasoId}/transicion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nuevo_estado: nuevoEstado,
          justificacion: justificacion,
          usuario_nombre: 'Juan David Berroterán',
          tipo_cierre: nuevoEstado === 'CERRADO' ? tipoCierre : null,
          asignado_a_id: asignadoA ? parseInt(asignadoA) : null
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error en transición de estado');
      }

      showToast(`Estado actualizado con éxito a: ${nuevoEstado}`);
      closeModal('modal-transicion-fsm');
      document.getElementById('form-transicion-fsm').reset();

      // Refresh drawer & background tables
      await openCasoDrawer(appState.selectedCasoId);
      await loadCasos();
      await loadStats();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

function openTransicionModal(nuevoEstado, estadoActual) {
  document.getElementById('transicion-nuevo-estado').value = nuevoEstado;
  document.getElementById('modal-fsm-title').textContent = `Transición: ${estadoActual} → ${nuevoEstado}`;
  document.getElementById('modal-fsm-desc').textContent = `Confirme la justificación para avanzar el expediente hacia el estado ${nuevoEstado}.`;

  const groupCierre = document.getElementById('group-fsm-tipo-cierre');
  const groupAsignar = document.getElementById('group-fsm-asignar');

  if (groupCierre) groupCierre.style.display = (nuevoEstado === 'CERRADO') ? 'block' : 'none';
  if (groupAsignar) groupAsignar.style.display = (nuevoEstado === 'ASIGNADO') ? 'block' : 'none';

  openModal('modal-transicion-fsm');
}

function openModal(modalId) {
  document.getElementById(modalId)?.classList.add('active');
}

function closeModal(modalId) {
  document.getElementById(modalId)?.classList.remove('active');
}

function iniciarCasoParaAprendiz(aprendizId) {
  document.getElementById('select-caso-aprendiz').value = aprendizId;
  openModal('modal-nuevo-caso');
}

// Toast Alert Utility
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'error' : ''}`;
  
  const iconSvg = type === 'error'
    ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
    : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';

  toast.innerHTML = `${iconSvg} <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
