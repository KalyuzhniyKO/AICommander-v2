const api = '';
let currentTask = null;
let currentRound = null;

const el = (id) => document.getElementById(id);
const roles = ['manager', 'architect', 'designer', 'coder', 'reviewer'];

function setStatus(text, type = 'info') {
  const node = el('status');
  node.textContent = text;
  node.className = `status ${type}`;
}

function escapeHtml(text = '') {
  return String(text).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

async function request(path, options = {}) {
  let data = {};
  const res = await fetch(api + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  try { data = await res.json(); } catch (_) { data = {}; }
  if (!res.ok) throw new Error(data.detail || data.error || JSON.stringify(data));
  return data;
}

function statusPill(status) {
  const normalized = String(status || 'unknown').replace(/[^a-z0-9_-]/gi, '_');
  return `<span class="pill ${normalized}">${escapeHtml(status || 'unknown')}</span>`;
}

async function loadTask() {
  if (!currentTask) return;
  currentTask = await request(`/tasks/${currentTask.id}`);
  currentRound = currentTask.rounds[currentTask.rounds.length - 1] || null;
  renderTask();
}

function renderTask() {
  el('currentRoundMeta').textContent = currentRound
    ? `Текущий круг #${currentRound.round_number}, id=${currentRound.id}. Premium Review: ${currentRound.premium_review_status}.`
    : 'Круг ещё не запущен.';

  const rounds = el('rounds');
  rounds.innerHTML = '';
  if (!currentTask || !currentTask.rounds.length) {
    rounds.className = 'rounds empty';
    rounds.textContent = 'Пока нет кругов. Создайте задачу и запустите первый круг.';
    renderPremium();
    return;
  }
  rounds.className = 'rounds';

  currentTask.rounds.forEach((round) => {
    const box = document.createElement('article');
    box.className = 'round-card';
    const rolesLine = (round.selected_roles || []).join(', ') || '—';
    box.innerHTML = `
      <div class="round-head">
        <div>
          <h3>Круг ${round.round_number}</h3>
          <p class="meta">Роли: ${escapeHtml(rolesLine)} • Комментарий: ${escapeHtml(round.user_comment || '—')}</p>
        </div>
        <div>${statusPill(round.premium_review_status)}</div>
      </div>
      ${round.summary ? `<details><summary>Summary текущего круга</summary><pre>${escapeHtml(round.summary)}</pre></details>` : ''}
    `;

    roles.forEach((roleName) => {
      const out = (round.role_outputs || []).find((item) => item.role === roleName);
      if (!out) return;
      const role = document.createElement('div');
      role.className = `role ${out.status === 'completed' ? 'ok' : 'failed'}`;
      const errors = (out.model_errors || []).map((e) => `${e.provider}/${e.model_id}: ${e.error}`).join('\n');
      role.innerHTML = `
        <div class="role-head">
          <h4>${escapeHtml(out.role)}</h4>
          ${statusPill(out.status)}
        </div>
        <p class="meta">Модель: <strong>${escapeHtml(out.provider || '—')}/${escapeHtml(out.model_id || '—')}</strong> • response_time_ms: ${out.response_time_ms || '—'}</p>
        <pre>${escapeHtml(out.output || '')}</pre>
        ${errors ? `<details open><summary>Ошибки моделей / fallback</summary><pre class="error">${escapeHtml(errors)}</pre></details>` : ''}
      `;
      box.appendChild(role);
    });

    if (round.premium_review_output) {
      const premium = document.createElement('div');
      premium.className = 'premium-inline';
      premium.innerHTML = `<h4>Premium Review: ${statusPill(round.premium_review_status)}</h4><p class="meta">Model: ${escapeHtml(round.premium_review_model || '—')}</p><pre>${escapeHtml(round.premium_review_output)}</pre>`;
      box.appendChild(premium);
    }
    rounds.appendChild(box);
  });
  renderPremium();
}

function renderPremium() {
  const p = el('premium');
  if (!currentRound) { p.textContent = 'No round yet.'; return; }
  p.innerHTML = `
    <p class="meta">Status: ${statusPill(currentRound.premium_review_status)} • Model: ${escapeHtml(currentRound.premium_review_model || '—')}</p>
    <pre>${escapeHtml(currentRound.premium_review_output || 'Premium Review ещё не запускался или был пропущен.')}</pre>
  `;
}

async function loadModels() {
  const data = await request('/models/status');
  const configNote = data.config_file_exists ? '' : '<div class="notice warning">config/models.json не найден: используется example для отображения. Для проверки моделей скопируйте config/models.example.json в config/models.json.</div>';
  const rows = (data.models || []).map((m) => `
    <tr>
      <td>${escapeHtml(m.role)}</td>
      <td>${escapeHtml(m.provider)}</td>
      <td><code>${escapeHtml(m.model_id)}</code></td>
      <td>${statusPill(m.status)}</td>
      <td class="error-cell">${escapeHtml(m.last_error || '')}</td>
      <td>${escapeHtml(m.last_success_at || '')}</td>
      <td>${escapeHtml(m.last_failure_at || '')}</td>
      <td>${m.response_time_ms || ''}</td>
    </tr>
  `).join('');
  el('models').innerHTML = `${configNote}<div class="table-wrap"><table><thead><tr><th>Role</th><th>Provider</th><th>model_id</th><th>Status</th><th>last_error</th><th>last_success_at</th><th>last_failure_at</th><th>response_time_ms</th></tr></thead><tbody>${rows || '<tr><td colspan="8">Нет данных о моделях.</td></tr>'}</tbody></table></div>`;
}

async function checkModels() {
  const box = el('modelCheckResult');
  box.className = 'notice';
  box.textContent = 'Проверяем модели...';
  const data = await request('/models/check', { method: 'POST' });
  const failed = (data.results || []).filter((item) => item.status !== 'available').length;
  box.className = `notice ${data.ok ? 'success' : 'warning'}`;
  box.innerHTML = `<strong>${escapeHtml(data.status || 'completed')}</strong>${data.error ? ` — ${escapeHtml(data.error)}` : ''}<br>Проверено: ${(data.results || []).length}, ошибок: ${failed}`;
  await loadModels();
}

el('runTeam').onclick = async () => {
  try {
    const description = el('taskText').value.trim();
    if (!description) return setStatus('Введите описание задачи.', 'warning');
    setStatus('Создаём задачу и запускаем первый круг...', 'info');
    currentTask = await request('/tasks', { method: 'POST', body: JSON.stringify({ description }) });
    currentRound = await request(`/tasks/${currentTask.id}/rounds`, { method: 'POST', body: JSON.stringify({ user_comment: '' }) });
    await loadTask();
    await loadModels();
    setStatus('Круг завершён. Проверьте ответы ролей и добавьте комментарий для следующего круга.', 'success');
  } catch (e) { setStatus(e.message, 'error'); }
};

el('runNext').onclick = async () => {
  if (!currentTask) return setStatus('Сначала создайте задачу.', 'warning');
  try {
    setStatus('Запускаем следующий круг...', 'info');
    currentRound = await request(`/tasks/${currentTask.id}/rounds`, { method: 'POST', body: JSON.stringify({ user_comment: el('commentText').value }) });
    el('commentText').value = '';
    await loadTask();
    await loadModels();
    setStatus('Следующий круг завершён.', 'success');
  } catch (e) { setStatus(e.message, 'error'); }
};

el('rerunRole').onclick = async () => {
  if (!currentRound) return setStatus('Сначала запустите круг.', 'warning');
  try {
    setStatus('Перезапускаем роль...', 'info');
    currentRound = await request(`/rounds/${currentRound.id}/roles/${el('roleSelect').value}/rerun`, { method: 'POST' });
    await loadTask();
    await loadModels();
    setStatus('Роль перезапущена.', 'success');
  } catch (e) { setStatus(e.message, 'error'); }
};

el('premiumReview').onclick = async () => {
  if (!currentRound) return setStatus('Сначала запустите круг.', 'warning');
  try {
    setStatus('Запускаем Premium Review или сохраняем причину пропуска...', 'info');
    currentRound = await request(`/rounds/${currentRound.id}/premium-review`, { method: 'POST' });
    await loadTask();
    await loadModels();
    setStatus(`Premium Review: ${currentRound.premium_review_status}.`, 'success');
  } catch (e) { setStatus(e.message, 'error'); }
};

el('refreshModels').onclick = () => loadModels().catch((e) => setStatus(e.message, 'error'));
el('checkModels').onclick = () => checkModels().catch((e) => setStatus(e.message, 'error'));

loadModels().catch(() => {});
