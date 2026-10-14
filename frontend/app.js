let task = null, tasks = [], projects = [], busy = false, polling = false;
const el = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {active:'Создана', running:'Выполняется', stopping:'Останавливается', stopped:'Остановлена', awaiting_owner:'Ожидает решения', failed:'Ошибка', approved:'Подтверждена', rejected:'Отклонена', retry:'Запуск / повтор', approve:'Подтверждение', reject:'Отклонение', stop:'Остановка'};
async function api(path, method = 'GET', payload) {
  const options = {method, credentials:'same-origin', headers:{'Content-Type':'application/json','X-AICommander-Request':'1'}};
  if (payload !== undefined) options.body = JSON.stringify(payload);
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Запрос не выполнен');
  return data;
}
function status(text) { el('status').textContent = text; }
function controls() {
  const state = task?.status;
  el('runTask').disabled = busy || !['active','awaiting_owner','failed','stopped','rejected'].includes(state);
  el('stopTask').disabled = busy || state !== 'running';
  el('approveTask').disabled = busy || state !== 'awaiting_owner';
  el('rejectTask').disabled = busy || !['active','awaiting_owner','failed','stopped'].includes(state);
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
    `<button class="task-choice ${task?.id === t.id ? 'selected' : ''}" data-task="${t.id}">${esc(t.title)}<small>${esc(labels[t.status] || t.status)}</small></button>`).join('') || '<p>Пока нет задач.</p>';
  el('taskList').querySelectorAll('[data-task]').forEach(button => button.onclick = () => action(() => selectTask(Number(button.dataset.task))));
}
function renderDetail() {
  el('taskTitle').textContent = task?.title || 'Выбери задачу';
  el('taskMeta').textContent = task ? `#${task.id} · ${labels[task.status] || task.status}` : '';
  el('description').textContent = task?.description || '';
  el('rounds').innerHTML = (task?.rounds || []).map(r => `<article class="round-card"><h4>Раунд ${r.round_number}</h4><p>${esc(r.user_comment)}</p>` +
    r.role_outputs.map(o => `<details><summary>${esc(o.role)} · ${esc(o.status)} · ${esc(o.model_id)}</summary><pre>${esc(o.output)}</pre></details>`).join('') + '</article>').join('') || '<p>Артефактов пока нет.</p>';
  el('decisions').innerHTML = (task?.decisions || []).map(d => `<p>${esc(d.created_at)} UTC · ${esc(labels[d.action] || d.action)}<br>${esc(d.comment)}</p>`).join('') || '<p>Решений пока нет.</p>';
  controls(); renderTasks();
}
async function selectTask(id) { task = await api('/tasks/' + id); renderDetail(); }
async function refreshTasks() {
  tasks = await api('/tasks');
  if (task) await selectTask(task.id);
  else renderTasks();
}
async function refreshModels() {
  const data = await api('/panel/status');
  el('cost').textContent = data.cost.available ? `Затраты: ${data.cost.total}` : 'Затраты неизвестны: учёт бюджета ожидает #18.';
  el('models').innerHTML = data.models.map(m => `<p>${esc(m.role)} · ${esc(m.model_id)} · ${esc(m.status)}</p>`).join('') || '<p>Модели ещё не вызывались.</p>';
}
el('projectForm').onsubmit = event => { event.preventDefault(); action(async () => {
  const project = await api('/projects','POST',{name:el('projectName').value});
  projects.push(project); renderProjects(project.id); el('projectName').value = ''; task = null; renderDetail();
}); };
function renderProjects(selected) {
  el('projectSelect').innerHTML = projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
  if (selected) el('projectSelect').value = selected;
}
el('projectSelect').onchange = () => { task = null; renderDetail(); };
el('taskForm').onsubmit = event => { event.preventDefault(); action(async () => {
  task = await api('/tasks','POST',{description:el('taskText').value,project_id:Number(el('projectSelect').value)});
  el('taskText').value = ''; await refreshTasks();
}); };
el('runTask').onclick = () => action(async () => { await api(`/tasks/${task.id}/run`,'POST',{comment:el('commentText').value}); await refreshTasks(); });
for (const [id, decision] of [['stopTask','stop'],['approveTask','approve'],['rejectTask','reject']]) {
  el(id).onclick = () => action(async () => { task = await api(`/tasks/${task.id}/decision`,'POST',{action:decision,comment:el('commentText').value}); renderDetail(); await refreshTasks(); });
}
el('refreshTasks').onclick = () => action(refreshTasks);
el('refreshModels').onclick = () => action(refreshModels);
async function init() {
  try { projects = await api('/projects'); renderProjects(); await refreshTasks(); await refreshModels(); status('Подключено'); }
  catch (error) { status(error.message); }
  controls();
}
setInterval(async () => {
  if (busy || polling || !task || !['running','stopping'].includes(task.status)) return;
  polling = true;
  try { await refreshTasks(); await refreshModels(); }
  catch (error) { status(error.message); }
  finally { polling = false; }
}, 1500);
init();
