"""Shared authenticated Chromium against the isolated temporary app."""
import socket
from threading import Thread
import time

import pytest

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

