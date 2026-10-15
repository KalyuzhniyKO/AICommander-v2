"""Export the public schema and a deterministic mock-only UI example."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from backend.app.storage.db import init_db
from backend.app.storage.repositories import Repository
from .models import Command, CreateRun, OwnerDecision, RunSnapshot
from .service import Taskflow


def export(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(':memory:')) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        init_db(conn)
        task = Repository(conn).create_task('Подготовить офлайн-план приёмки товара')
        flow = Taskflow(conn)
        run = flow.create(task['id'], CreateRun(idempotency_key='example-create'))
        for index, action in enumerate(['start', 'step', 'step', 'step']):
            run = flow.apply(run.run_id, Command(idempotency_key=f'example-{index}', expected_version=run.version, action=action))
        example = run.model_dump(mode='json')
    # Fixture timestamps are examples, not evidence of an actual execution time.
    for obj in [example, *example['artifacts'], *example['timeline']]:
        for key in ['created_at', 'updated_at']:
            if key in obj:
                obj[key] = '2026-10-14T00:00:00.000Z'
    requests = {model.__name__: model.model_json_schema() for model in (CreateRun, Command, OwnerDecision)}
    for name, data in [('taskflow-v1.schema.json', RunSnapshot.model_json_schema()),
                       ('taskflow-v1.requests.json', requests), ('taskflow-v1.example.json', example)]:
        (output_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    export(Path(__file__).resolve().parents[3] / 'docs' / 'contracts')
