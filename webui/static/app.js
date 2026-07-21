let state = {};
let currentView = 'gameSelect';
let settingsGame = 'ets2';

const $ = (sel) => document.querySelector(sel);
const t = (key, fallback) => (state.translations && state.translations[key]) || fallback || key;

const api = async (url, data) => {
  const opts = data === undefined ? {} : { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) };
  const res = await fetch(url, opts);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Error');
  return json;
};

function escapeHtml(value='') {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}

function jsString(value='') {
  return JSON.stringify(String(value));
}

function activate(view) {
  currentView = view;
  const setupView = view === 'gameSelect' || view === 'profileSelect';
  document.querySelector('.app-shell').classList.toggle('setup-flow', setupView);
  document.querySelectorAll('.nav').forEach(btn => btn.classList.toggle('active', btn.dataset.view === view));
  document.querySelectorAll('.view').forEach(el => el.classList.toggle('active', el.id === view));
  render();
}

async function refreshState() {
  state = await api('/api/state');
  document.documentElement.lang = state.lang || 'es';
  $('#appTitle').textContent = state.app || 'Truck Manager';
  const versionBadge = $('#appVersion');
  if (versionBadge) versionBadge.textContent = `v${state.version || '4.0.0'}`;
  const lang = $('#langSelect');
  if (lang && state.lang && lang.value !== state.lang) lang.value = state.lang;
  $('#changeGameBtn').textContent = t('change_game', 'Change game');
  $('#themeBtn').textContent = document.body.classList.contains('dark') ? t('light', 'Claro') : t('dark', 'Oscuro');
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n, el.textContent); });
  const usersLabel = t('online_users', 'Usuarios: {count}');
  $('#onlineBadge').textContent = usersLabel.replace('{count}', state.online_count == null ? '--' : state.online_count);
}

function header(title, subtitle='') { return `<h1 class="page-title">${title}</h1>${subtitle ? `<p class="subtitle">${subtitle}</p>` : ''}`; }

function notify(message, type='success') {
  const host = $('#toastHost');
  if (!host) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<div class="toast-mark"></div><div class="toast-body"><strong>${type === 'error' ? t('error', 'Error') : t('success', 'Success')}</strong><span>${message}</span></div><button class="toast-close" aria-label="${t('close', 'Close')}">&times;</button>`;
  host.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  const close = () => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 220);
  };
  toast.querySelector('.toast-close').onclick = close;
  setTimeout(close, 3600);
}

function showDialog({title, message, code, confirmText, cancelText, danger=false}) {
  const dialog = $('#notifyDialog');
  const content = $('#notifyDialogContent');
  return new Promise(resolve => {
    content.innerHTML = `<div class="dialog-card">
      <div class="editor-head"><h2>${title}</h2><button class="icon-close" data-result="false" aria-label="${t('close', 'Close')}">&times;</button></div>
      <p class="dialog-message">${message || ''}</p>
      ${code ? `<button class="dialog-code" data-copy="${code}">${code}</button>` : ''}
      <div class="actions dialog-actions">
        ${cancelText ? `<button class="ghost" data-result="false">${cancelText}</button>` : ''}
        <button class="${danger ? 'danger' : 'primary'}" data-result="true">${confirmText || t('ok', 'OK')}</button>
      </div>
    </div>`;
    const finish = value => { dialog.close(); resolve(value); };
    content.querySelectorAll('[data-result]').forEach(btn => btn.onclick = () => finish(btn.dataset.result === 'true'));
    const copy = content.querySelector('[data-copy]');
    if (copy) copy.onclick = async () => { await copyText(copy.dataset.copy); notify(t('code_copied', 'Code copied to clipboard.')); };
    dialog.oncancel = event => { event.preventDefault(); finish(false); };
    dialog.showModal();
  });
}

function showInfo(title, message, code=null) {
  return showDialog({title, message, code, confirmText: t('ok', 'OK')});
}

function showConfirm(title, message) {
  return showDialog({title, message, confirmText: t('delete', 'Delete'), cancelText: t('cancel', 'Cancelar'), danger: true});
}

function showInputDialog({title, message, value='', confirmText, cancelText}) {
  const dialog = $('#notifyDialog');
  const content = $('#notifyDialogContent');
  return new Promise(resolve => {
    content.innerHTML = `<div class="dialog-card">
      <div class="editor-head"><h2>${escapeHtml(title)}</h2><button class="icon-close" data-result="cancel" aria-label="${t('close', 'Close')}">&times;</button></div>
      <p class="dialog-message">${escapeHtml(message || '')}</p>
      <input id="dialogInput" class="dialog-input" value="${escapeHtml(value)}" autocomplete="off">
      <div class="actions dialog-actions">
        <button class="ghost" data-result="cancel">${cancelText || t('cancel', 'Cancelar')}</button>
        <button class="primary" data-result="ok">${confirmText || t('save', 'Guardar')}</button>
      </div>
    </div>`;
    const input = content.querySelector('#dialogInput');
    const finish = result => {
      const text = result === 'ok' ? input.value.trim() : null;
      dialog.close();
      resolve(text);
    };
    content.querySelectorAll('[data-result]').forEach(btn => btn.onclick = () => finish(btn.dataset.result));
    input.addEventListener('keydown', event => {
      if (event.key === 'Enter') finish('ok');
      if (event.key === 'Escape') finish('cancel');
    });
    dialog.oncancel = event => { event.preventDefault(); finish('cancel'); };
    dialog.showModal();
    setTimeout(() => input.focus(), 20);
  });
}

function showModPreview(mod) {
  const dialog = $('#notifyDialog');
  const content = $('#notifyDialogContent');
  const id = mod?.id || '';
  const name = mod?.name || t('mod_preview', 'Vista previa');
  content.innerHTML = `<div class="dialog-card preview-card">
    <div class="editor-head">
      <h2>${escapeHtml(name)}</h2>
      <button class="icon-close" aria-label="${t('close', 'Close')}">&times;</button>
    </div>
    <div class="preview-frame">
      <img class="preview-image" alt="${escapeHtml(name)}" src="/api/mod-thumb?id=${encodeURIComponent(id)}">
      <div class="preview-fallback">${escapeHtml(t('mod_preview_unavailable', 'Preview is not available.'))}</div>
    </div>
  </div>`;
  const close = () => dialog.close();
  const img = content.querySelector('.preview-image');
  const fallback = content.querySelector('.preview-fallback');
  const closeBtn = content.querySelector('.icon-close');
  if (closeBtn) closeBtn.onclick = close;
  if (img) {
    img.onload = () => {
      img.classList.remove('is-hidden');
      if (fallback) fallback.classList.remove('is-visible');
    };
    img.onerror = () => {
      img.classList.add('is-hidden');
      if (fallback) fallback.classList.add('is-visible');
    };
  }
  dialog.oncancel = event => { event.preventDefault(); close(); };
  dialog.showModal();
}

async function copyText(value) {
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch (_) {
    return false;
  }
}


function renderGameSelect() {
  const games = Object.entries(state.games || {});
  $('#gameSelect').innerHTML = `
    <div class="setup-card">
      <div class="setup-logo">TM</div>
      ${header(t('choose_game', 'Elige el juego'), t('select_game_subtitle', 'Selecciona el juego que quieres gestionar'))}
      <div class="game-grid">
        ${games.map(([key,g]) => `<button class="game-choice" onclick="selectGame('${key}')"><strong>${g.short}</strong><span>${g.name}</span></button>`).join('')}
      </div>
    </div>`;
}

async function renderProfileSelect() {
  const data = await api('/api/profiles');
  const gameName = state.games?.[state.game]?.name || '';
  $('#profileSelect').innerHTML = `
    <div class="setup-card wide">
      ${header(t('choose_profile', 'Choose profile'), gameName)}
      <div class="actions"><button class="ghost" onclick="activate('gameSelect')">${t('change_game', 'Change game')}</button><button class="ghost" onclick="openSetupSettings()">${t('settings', 'Settings')}</button><button class="primary" onclick="renderProfileSelect()">${t('refresh', 'Refresh')}</button></div>
      <div class="panel profile-list">${data.profiles.map(p => `<div class="row"><div><strong>${p.display_name}</strong><div class="source">${p.hex_id}${p.level ? ' - ' + t('level', 'Level') + ' ' + p.level : ''}</div></div><button class="primary" onclick="selectProfile('${p.hex_id}')">${t('select', 'Select')}</button></div>`).join('') || `<p>${t('no_profiles_found', 'No profiles found')}</p>`}</div>
    </div>`;
}


function renderDashboard() {
  const profileName = state.profile_driver_name || state.profile_display_name || state.profile_id || t('unselected', 'Not selected');
  $('#dashboard').innerHTML = header(t('dashboard', 'Dashboard')) + `
    <div class="grid">
      <div class="card"><h3>${t('game', 'Game')}</h3><p>${state.games?.[state.game]?.name || ''}</p></div>
      <div class="card"><div class="value">${state.profile_id ? '1' : '0'}</div><h3>${t('profile', 'Profile')}</h3><p>${escapeHtml(profileName)}</p></div>
      <div class="card"><div class="value" id="modCount">--</div><h3>${t('mods', 'Mods')}</h3><p>${t('installed_workshop', 'Installed and Workshop')}</p></div>
      <div class="card"><div class="value">${state.scanning ? '...' : 'OK'}</div><h3>${t('status', 'Status')}</h3><p>${state.scan_message || t('ready', 'Ready')}</p></div>
    </div>`;
  api('/api/mods').then(data => $('#modCount').textContent = data.mods.length).catch(()=>{});
}
async function renderProfiles() {
  const data = await api('/api/profiles');
  $('#profiles').innerHTML = header(t('profiles', 'Profiles'), t('select_profile', 'Select a profile to scan and edit.')) + `
    <div class="actions"><button class="primary" onclick="loadProfiles()">${t('refresh', 'Refresh')}</button></div>
    <div class="panel profile-list">${data.profiles.map(p => `<div class="profile-row"><div><strong>${p.display_name}</strong><div class="source">${p.hex_id}${p.level ? ' - ' + t('level', 'Level') + ' ' + p.level : ''}</div></div><div class="row-actions"><button class="ghost" onclick="editProfile('${p.hex_id}')">${t('edit_profile', 'Edit profile')}</button><button class="primary" onclick="selectProfile('${p.hex_id}')">${t('select', 'Select')}</button></div></div>`).join('') || `<p>${t('no_profiles_found', 'No profiles found')}</p>`}</div>`;
}

function loadProfiles(){ activate('profiles'); }
async function selectGame(game){ await api('/api/game', {game}); await refreshState(); activate('profileSelect'); }
async function selectProfile(hex){
  const result = await api('/api/profile', {hex_id: hex});
  await refreshState();
  await handleProfileHealth(result.health);
  await api('/api/scan', {});
  await refreshState();
  activate('dashboard');
  pollScan();
}

async function handleProfileHealth(health) {
  if (!health || !health.needs_repair) return;
  const issues = (health.issues || []).map(issue => `- ${issue.message}`).join('\n');
  if (!health.can_repair) {
    await showInfo('Perfil necesita revision', escapeHtml(`He encontrado detalles que conviene revisar manualmente:\n\n${issues}`));
    return;
  }
  const repair = await showDialog({
    title: t('repair_profile_recommended', 'Repair profile (strongly recommended)'),
    message: escapeHtml(`He encontrado detalles en el perfil que pueden afectar al orden de carga o a la lectura del profile.sii. Antes de reparar se creara una copia de seguridad.\n\n${issues}`).replace(/\n/g, '<br>'),
    confirmText: t('repair_profile', 'Repair profile'),
    cancelText: t('continue_without_repair', 'Continue without repairing'),
    danger: false
  });
  if (!repair) return;
  try {
    const result = await api('/api/repair-profile', {});
    const backup = result.health?.backup_path ? `\nBackup: ${result.health.backup_path}` : '';
    notify(`Perfil reparado correctamente.${backup}`);
    if (result.health?.needs_repair) {
      const remaining = (result.health.issues || []).map(issue => `- ${issue.message}`).join('\n');
      await showInfo('Revision pendiente', escapeHtml(`Se reparo lo automatico, pero queda algo para revisar:\n\n${remaining}`).replace(/\n/g, '<br>'));
    }
  } catch (e) {
    notify(e.message, 'error');
  }
}
async function editProfile(hex){ await api('/api/profile', {hex_id: hex}); await refreshState(); await openProfileEditor(); }
async function pollScan(){ await refreshState(); if(currentView==='order') renderOrder(); if(currentView==='dashboard') renderDashboard(); if (state.scanning) setTimeout(pollScan, 1200); }

async function renderOrder() {
  const data = await api('/api/mods');
  const inactive = data.mods.filter(m => !m.active);
  const byId = new Map(data.mods.map(m => [m.id, m]));
  const active = [...data.active].reverse()
    .map(item => byId.get(String(item).split('|')[0].trim()))
    .filter(Boolean);
  $('#order').innerHTML = header(t('order', 'Orden'), state.scanning ? state.scan_message : '') + `
    <div class="actions">
      <button class="primary" onclick="saveOrder()">${t('save_order_game', 'Guardar en el juego')}</button>
    </div>
    <div class="columns order-columns">
      <div class="panel drop-panel" data-list="inactive">
        <h3 id="inactiveModsTitle">${t('available_mods', 'Mods disponibles')} (${inactive.length})</h3>
        <div id="inactiveMods" class="drop-zone" data-zone="inactive">${inactive.map(m => dragModRow(m, false)).join('') || `<p class="empty-drop">${t('no_inactive_mods', 'No hay mods inactivos.')}</p>`}</div>
      </div>
      <div class="panel drop-panel" data-list="active">
        <h3 id="activeModsTitle">${t('load_order_plain', 'Orden de carga')} (${active.length})</h3>
        <div id="activeMods" class="drop-zone active-zone" data-zone="active">${active.map(m => dragModRow(m, true)).join('') || `<p class="empty-drop">${t('no_active_mods_yet', 'No active mods yet.')}</p>`}</div>
      </div>
    </div>`;
  bindOrderDrag();
  updateOrderCounts();
}

function dragModRow(m, active){
  const previewUnavailable = !m.preview_available;
  return `<div class="mod-row drag-mod ${active ? 'active-mod' : ''}" draggable="true" data-id="${m.id}">
    <div class="drag-handle" aria-hidden="true">&#8801;</div>
    <div class="mod-main"><strong>${m.name}</strong><div class="source">${m.source}</div></div>
    <div class="mod-preview-pop" onmousedown="event.stopPropagation()" onclick="event.stopPropagation()">
      <button class="icon-btn mod-preview-btn" type="button" title="${t('mod_preview', 'Vista previa')}" aria-label="${t('mod_preview', 'Vista previa')}">⌁</button>
      <div class="mod-preview-cloud ${previewUnavailable ? 'no-image' : ''}" role="tooltip">
        <div class="mod-preview-tail" aria-hidden="true">
          <span class="tail-dot tail-dot-lg"></span>
          <span class="tail-dot tail-dot-md"></span>
          <span class="tail-dot tail-dot-sm"></span>
        </div>
        <img class="mod-preview-thumb ${previewUnavailable ? 'is-hidden' : ''}" alt="${escapeHtml(m.name)}" src="${previewUnavailable ? '' : `/api/mod-thumb?id=${encodeURIComponent(m.id)}`}" onerror="this.classList.add('is-hidden'); this.parentElement.classList.add('no-image')">
        <div class="mod-preview-empty">${escapeHtml(t('mod_preview_unavailable', 'Preview is not available.'))}</div>
      </div>
    </div>
  </div>`;
}

function bindOrderDrag(){
  let dragged = null;
  document.querySelectorAll('.drag-mod').forEach(card => {
    card.addEventListener('dragstart', event => {
      dragged = card;
      card.classList.add('dragging');
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', card.dataset.id);
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      dragged = null;
      syncOrderFromDom();
    });
  });
  document.querySelectorAll('.drop-zone').forEach(zone => {
    zone.addEventListener('dragover', event => {
      event.preventDefault();
      zone.classList.add('drag-over');
      const after = getDragAfterElement(zone, event.clientY);
      if (!dragged) return;
      const empty = zone.querySelector('.empty-drop');
      if (empty) empty.remove();
      if (after == null) zone.appendChild(dragged);
      else zone.insertBefore(dragged, after);
      updateOrderVisualState();
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', event => {
      event.preventDefault();
      zone.classList.remove('drag-over');
      updateOrderVisualState();
      syncOrderFromDom();
    });
  });
}

function updateOrderVisualState(){
  document.querySelectorAll('#activeMods .drag-mod').forEach(card => card.classList.add('active-mod'));
  document.querySelectorAll('#inactiveMods .drag-mod').forEach(card => card.classList.remove('active-mod'));
}

function updateOrderCounts(){
  const inactiveCount = document.querySelectorAll('#inactiveMods .drag-mod').length;
  const activeCount = document.querySelectorAll('#activeMods .drag-mod').length;
  const inactiveTitle = $('#inactiveModsTitle');
  const activeTitle = $('#activeModsTitle');
  if (inactiveTitle) inactiveTitle.textContent = `${t('available_mods', 'Mods disponibles')} (${inactiveCount})`;
  if (activeTitle) activeTitle.textContent = `${t('load_order_plain', 'Orden de carga')} (${activeCount})`;
}

function getDragAfterElement(container, y){
  const cards = [...container.querySelectorAll('.drag-mod:not(.dragging)')];
  return cards.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) return {offset, element: child};
    return closest;
  }, {offset: Number.NEGATIVE_INFINITY}).element;
}

async function syncOrderFromDom(){
  const ids = [...document.querySelectorAll('#activeMods .drag-mod')].map(el => el.dataset.id);
  updateOrderVisualState();
  updateOrderCounts();
  document.querySelectorAll('.drop-zone').forEach(zone => zone.classList.remove('drag-over'));
  await api('/api/order', {ids});
}

async function saveOrder(){ await syncOrderFromDom(); await api('/api/save-order', {}); notify(t('saved', 'Guardado.')); }


async function renderPresets() {
  $('#presets').innerHTML = header(t('presets', 'Presets'), t('presets_description', 'Share your current load order or import a code from another player.')) + `
    <div class="preset-layout">
      <div class="panel">
        <h3>${t('save_preset_title', 'Guardar preset')}</h3>
        <label>${t('preset_name', 'Nombre del preset')}</label>
        <input id="presetName" value="${state.profile_id || 'Preset'}">
        <button class="primary full" onclick="sharePreset()">${t('share_preset', 'Guardar preset')}</button>
        <div id="sharedCode" class="code-box muted-box"></div>
      </div>
      <div class="panel">
        <h3>${t('import_preset', 'Importar preset')}</h3>
        <label>${t('enter_code', 'Preset code')}</label>
        <input id="presetCode" placeholder="ABCDE-FGHIJ-KLMNO-PQRST-UVWXY">
        <button class="primary full" onclick="importPreset()">${t('import_code', 'Import code')}</button>
      </div>
    </div>
    <div class="panel presets-panel">
      <div class="panel-head"><h3>${t('my_presets', 'Mis presets')}</h3><button class="ghost" onclick="loadMyPresets()">${t('refresh', 'Refresh')}</button></div>
      <div id="myPresetsList" class="preset-list"><p>${t('loading', 'Loading...')}</p></div>
    </div>`;
  loadMyPresets();
}

async function loadMyPresets() {
  const list = $('#myPresetsList');
  if (!list) return;
  list.innerHTML = `<p>${t('loading', 'Loading...')}</p>`;
  try {
    const data = await api('/api/presets');
    const presets = data.presets || [];
    list.innerHTML = presets.map(presetCard).join('') || `<p>${t('no_presets_yet', 'You have not shared any presets yet.')}</p>`;
  } catch (e) {
    list.innerHTML = `<p class="error-text">${e.message}</p>`;
  }
}

function presetCard(p) {
  const name = p.preset_name || p.profile_name || t('unnamed_preset', 'Preset sin nombre');
  const code = p.code || '';
  const count = (p.mods || []).length;
  return `<div class="preset-card">
    <div><strong>${escapeHtml(name)}</strong><div class="source">${escapeHtml(code)} - ${count} ${t('mods', 'Mods')}</div></div>
    <div class="row-actions">
      <button class="ghost" onclick='renamePreset(${jsString(code)}, ${jsString(name)})'>${t('rename_preset', 'Cambiar nombre')}</button>
      <button class="ghost" onclick='copyPresetCode(${jsString(code)})'>${t('copy_code', 'Copy code')}</button>
      <button class="primary" onclick='importPresetCode(${jsString(code)})'>${t('import_code', 'Import code')}</button>
      <button class="danger" onclick='deletePreset(${jsString(code)})'>${t('delete', 'Delete')}</button>
    </div>
  </div>`;
}
async function sharePreset() {
  const name = ($('#presetName')?.value || '').trim();
  try {
    const data = await api('/api/presets/share', {name});
    const box = $('#sharedCode');
    if (box) box.innerHTML = `<strong>${t('your_code_is', 'Your code is:')}</strong><button class="code-pill" onclick="copyPresetCode('${data.code}')">${data.code}</button>`;
    await showInfo(t('preset_shared', 'Preset shared'), t('share_with_friends', 'Share this code with your friends.'), data.code);
    await loadMyPresets();
  } catch (e) { notify(e.message, 'error'); }
}

async function importPreset() {
  const code = ($('#presetCode')?.value || '').trim();
  await importPresetCode(code);
}

async function importPresetCode(code) {
  if (!code) return;
  try {
    await api('/api/presets/import', {code});
    notify(t('preset_imported', 'Preset importado. No olvides guardar en el juego.'));
    if (currentView === 'order') renderOrder();
  } catch (e) { notify(e.message, 'error'); }
}

async function copyPresetCode(code) {
  const copied = await copyText(code);
  if (copied) notify(t('code_copied', 'Code copied to clipboard.'));
  else await showInfo(t('copy_code', 'Copy code'), t('click_to_copy', 'Click the code to copy it:'), code);
}

async function deletePreset(code) {
  const ok = await showConfirm(t('delete', 'Delete'), t('confirm_delete', 'Are you sure you want to delete this preset?'));
  if (!ok) return;
  try {
    await api('/api/presets/delete', {code});
    notify(t('preset_deleted', 'Preset eliminado correctamente.'));
    await loadMyPresets();
  } catch (e) { notify(e.message, 'error'); }
}

async function renamePreset(code, currentName) {
  const name = await showInputDialog({
    title: t('rename_preset', 'Cambiar nombre'),
    message: t('rename_preset_hint', 'Escribe el nuevo nombre del preset.'),
    value: currentName || '',
    confirmText: t('save', 'Guardar'),
    cancelText: t('cancel', 'Cancelar')
  });
  if (name === null) return;
  if (!name) {
    notify(t('preset_name_empty', 'Preset name is empty.'), 'error');
    return;
  }
  try {
    await api('/api/presets/rename', {code, name});
    notify(t('preset_renamed', 'Nombre del preset actualizado.'));
    await loadMyPresets();
  } catch (e) { notify(e.message, 'error'); }
}
async function renderSettings() {
  settingsGame = state.game || settingsGame || 'ets2';
  await renderSettingsInto('#settings', false);
}

async function openSetupSettings() {
  settingsGame = state.game || settingsGame || 'ets2';
  await refreshState();
  const modal = $('#modal');
  $('#modalContent').innerHTML = `<div id="setupSettingsHost"></div>`;
  modal.showModal();
  await renderSettingsInto('#setupSettingsHost', true);
}

async function renderSettingsInto(targetSelector, inModal=false) {
  const game = state.game || settingsGame || 'ets2';
  settingsGame = game;
  const data = await api(`/api/settings?game=${encodeURIComponent(game)}`);
  const s = data.settings;
  const games = state.games || {};
  const localMode = s.local_mod_dirs === null ? 'auto' : 'manual';
  const workshopMode = s.workshop_mod_dirs === null ? 'auto' : 'manual';
  const closeButton = inModal
    ? `<button class="icon-close" onclick="modal.close()" aria-label="${t('close', 'Close')}">&times;</button>`
    : '';
  $(targetSelector).innerHTML = `
    <div class="editor-head">
      <div>${header(t('settings', 'Settings'), t('settings_subtitle', 'Configure automatic or manual detection.'))}</div>
      ${closeButton}
    </div>
    <div class="panel settings-panel">
      <div class="panel-head"><h3>${games[game]?.name || game.toUpperCase()}</h3></div>
      <label>${t('mode', 'Mode')}</label><select id="mode"><option value="auto" ${s.game_dir_mode==='auto'?'selected':''}>${t('automatic', 'Automatic')}</option><option value="manual" ${s.game_dir_mode==='manual'?'selected':''}>${t('manual', 'Manual')}</option></select>
      <p class="subtitle">${t('auto_path', 'Automatic path:')} ${data.auto_dir}</p>
      <div id="manualFields">
        <label>${t('game_directory_homedir', 'Game directory / -homedir')}</label><input id="manual_game_dir" data-auto-dir="${escapeHtml(data.auto_dir)}" placeholder="${escapeHtml(data.auto_dir)}" value="${escapeHtml(s.manual_game_dir || '')}">
        <label>${t('downloaded_mods', 'Downloaded mods')}</label><select id="local_mod_mode"><option value="auto" ${localMode==='auto'?'selected':''}>${t('automatic', 'Automatic')}</option><option value="manual" ${localMode==='manual'?'selected':''}>${t('manual', 'Manual')}</option></select>
        <p class="subtitle">${t('local_mods_auto_hint', 'Automatic uses the mod folder inside the game directory / -homedir.')}</p>
        <input id="local_mod_dirs" value="${escapeHtml((s.local_mod_dirs || []).join(';'))}" placeholder="${escapeHtml((data.current_root || data.auto_dir) + '\\mod')}">
        <label>${t('workshop_mods', 'Workshop')}</label><select id="workshop_mod_mode"><option value="auto" ${workshopMode==='auto'?'selected':''}>${t('automatic', 'Automatic')}</option><option value="manual" ${workshopMode==='manual'?'selected':''}>${t('manual', 'Manual')}</option></select>
        <p class="subtitle">${t('workshop_auto_hint', 'Automatic searches for Workshop mods in Steam libraries.')}</p>
        <input id="workshop_mod_dirs" value="${escapeHtml((s.workshop_mod_dirs || []).join(';'))}" placeholder="Steam\\steamapps\\workshop\\content\\${games[game]?.app_id || ''}">
      </div>
      <div class="actions"><button class="primary" onclick="saveSettings()">${t('save_settings', 'Save settings')}</button><button class="ghost" onclick="resetSettings()">${t('reset', 'Reset')}</button></div>
    </div>`;
  const update = () => {
    const manual = $('#mode').value === 'manual';
    $('#manualFields').style.display = manual ? 'block' : 'none';
    $('#local_mod_dirs').style.display = manual && $('#local_mod_mode').value === 'manual' ? 'block' : 'none';
    $('#workshop_mod_dirs').style.display = manual && $('#workshop_mod_mode').value === 'manual' ? 'block' : 'none';
  };
  $('#mode').addEventListener('change', update);
  $('#local_mod_mode').addEventListener('change', update);
  $('#workshop_mod_mode').addEventListener('change', update);
  update();
}
function selectSettingsGame(game){ settingsGame = game; renderSettingsInto($('#setupSettingsHost') ? '#setupSettingsHost' : '#settings', Boolean($('#setupSettingsHost'))); }
async function saveSettings(){
  const mode = $('#mode').value;
  const manualInput = $('#manual_game_dir');
  const manualDir = mode === 'manual' ? (manualInput.value.trim() || manualInput.dataset.autoDir || '') : '';
  const localMode = $('#local_mod_mode')?.value || 'auto';
  const workshopMode = $('#workshop_mod_mode')?.value || 'auto';
  await api('/api/settings', {
    game: settingsGame || state.game || 'ets2',
    game_dir_mode: mode,
    manual_game_dir: manualDir,
    local_mod_dirs: mode === 'manual' && localMode === 'manual' ? splitPaths($('#local_mod_dirs').value) : null,
    workshop_mod_dirs: mode === 'manual' && workshopMode === 'manual' ? splitPaths($('#workshop_mod_dirs').value) : null
  });
  if (mode === 'manual' && !manualInput.value.trim()) manualInput.value = manualDir;
  notify(t('settings_saved_short', 'Settings saved.'));
}
function splitPaths(v){ return v.split(';').map(x=>x.trim()).filter(Boolean); }
async function resetSettings(){ await api('/api/reset-settings', {game: settingsGame || state.game || 'ets2'}); await renderSettingsInto($('#setupSettingsHost') ? '#setupSettingsHost' : '#settings', Boolean($('#setupSettingsHost'))); }
async function openProfileEditor(){
  const data = await api('/api/profile-editor');
  const p = data.profile, g = data.game;
  const modal = $('#modal');
  $('#modalContent').innerHTML = `<div class="editor-head"><h2>${t('profile_editor', 'Profile editor')}</h2><button class="icon-close" onclick="modal.close()" aria-label="${t('close', 'Close')}">&times;</button></div><div class="tabs" role="tablist"><button class="tab active" data-tab="profileTab" role="tab">${t('editor_profile_section', 'Profile')}</button><button class="tab" data-tab="ecoTab">${t('editor_economy_section', 'Economy')}</button><button class="tab" data-tab="skillsTab" role="tab">${t('skills', 'Skills')}</button><button class="tab" data-tab="companyTab">${t('editor_company_section', 'Company')}</button></div>
  <div id="profileTab" class="tab-panel active">
    <label>${t('profile_name', 'Nombre del perfil')}</label><input id="pe_profile_name" value="${p.profile_name||''}">
    <label>${t('driver', 'Conductor')}</label><input id="pe_driver" value="${p.online_user_name||''}">
    <label>${t('company', 'Empresa')}</label><input id="pe_company" value="${p.company_name||''}">
    ${slider('pe_level',t('experience', 'Experiencia'),p.level||1,1,150)}
  </div>
  <div id="ecoTab" class="tab-panel">
    ${g.save_path ? `<p class="subtitle">${g.save_path}</p>${slider('ge_money',t('money', 'Money'),Number(g.fields.money_account||1),1,1000000000,true)}<label>${t('bank_loan', 'Bank loan')}</label><input id="ge_bank" value="${g.fields.bank_loan||''}"><label>${t('total_distance', 'Total distance')}</label><input id="ge_distance" value="${g.fields.total_distance||''}">` : `<p>${t('game_sii_not_found', 'game.sii was not found.')}</p>`}
  </div>
  <div id="skillsTab" class="tab-panel">
    ${skillSlider('adr',t('skill_adr', 'ADR'),g.fields.adr,0,63)}${skillSlider('long_dist',t('skill_long_dist', 'Long distance'),g.fields.long_dist,0,6)}${skillSlider('heavy',t('skill_heavy', 'Heavy cargo'),g.fields.heavy,0,6)}${skillSlider('fragile',t('skill_fragile', 'Fragile cargo'),g.fields.fragile,0,6)}${skillSlider('urgent',t('skill_urgent', 'Urgent delivery'),g.fields.urgent,0,6)}${skillSlider('mechanical',t('skill_mechanical', 'Eco driving'),g.fields.mechanical,0,6)}
  </div>
  <div id="companyTab" class="tab-panel"><p>${t('garages', 'Garajes')}: ${g.garage_count}</p><p>${t('trucks', 'Camiones')}: ${g.truck_count}</p><p>${t('drivers', 'Conductores')}: ${g.driver_count}</p></div>
  <div class="actions"><button class="primary" onclick="saveProfileEditor()">${t('save_profile', 'Guardar perfil')}</button><button class="ghost" onclick="modal.close()">${t('cancel', 'Cancelar')}</button></div>`;
  document.querySelectorAll('.tab').forEach(btn=>btn.onclick=()=>switchTab(btn.dataset.tab));
  bindSliders(); modal.showModal();
}
function slider(id,label,value,min,max,money=false){ return `<div class="slider-row"><label>${label} (${money?formatMoney(min):min} - ${money?formatMoney(max):max})<input id="${id}" type="range" min="${min}" max="${max}" value="${value}"></label><strong id="${id}_v">${money?formatMoney(value):value}</strong></div>`; }
function skillSlider(id,label,value,min,max){ return slider('sk_'+id,label,Number(value ?? min),min,max); }
function bindSliders(){ document.querySelectorAll('input[type=range]').forEach(r=>{ const out=$('#'+r.id+'_v'); const money=r.id==='ge_money'; const set=()=>out.textContent=money?formatMoney(r.value):r.value; r.oninput=set; set(); }); }
function formatMoney(v){ return Number(v).toLocaleString(state.lang === 'en' ? 'en-US' : 'es-ES'); }
function switchTab(id){ document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active', b.dataset.tab===id)); document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active', p.id===id)); }
async function saveProfileEditor(){ const profile={profile_name:$('#pe_profile_name').value, online_user_name:$('#pe_driver').value, company_name:$('#pe_company').value, cached_experience:(Number($('#pe_level').value)-1)*5000}; const game={money_account:$('#ge_money')?.value, bank_loan:$('#ge_bank')?.value, total_distance:$('#ge_distance')?.value, adr:$('#sk_adr')?.value, long_dist:$('#sk_long_dist')?.value, heavy:$('#sk_heavy')?.value, fragile:$('#sk_fragile')?.value, urgent:$('#sk_urgent')?.value, mechanical:$('#sk_mechanical')?.value}; await api('/api/profile-editor',{profile,game}); $('#modal').close(); notify(t('profile_saved_short', 'Perfil guardado.')); }

function renderAbout(){ $('#about').innerHTML = header(t('about', 'About'), state.app || 'Truck Manager') + `<div class="panel about-panel"><div class="contact-grid"><a class="contact-card" href="mailto:cortex.studios.info@gmail.com"><b>${t('email', 'Email')}</b><span>cortex.studios.info@gmail.com</span></a><a class="contact-card" href="https://discord.gg/UUfsc89HNv" target="_blank" rel="noopener"><b>Discord</b><span>discord.gg/UUfsc89HNv</span></a><a class="contact-card" href="https://github.com/cortexstudiosinfo/ETS2-MOD-MANAGER-UI" target="_blank" rel="noopener"><b>GitHub</b><span>cortexstudiosinfo/ETS2-MOD-MANAGER-UI</span></a></div></div>`; }
async function render(){ await refreshState(); if(currentView==='gameSelect') renderGameSelect(); if(currentView==='profileSelect') await renderProfileSelect(); if(currentView==='dashboard') renderDashboard(); if(currentView==='profiles') renderProfiles(); if(currentView==='order') renderOrder(); if(currentView==='presets') renderPresets(); if(currentView==='settings') renderSettings(); if(currentView==='about') renderAbout(); }

document.querySelectorAll('.nav').forEach(btn => btn.addEventListener('click', () => activate(btn.dataset.view)));
$('#themeBtn').onclick = () => { document.body.classList.toggle('dark'); $('#themeBtn').textContent = document.body.classList.contains('dark') ? t('light', 'Claro') : t('dark', 'Oscuro'); };
$('#langSelect').onchange = async () => { await api('/api/lang', {lang: $('#langSelect').value}); await render(); };
$('#changeGameBtn').onclick = () => activate('gameSelect');
setInterval(refreshState, 3000);
activate('gameSelect');












