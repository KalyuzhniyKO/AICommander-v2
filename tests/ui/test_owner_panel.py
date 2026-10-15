"""Браузерные сценарии через настоящий HTTP-сервер и временную SQLite."""
import os
import socket
from contextlib import closing
from threading import Event, Thread
import time

import pytest

pytestmark = pytest.mark.skipif(os.environ.get('RUN_UI_TESTS') != '1', reason='RUN_UI_TESTS=1 и requirements-ui.txt включают Chromium UI tests')


@pytest.fixture
def browser_page(monkeypatch):
    playwright = pytest.importorskip('playwright.sync_api')
    import uvicorn
    from backend.app import main
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(main.app, host='127.0.0.1', port=port, log_level='error'))
    thread = Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and time.monotonic() < deadline:
        time.sleep(.02)
    assert server.started
    try:
        with playwright.sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                context = browser.new_context(base_url=f'http://127.0.0.1:{port}', http_credentials={'username':'owner','password':'test-panel-password-32-characters-long'}, viewport={'width':1440,'height':1050})
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{port}')
                playwright.expect(page.locator('#status')).to_have_text('Подключено')
                yield page, playwright.expect
                assert not errors
            finally:
                browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        assert not thread.is_alive()



def create_task(page, expect, description):
    page.locator('#taskText').fill(description)
    page.get_by_role('button', name='Создать задачу', exact=True).click()
    expect(page.locator('#taskTitle')).to_have_text(description)


def new_run(page, expect, max_steps=3):
    page.locator('#maxSteps').fill(str(max_steps))
    page.locator('#newRun').click()
    expect(page.locator('#taskMeta')).to_contain_text('Запланирован')


def start(page, expect):
    page.locator('#runTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Готов к следующему шагу')


def step(page, expect, count):
    page.locator('#stepTask').click()
    expect(page.locator('#artifacts details')).to_have_count(count)


def current(page):
    run_id=page.locator('#runSelect').input_value()
    return page.request.get('/taskflow/runs/'+run_id).json()


def external_command(page, action):
    run=current(page)
    result=page.request.post(f"/taskflow/runs/{run['run_id']}/commands",headers={'X-AICommander-Request':'1'},data={
        'idempotency_key':f"external-{run['version']}", 'expected_version':run['version'],'action':action})
    assert result.ok
    return result.json()


def test_projects_handoff_reject_resume_approve_reload_and_mobile(browser_page):
    page, expect=browser_page
    requests=[]
    page.on('request',lambda request: requests.append(request.url))
    page.locator('#projectName').fill('Склад')
    page.get_by_role('button',name='Добавить проект',exact=True).click()
    expect(page.locator('#projectSelect option:checked')).to_have_text('Склад')
    create_task(page,expect,'Приёмка товара')
    new_run(page,expect)
    expect(page.locator('#approveTask')).to_be_disabled()
    start(page,expect)
    for count in range(1,4):
        step(page,expect,count)
    expect(page.locator('#taskMeta')).to_contain_text('Ожидает решения')
    artifacts=current(page)['artifacts']
    assert artifacts[1]['content']['requirements']==artifacts[0]['content']
    assert artifacts[2]['content']['design']==artifacts[1]['content']
    page.locator('#commentText').fill('Уточнить план')
    page.locator('#rejectTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Заблокирован')
    expect(page.locator('#decisions')).to_contain_text('Уточнить план')
    page.locator('#runTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Ожидает решения')
    assert current(page)['artifacts']==artifacts
    page.locator('#commentText').fill('Принимаю mock-план')
    page.locator('#approveTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('План согласован')
    expect(page.locator('#stepTask')).to_be_disabled()
    page.reload()
    expect(page.locator('#status')).to_have_text('Подключено')
    page.locator('#projectSelect').select_option(label='Склад')
    page.locator('[data-task]').click()
    expect(page.locator('#decisions')).to_contain_text('Принимаю mock-план')
    expect(page.locator('#artifacts details')).to_have_count(3)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    if os.environ.get('PANEL_SCREENSHOT'):
        page.set_viewport_size({'width':1440,'height':1050})
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=os.environ['PANEL_SCREENSHOT'],full_page=True)
    assert not any('/rounds' in url or '/decision' in url.replace('/owner-decision','') or url.endswith('/run') for url in requests)


def test_cancel_new_run_history_and_step_limit(browser_page):
    page,expect=browser_page
    create_task(page,expect,'Остановить процесс')
    new_run(page,expect)
    start(page,expect)
    step(page,expect,1)
    old_run=current(page)
    page.locator('#stopTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Отменён')
    expect(page.locator('#runTask')).to_be_disabled()
    expect(page.locator('#approveTask')).to_be_disabled()
    new_run(page,expect,max_steps=1)
    start(page,expect)
    step(page,expect,1)
    expect(page.locator('#taskMeta')).to_contain_text('Заблокирован')
    expect(page.locator('#flowReason')).to_contain_text('лимит')
    expect(page.locator('#runTask')).to_be_disabled()
    page.locator('#runSelect').select_option(str(old_run['run_id']))
    expect(page.locator('#taskMeta')).to_contain_text('Отменён')
    assert current(page)['artifacts']==old_run['artifacts']


def test_stale_version_refreshes_without_repeating_step(browser_page):
    page,expect=browser_page
    create_task(page,expect,'Конкурентное изменение')
    new_run(page,expect)
    start(page,expect)
    changed=external_command(page,'step')
    page.locator('#stepTask').click()
    expect(page.locator('#status')).to_contain_text('Версия изменилась')
    expect(page.locator('#artifacts details')).to_have_count(1)
    assert current(page)['version']==changed['version']
    step(page,expect,2)


@pytest.mark.parametrize('failure',['network','server_error'])
def test_lost_response_replays_same_key_and_reads_latest_snapshot(browser_page,failure):
    page,expect=browser_page
    create_task(page,expect,'Потеря ответа')
    new_run(page,expect)
    start(page,expect)
    bodies=[]
    def lose_first_response(route):
        bodies.append(route.request.post_data_json)
        if len(bodies)==1:
            result=route.fetch()
            assert result.ok
            if failure=='network':
                route.abort('failed')
            else:
                route.fulfill(status=503,json={'detail':'Временная ошибка после commit'})
        else:
            route.continue_()
    page.route('**/taskflow/runs/*/commands',lose_first_response)
    page.locator('#stepTask').click()
    expect(page.locator('#status')).to_contain_text('Результат запроса неизвестен')
    expect(page.locator('#stepTask')).to_be_disabled()
    changed=external_command(page,'step')
    assert len(changed['artifacts'])==2
    page.locator('#retryRequest').click()
    expect(page.locator('#artifacts details')).to_have_count(2)
    expect(page.locator('#retryRequest')).to_be_hidden()
    assert bodies[0]==bodies[1]
    assert current(page)['version']==changed['version']


def test_failed_stage_resume_and_html_is_escaped(browser_page,monkeypatch):
    from backend.app.taskflow.director import MockDirector
    page,expect=browser_page
    create_task(page,expect,'<img src=x onerror="alert(1)">')
    new_run(page,expect,max_steps=4)
    start(page,expect)
    original=MockDirector.produce
    def fail(*args):
        raise RuntimeError('raw-secret-exception')
    monkeypatch.setattr(MockDirector,'produce',fail)
    page.locator('#stepTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Ошибка')
    expect(page.locator('#flowReason')).to_contain_text('Ошибка Mock Director')
    assert 'raw-secret-exception' not in page.content()
    monkeypatch.setattr(MockDirector,'produce',original)
    page.locator('#runTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Готов к следующему шагу')
    step(page,expect,1)
    assert page.locator('#artifacts img').count()==0
    assert '<img' in page.locator('#artifacts pre').text_content()
    run=current(page)
    page.reload()
    expect(page.locator('#status')).to_have_text('Подключено')
    page.locator('[data-task]').click()
    expect(page.locator('#artifacts details')).to_have_count(1)
    assert current(page)==run


def test_language_switch_preserves_task_artifacts_and_does_not_write(browser_page):
    """English UI is opt-in; switching never mutates stored tasks or invokes APIs."""
    page, expect = browser_page
    assert page.locator('html').get_attribute('lang') == 'ru'
    description = 'Пока нет задач. <тестовые данные>'
    create_task(page, expect, description)
    new_run(page, expect)
    start(page, expect)
    step(page, expect, 1)
    before = current(page)
    artifact_content = page.locator('#artifacts pre').first.text_content()
    writes = []
    page.on('request', lambda request: writes.append(request.url) if request.method not in ('GET', 'HEAD') else None)

    page.locator('#languageSelect').select_option('en')
    expect(page.locator('html')).to_have_attribute('lang', 'en')
    expect(page.locator('header h1')).to_have_text('Your AI team')
    expect(page.locator('#taskTitle')).to_have_text(description)
    expect(page.locator('#description')).to_have_text(description)
    expect(page.locator('#taskMeta')).to_contain_text('Ready for next step')
    expect(page.locator('#newRun')).to_have_text('New run')
    expect(page.locator('#artifacts details summary').first).to_contain_text('Analyst')
    expect(page.locator('#taskDetail > details > summary')).to_have_text('Legacy round history (separate from taskflow)')
    assert page.locator('#artifacts pre').first.text_content() == artifact_content
    assert current(page) == before

    page.locator('#languageSelect').select_option('ru')
    expect(page.locator('html')).to_have_attribute('lang', 'ru')
    expect(page.locator('header h1')).to_have_text('Твоя AI-команда')
    expect(page.locator('#taskMeta')).to_contain_text('Готов к следующему шагу')
    expect(page.locator('#taskDetail > details > summary')).to_have_text('История legacy-раундов (отдельно от taskflow)')
    assert current(page) == before
    assert not writes, 'Switching languages must not send mutations or model requests'


def test_mock_director_chat_shows_only_stored_evidence(browser_page):
    """Chat-looking bubbles are a read-only view, not fabricated Hermes/QA."""
    page, expect = browser_page
    expect(page.locator('#directorMessages .chat-bubble')).to_have_count(1)
    description = '<img src=x onerror=alert(1)> проверка безопасности'
    create_task(page, expect, description)
    expect(page.locator('#directorMessages .chat-bubble')).to_have_count(2)
    expect(page.locator('#directorMessages')).to_contain_text(description)
    assert page.locator('#directorMessages img').count() == 0
    expect(page.locator('#directorDisclaimer')).to_contain_text('Настоящий Hermes')

    new_run(page, expect)
    start(page, expect)
    step(page, expect, 1)
    record = current(page)
    assert len(record['artifacts']) == 1
    expect(page.locator('#directorMessages .chat-bubble')).to_have_count(3)
    expect(page.locator('#directorMessages')).to_contain_text(f"#{record['artifacts'][0]['artifact_id']}")
    expect(page.locator('#directorMessages')).to_contain_text('реальное программирование и QA не выполнялись')

    page.locator('#languageSelect').select_option('en')
    expect(page.locator('#directorHeading')).to_have_text('Director activity · demo')
    expect(page.locator('#directorMessages')).to_contain_text('Saved status')
    expect(page.locator('#directorMessages')).to_contain_text(description)
    assert page.locator('#directorMessages img').count() == 0
    assert current(page) == record
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
