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
                context = browser.new_context(http_credentials={'username':'owner','password':'test-panel-password-32-characters-long'}, viewport={'width':1440,'height':1050})
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{port}')
                playwright.expect(page.locator('#status')).to_have_text('Подключено')
                yield page, playwright.expect
                if os.environ.get('PANEL_SCREENSHOT'):
                    page.screenshot(path=os.environ['PANEL_SCREENSHOT'], full_page=True)
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


def test_projects_retry_failure_history_reload_and_mobile(browser_page):
    page, expect = browser_page
    page.locator('#projectName').fill('Склад')
    page.get_by_role('button', name='Добавить проект', exact=True).click()
    expect(page.locator('#projectSelect option:checked')).to_have_text('Склад')
    create_task(page, expect, 'Проверить склад')
    expect(page.locator('#approveTask')).to_be_disabled()
    page.locator('#commentText').fill('Нужны уточнения')
    page.locator('#rejectTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Отклонена')
    expect(page.locator('#decisions')).to_contain_text('Нужны уточнения')
    page.locator('#runTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Ошибка', timeout=10000)
    expect(page.locator('#rounds')).to_contain_text('manager')
    expect(page.locator('#cost')).to_contain_text('Затраты неизвестны')
    page.reload()
    expect(page.locator('#status')).to_have_text('Подключено')
    page.locator('#projectSelect').select_option(label='Склад')
    page.locator('[data-task]').click()
    expect(page.locator('#decisions')).to_contain_text('Нужны уточнения')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


def test_approval_is_persisted_and_text_is_escaped(browser_page, monkeypatch, write_models_config):
    from backend.app.orchestration import round_runner
    from backend.app.providers.base import ChatResult
    page, expect = browser_page
    write_models_config({'manager':['openrouter/test'],'reviewer':['openrouter/test']})
    class Provider:
        def chat(self, **kwargs):
            return ChatResult('openrouter','test','<img src=x onerror="alert(1)">',1)
    monkeypatch.setattr(round_runner,'OpenRouterProvider',lambda *a: Provider())
    create_task(page, expect, 'Документация')
    page.locator('#runTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Ожидает решения', timeout=10000)
    assert page.locator('#rounds img').count() == 0
    page.locator('#commentText').fill('Принимаю текст')
    page.locator('#approveTask').click()
    expect(page.locator('#taskMeta')).to_contain_text('Подтверждена')
    expect(page.locator('#runTask')).to_be_disabled()
    page.reload()
    expect(page.locator('#status')).to_have_text('Подключено')
    page.locator('[data-task]').click()
    expect(page.locator('#decisions')).to_contain_text('Принимаю текст')
    expect(page.locator('#approveTask')).to_be_disabled()


def test_stop_during_actual_background_execution(browser_page, monkeypatch, write_models_config):
    from backend.app.orchestration import round_runner
    from backend.app.providers.base import ChatResult
    page, expect = browser_page
    write_models_config({'manager':['openrouter/test'],'reviewer':['openrouter/test']})
    started, release = Event(), Event()
    calls = []
    class Provider:
        def chat(self, **kwargs):
            calls.append(kwargs['model_id'])
            started.set()
            assert release.wait(10)
            return ChatResult('openrouter','test','Ответ после остановки',1)
    monkeypatch.setattr(round_runner,'OpenRouterProvider',lambda *a: Provider())
    create_task(page, expect, 'Документация')
    try:
        page.locator('#runTask').click()
        assert started.wait(5)
        expect(page.locator('#stopTask')).to_be_enabled()
        page.locator('#stopTask').click()
        expect(page.locator('#taskMeta')).to_contain_text('Останавливается')
        expect(page.locator('#runTask')).to_be_disabled()
    finally:
        release.set()
    expect(page.locator('#taskMeta')).to_contain_text('Остановлена', timeout=10000)
    expect(page.locator('#runTask')).to_be_enabled()
    assert calls == ['test']
    assert page.locator('#rounds details').count() == 0
    expect(page.locator('#decisions')).to_contain_text('Остановка')
