let task = null, tasks = [], projects = [], runs = [], run = null, busy = false, pending = null;
const el = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {planned:'Запланирован', running:'Готов к следующему шагу', failed:'Ошибка', blocked:'Заблокирован', awaiting_owner:'Ожидает решения', done:'План согласован', cancelled:'Отменён', pending:'Ожидает', ready:'Готов', completed:'Завершён', analyst:'Аналитик', architect:'Архитектор', developer:'Разработчик', create:'Создание', start:'Запуск', step:'Шаг', block:'Пауза', resume:'Продолжение', fail:'Ошибка', cancel:'Отмена', owner_approve:'Подтверждение', owner_reject:'Отклонение',
  requirements:'Требования', design:'Проект', plan:'План'};
const enLabels = {planned:'Planned', running:'Ready for next step', failed:'Failed', blocked:'Blocked',
 awaiting_owner:'Awaiting owner decision', done:'Mock plan approved', cancelled:'Cancelled',
 pending:'Pending', ready:'Ready', completed:'Completed', analyst:'Analyst', architect:'Architect',
 developer:'Developer', create:'Created', start:'Started', step:'Step', block:'Paused',
 resume:'Resumed', fail:'Failed', cancel:'Cancelled', owner_approve:'Approved', owner_reject:'Rejected',
 requirements:'Requirements', design:'Design', plan:'Plan'};
const label = key => panelLocale.language === 'en' ? (enLabels[key] || labels[key] || key) : (labels[key] || key);
const tr = value => panelLocale.tr(value);
let cachedModels = null;
async function api(path, method = 'GET', payload) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const options = {method, signal:controller.signal, credentials:'same-origin', headers:{'Content-Type':'application/json','X-AICommander-Request':'1'}};
    if (payload !== undefined) options.body = JSON.stringify(payload);
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail;
      const error = new Error(typeof detail === 'string' ? detail : detail?.message || 'Некорректный запрос');
      error.httpStatus = response.status;
      throw error;
    }
    return data;
  } finally { clearTimeout(timeout); }
}
function status(text) { el('status').textContent = tr(text); }
function controls() {
  const locked = busy || Boolean(pending), state = run?.status;
  el('projectSelect').disabled = busy;
  el('runSelect').disabled = busy;
  el('newRun').disabled = locked || !task;
  el('runTask').disabled = locked || !['planned','blocked','failed'].includes(state) || (['blocked','failed'].includes(state) && run.steps_done >= run.max_steps && run.stages.some(s => s.status !== 'completed'));
  el('runTask').textContent = state === 'planned' ? tr('Запустить процесс') : tr('Продолжить / Повторить');
  el('stepTask').disabled = locked || state !== 'running';
  el('pauseTask').disabled = locked || state !== 'running';
  el('stopTask').disabled = locked || !['planned','running','blocked','failed','awaiting_owner'].includes(state);
  el('approveTask').disabled = locked || state !== 'awaiting_owner';
  el('rejectTask').disabled = locked || state !== 'awaiting_owner';
  el('retryRequest').hidden = !pending;
  el('retryRequest').disabled = busy || !pending;
  document.querySelectorAll('button[type="submit"]').forEach(button => button.disabled = locked);
}
async function action(fn) {
  if (busy) return;
  busy = true; controls();
  try { await fn(); status('Сохранено'); }
  catch (error) { status(error.message); }
  finally { busy = false; controls(); }
}
function renderTasks() {
  el('taskList').innerHTML = tasks.filter(t => String(t.project_id) === el('projectSelect').value).map(t =>
    `<button class="task-choice ${task?.id === t.id ? 'selected' : ''}" data-task="${t.id}">${esc(t.title)}<small>${esc(t.flow_status ? label(t.flow_status) : tr('Нет taskflow'))}</small></button>`).join('') || `<p>${esc(tr('Пока нет задач.'))}</p>`;
  el('taskList').querySelectorAll('[data-task]').forEach(button => button.onclick = () => action(() => selectTask(Number(button.dataset.task))));
}
function renderDetail() {
  el('taskTitle').textContent = task?.title || tr('Выбери задачу');
  el('taskMeta').textContent = run ? (panelLocale.language === 'en' ? `Task #${task.id} · Run #${run.run_id} · ${label(run.status)} · Version ${run.version} · Steps ${run.steps_done}/${run.max_steps}` : `Задача #${task.id} · Процесс #${run.run_id} · ${label(run.status)} · Версия ${run.version} · Шаги ${run.steps_done}/${run.max_steps}`) : tr('Процесс не выбран');
  el('description').textContent = task?.description || '';
  el('runSelect').innerHTML = runs.map(r => `<option value="${r.run_id}">#${r.run_id} · ${esc(label(r.status))}</option>`).join('');
  if (run) el('runSelect').value = run.run_id;
  el('flowReason').textContent = run?.reason || '';
  el('roleBoard').innerHTML = (run?.stages || []).map(s => `<article class="role"><strong>${esc(label(s.role))}</strong><p>${esc(label(s.status))}</p></article>`).join('');
  el('artifacts').innerHTML = (run?.artifacts || []).map(a => `<details><summary>${esc(label(a.role))} · ${esc(a.type)} · #${a.artifact_id} · mock</summary><p>${esc(tr('Входы:'))} ${esc(a.input_artifact_ids.join(', ') || tr('нет'))} · ${esc(a.created_at)}</p><pre>${esc(JSON.stringify(a.content,null,2))}</pre></details>`).join('') || `<p>${esc(tr('Артефактов пока нет.'))}</p>`;
  el('decisions').innerHTML = (run?.timeline || []).map(e => `<p>v${e.version} · ${esc(label(e.action) || e.action)} → ${esc(label(e.to_status))} · ${esc(e.created_at)}<br>${esc(e.reason)}</p>`).join('') || `<p>${esc(tr('Событий пока нет.'))}</p>`;
  el('rounds').innerHTML = (task?.rounds || []).map(r => `<article class="round-card"><h4>${esc(panelLocale.language === 'en' ? 'Legacy round' : 'Legacy раунд')} ${r.round_number}</h4>` + r.role_outputs.map(o => `<details><summary>${esc(o.role)} · ${esc(o.status)}</summary><pre>${esc(o.output)}</pre></details>`).join('') + '</article>').join('') || `<p>${esc(tr('Legacy-раундов нет.'))}</p>`;
  controls(); renderTasks();
}
async function selectTask(id, selectedRun) {
  task = await api('/tasks/' + id);
  runs = await api(`/taskflow/tasks/${id}/runs`);
  run = runs.find(r => r.run_id === selectedRun) || runs[0] || null;
  renderDetail();
}
async function refreshTasks() {
  tasks = await api('/tasks');
  if (task) await selectTask(task.id, run?.run_id);
  else renderTasks();
}
function renderCachedModels() {
  if (!cachedModels) return;
  el('cost').textContent = tr('Taskflow работает с Mock Director без вызовов моделей. Учёт затрат реальных моделей ожидает #18.');
  el('models').innerHTML = cachedModels.models.map(m => `<p>${esc(m.role)} · ${esc(m.model_id)} · ${esc(m.status)}</p>`).join('') || `<p>${esc(tr('В legacy-раундах модели ещё не вызывались.'))}</p>`;
}
async function refreshModels() {
  cachedModels = await api('/panel/status');
  renderCachedModels();
}
function renderProjects(selected) {
  el('projectSelect').innerHTML = projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
  if (selected) el('projectSelect').value = selected;
}
async function sendPending() {
  const request = pending;
  let response;
  try { response = await api(request.path,'POST',request.body); }
  catch (error) {
    if (error.httpStatus && error.httpStatus < 500) {
      pending = null;
      // Конфликт версии требует нового снимка и нового решения пользователя.
      if (error.httpStatus === 409) await selectTask(request.taskId, request.runId);
    } else {
      throw new Error(tr('Результат запроса неизвестен. Повторите тот же запрос кнопкой «Повторить запрос».'));
    }
    throw error;
  }
  pending = null;
  tasks = await api('/tasks');
  // Replay может вернуть старую версию: всегда перечитываем актуальный снимок.
  await selectTask(request.taskId, response.run_id);
  el('projectSelect').value = task.project_id;
  renderTasks();
}
function mutate(path, body) {
  if (pending) return;
  pending = {path, body:{...body,idempotency_key:crypto.randomUUID()},taskId:task.id,runId:run?.run_id};
  return sendPending();
}
el('projectForm').onsubmit = event => { event.preventDefault(); action(async () => {
  const project = await api('/projects','POST',{name:el('projectName').value});
  projects.push(project); renderProjects(project.id); el('projectName').value = ''; task = run = null; runs = []; renderDetail();
}); };
el('projectSelect').onchange = () => { task = run = null; runs = []; renderDetail(); };
el('runSelect').onchange = () => action(() => selectTask(task.id,Number(el('runSelect').value)));
el('taskForm').onsubmit = event => { event.preventDefault(); action(async () => {
  task = await api('/tasks','POST',{description:el('taskText').value,project_id:Number(el('projectSelect').value)});
  el('taskText').value = ''; run = null; runs = []; await refreshTasks();
}); };
el('newRun').onclick = () => action(() => mutate(`/taskflow/tasks/${task.id}/runs`, {max_steps:Number(el('maxSteps').value)}));
function command(actionName) {
  return mutate(`/taskflow/runs/${run.run_id}/commands`, {action:actionName,expected_version:run.version,reason:el('commentText').value});
}
el('runTask').onclick = () => action(() => command(run.status === 'planned' ? 'start' : 'resume'));
el('stepTask').onclick = () => action(() => command('step'));
el('pauseTask').onclick = () => action(() => command('block'));
el('stopTask').onclick = () => action(() => command('cancel'));
for (const [id, decision] of [['approveTask','approve'],['rejectTask','reject']]) {
  el(id).onclick = () => action(() => mutate(`/taskflow/runs/${run.run_id}/owner-decision`,{decision,expected_version:run.version,reason:el('commentText').value}));
}
el('retryRequest').onclick = () => action(sendPending);
el('refreshTasks').onclick = () => action(refreshTasks);
el('refreshModels').onclick = () => action(refreshModels);
async function init() {
  try { projects = await api('/projects'); renderProjects(); await refreshTasks(); await refreshModels(); status('Подключено'); }
  catch (error) { status(error.message); }
  controls();
}
el('languageSelect').onchange = () => panelLocale.setLanguage(el('languageSelect').value);
document.addEventListener('panel-language-change', () => {
  renderDetail(); renderCachedModels();
});
panelLocale.apply();
init();
