const api = '';
let currentTask = null;
let currentRound = null;

const el = (id) => document.getElementById(id);
function setStatus(text) { el('status').textContent = text; }
async function request(path, options = {}) {
  const res = await fetch(api + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}
async function loadTask() {
  if (!currentTask) return;
  currentTask = await request(`/tasks/${currentTask.id}`);
  currentRound = currentTask.rounds[currentTask.rounds.length - 1] || null;
  renderTask();
}
function renderTask() {
  const rounds = el('rounds');
  rounds.innerHTML = '';
  if (!currentTask) return;
  currentTask.rounds.forEach((round) => {
    const box = document.createElement('div');
    box.className = 'card';
    box.innerHTML = `<h3>Round ${round.round_number}</h3><p class="meta">Selected roles: ${round.selected_roles.join(', ')} | User comment: ${round.user_comment || '—'}</p>`;
    round.role_outputs.forEach((out) => {
      const role = document.createElement('div');
      role.className = 'role';
      const errors = (out.model_errors || []).map((e) => `${e.provider}/${e.model_id}: ${e.error}`).join('\n');
      role.innerHTML = `<h4>${out.role}</h4><p class="meta">Status: ${out.status} | Model: ${out.provider || '—'}/${out.model_id || '—'} | Time: ${out.response_time_ms || '—'} ms</p><pre>${escapeHtml(out.output || '')}</pre>${errors ? `<h5>Model/API errors</h5><pre class="error">${escapeHtml(errors)}</pre>` : ''}`;
      box.appendChild(role);
    });
    rounds.appendChild(box);
  });
  renderPremium();
}
function renderPremium() {
  const p = el('premium');
  if (!currentRound) { p.textContent = 'No round yet.'; return; }
  p.innerHTML = `<p class="meta">Status: ${currentRound.premium_review_status} | Model: ${currentRound.premium_review_model || '—'}</p><pre>${escapeHtml(currentRound.premium_review_output || '')}</pre>`;
}
function escapeHtml(text) { return text.replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

el('runTeam').onclick = async () => {
  try {
    setStatus('Creating task and running one round...');
    currentTask = await request('/tasks', { method: 'POST', body: JSON.stringify({ description: el('taskText').value }) });
    currentRound = await request(`/tasks/${currentTask.id}/rounds`, { method: 'POST', body: JSON.stringify({ user_comment: '' }) });
    await loadTask();
    await loadModels();
    setStatus('Round finished. Add a comment before the next round.');
  } catch (e) { setStatus(e.message); }
};
el('runNext').onclick = async () => {
  if (!currentTask) return setStatus('Create a task first.');
  try {
    setStatus('Running next human-approved round...');
    currentRound = await request(`/tasks/${currentTask.id}/rounds`, { method: 'POST', body: JSON.stringify({ user_comment: el('commentText').value }) });
    await loadTask(); await loadModels(); setStatus('Next round finished.');
  } catch (e) { setStatus(e.message); }
};
el('rerunRole').onclick = async () => {
  if (!currentRound) return setStatus('Run a round first.');
  try {
    setStatus('Rerunning role...');
    currentRound = await request(`/rounds/${currentRound.id}/roles/${el('roleSelect').value}/rerun`, { method: 'POST' });
    await loadTask(); await loadModels(); setStatus('Role rerun finished.');
  } catch (e) { setStatus(e.message); }
};
el('premiumReview').onclick = async () => {
  if (!currentRound) return setStatus('Run a round first.');
  try {
    setStatus('Running Premium Review if enabled/configured...');
    currentRound = await request(`/rounds/${currentRound.id}/premium-review`, { method: 'POST' });
    await loadTask(); await loadModels(); setStatus('Premium Review request finished.');
  } catch (e) { setStatus(e.message); }
};
async function loadModels() {
  const data = await request('/models/status');
  el('models').innerHTML = `<table><thead><tr><th>Role</th><th>Provider/model</th><th>Status</th><th>Last error</th><th>Last success</th><th>Last failure</th><th>ms</th></tr></thead><tbody>${data.models.map((m) => `<tr><td>${m.role}</td><td>${m.provider}/${m.model_id}</td><td>${m.status}</td><td>${escapeHtml(m.last_error || '')}</td><td>${m.last_success_at || ''}</td><td>${m.last_failure_at || ''}</td><td>${m.response_time_ms || ''}</td></tr>`).join('')}</tbody></table>`;
}
el('refreshModels').onclick = loadModels;
loadModels().catch(() => {});
