"""Synthetic tariffs, responses and transport; real temporary SQLite and concurrency."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import sqlite3
from threading import Barrier

import pytest
from pydantic import ValidationError

from backend.app.budgets.ledger import BudgetError, BudgetLedger
from backend.app.budgets.models import Limits, Outcome, Policy, Request, Route, Tariff, Usage


FREE=Tariff(input_micro_usd_per_million=0,output_micro_usd_per_million=0)
PAID=Tariff(input_micro_usd_per_million=1_000_000,output_micro_usd_per_million=2_000_000)


class Clock:
    value=1_000_000
    def __call__(self):return self.value
    def advance(self,seconds):self.value+=seconds*1000


def policy(tariff=FREE,**limits):
    return Policy(routes=(Route(role='analyst',model_id='synthetic/model',tariff=tariff),),limits=Limits(**limits))


def request(op='one',**changes):
    return Request(operation_id=op,role='analyst',model_id='synthetic/model',input_tokens=80,output_tokens=20,timeout_seconds=10,**changes)


@pytest.fixture
def ledger(tmp_path):
    clock=Clock();ledger=BudgetLedger(tmp_path/'budget.sqlite3',clock_ms=clock)
    ledger.initialize();ledger.initialize()
    return ledger,clock


def test_explicit_initialize_policy_binding_and_old_app_data_are_preserved(tmp_path):
    path=tmp_path/'budget.sqlite3';ledger=BudgetLedger(path)
    assert not path.exists()
    with pytest.raises(BudgetError,match='ledger_uninitialized'):ledger.create_account('a',policy())
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute('CREATE TABLE tasks(id INTEGER PRIMARY KEY,description TEXT)')
        conn.execute("INSERT INTO tasks VALUES(1,'synthetic legacy task')")
    ledger.initialize();ledger.create_account('a',policy());ledger.create_account('a',policy())
    with pytest.raises(BudgetError,match='policy_conflict'):ledger.create_account('a',policy(max_requests=2))
    with closing(sqlite3.connect(path)) as conn, conn:
        assert conn.execute('SELECT description FROM tasks').fetchone()[0]=='synthetic legacy task'
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
    with pytest.raises(BudgetError,match='file_backed'):BudgetLedger(':memory:')


@pytest.mark.parametrize('tariff,limits,code',[(None,{},'pricing_unknown'),(PAID,{},'paid_approval_required'),(PAID,{'allow_paid':True,'max_micro_usd':119},'money_budget'),(FREE,{'max_input_tokens':79},'input_limit'),(FREE,{'max_output_tokens':19},'output_limit'),(FREE,{'max_request_seconds':9},'timeout_limit'),(FREE,{'max_total_tokens':99},'token_budget'),(FREE,{'lifetime_seconds':9},'deadline_exhausted')])
def test_denial_happens_before_reservation_or_dispatch(ledger,tariff,limits,code):
    store,_=ledger;store.create_account('a',policy(tariff,**limits))
    decision=store.reserve('a',request())
    assert not decision.allowed and decision.code==code
    assert store.report('a')['requests_committed']==0
    with pytest.raises(BudgetError,match='reservation_not_found'):store.claim('one')


def test_model_name_is_not_free_pricing_evidence_and_wrong_roles_do_not_route(ledger):
    store,_=ledger
    store.create_account('a',Policy(routes=(Route(role='analyst',model_id='synthetic/free'),)))
    unknown=Request(**{**request().model_dump(),'model_id':'synthetic/free'})
    assert store.reserve('a',unknown).code=='pricing_unknown'
    assert store.reserve('a',request()).code=='route_not_allowed'
    wrong=Request(**{**unknown.model_dump(),'role':'developer'})
    assert store.reserve('a',wrong).code=='route_not_allowed'


def test_paid_approval_integer_rounding_exact_boundary_and_actual_cost_unknown(ledger):
    store,_=ledger;store.create_account('a',policy(PAID,allow_paid=True,max_micro_usd=120))
    decision=store.reserve('a',request())
    assert decision.allowed and decision.estimated_micro_usd==120 and decision.code=='allowed_paid_approved'
    assert Tariff(input_micro_usd_per_million=1,output_micro_usd_per_million=1).quote(1,1)==2
    assert store.reserve('a',request('two')).code=='money_budget'
    store.claim('one');store.record('one',Outcome(kind='completed',http_status=200))
    report=store.report('a')
    assert report['reported_cost_micro_usd'] is None and not report['reported_cost_complete']
    assert report['budget_committed_micro_usd']==120 and report['known_cost_subtotal_micro_usd']==0


def test_reported_usage_releases_only_known_capacity_and_is_idempotent(ledger):
    store,_=ledger;store.create_account('a',policy(PAID,allow_paid=True,max_micro_usd=150,max_total_tokens=150,max_requests=2))
    store.reserve('a',request());store.claim('one')
    outcome=Outcome(kind='completed',http_status=200,usage=Usage(input_tokens=5,output_tokens=5,cost_micro_usd=15))
    store.record('one',outcome);store.record('one',outcome)
    report=store.report('a')
    assert report['requests_committed']==1 and report['tokens_committed']==10 and report['reported_cost_micro_usd']==15
    assert store.reserve('a',request('two')).allowed
    with pytest.raises(BudgetError,match='outcome_conflict'):store.record('one',Outcome(kind='completed',http_status=200))


def test_replay_reopen_and_exclusive_dispatch_with_fixture_transport(ledger):
    store,clock=ledger;store.create_account('a',policy(max_requests=1))
    assert store.reserve('a',request()).created
    repeat=store.reserve('a',request())
    assert not repeat.allowed and not repeat.created and repeat.code=='reservation_exists'
    reopened=BudgetLedger(store.path,clock_ms=clock);sent=[]
    permit=reopened.claim('one');sent.append(permit.operation_id) # The only fixture "send".
    with pytest.raises(BudgetError,match='dispatch_already'):store.claim('one')
    with pytest.raises(BudgetError,match='operation_conflict'):
        store.reserve('a',Request(**{**request().model_dump(),'output_tokens':21}))
    with pytest.raises(BudgetError,match='cannot_release'):store.release_unclaimed('one')
    reopened.record('one',Outcome(kind='unknown'))
    with pytest.raises(BudgetError,match='dispatch_already'):reopened.claim('one')
    assert not reopened.reserve('a',request()).allowed and sent==['one']
    report=reopened.report('a');assert report['requests_committed']==1 and report['tokens_committed']==100
    assert report['states']=={'unknown':1} and report['reported_cost_micro_usd'] is None
    with pytest.raises(BudgetError,match='outcome_conflict'):store.record('one',Outcome(kind='completed',http_status=200,usage=Usage(input_tokens=0,output_tokens=0,cost_micro_usd=0)))


def test_unclaimed_release_refunds_capacity_but_never_reuses_operation_id(ledger):
    store,_=ledger;store.create_account('a',policy(max_requests=1))
    store.reserve('a',request());store.release_unclaimed('one');store.release_unclaimed('one')
    assert store.report('a')['requests_committed']==0
    assert store.reserve('a',request()).state=='released'
    with pytest.raises(BudgetError,match='dispatch_already'):store.claim('one')
    assert store.reserve('a',request('two')).allowed


def test_competing_reservations_cannot_overspend_the_last_slot(ledger):
    store,clock=ledger;store.create_account('a',policy(max_requests=1,max_total_tokens=100));barrier=Barrier(2)
    def reserve(op):
        peer=BudgetLedger(store.path,clock_ms=clock);barrier.wait(timeout=5)
        return peer.reserve('a',request(op))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(reserve,['one','two']))
    assert sum(x.allowed for x in results)==1
    assert store.report('a')['requests_committed']==1
    assert store.report('a')['tokens_committed']==100


def test_only_one_concurrent_claim_gets_permission(ledger):
    store,clock=ledger;store.create_account('a',policy());store.reserve('a',request());barrier=Barrier(2)
    def claim(_):
        peer=BudgetLedger(store.path,clock_ms=clock);barrier.wait(timeout=5)
        try:return peer.claim('one').operation_id
        except BudgetError as exc:return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,range(2)))
    assert sorted(results)==['dispatch_already_claimed_or_closed','one']


def test_quota_cooldown_honors_retry_after_and_never_resends(ledger):
    store,clock=ledger;store.create_account('a',policy(base_backoff_seconds=10,max_backoff_seconds=20))
    store.reserve('a',request());store.reserve('a',request('queued'));store.claim('one')
    store.record('one',Outcome(kind='quota',http_status=429,retry_after_seconds=100))
    report=store.report('a');assert report['cooldown_until_ms']==clock.value+100_000
    before=store.report('a')
    for _ in range(3):
        assert store.reserve('a',request('new')).code=='provider_cooldown'
        with pytest.raises(BudgetError,match='provider_cooldown'):store.claim('queued')
    assert store.report('a')==before
    clock.advance(100);assert store.claim('queued').operation_id=='queued'
    store.record('queued',Outcome(kind='quota',http_status=200,provider_code='quota_exhausted'))
    assert store.report('a')['cooldown_until_ms']==clock.value+20_000
    assert store.report('a')['quota_streak']==2
    assert store.report('a')['dispatches_claimed']==2


def test_late_success_does_not_clear_another_requests_cooldown(ledger):
    store,clock=ledger;store.create_account('a',policy(base_backoff_seconds=10))
    for op in ('one','two'):store.reserve('a',request(op));store.claim(op)
    store.record('one',Outcome(kind='quota',http_status=429))
    store.record('two',Outcome(kind='completed',http_status=200))
    assert store.report('a')['cooldown_until_ms']==clock.value+10_000
    assert store.report('a')['quota_streak']==1
    assert store.reserve('a',request('three')).code=='provider_cooldown'


@pytest.mark.parametrize('usage',[Usage(input_tokens=81,output_tokens=0,cost_micro_usd=1),Usage(input_tokens=1,output_tokens=21,cost_micro_usd=1),Usage(input_tokens=1,output_tokens=1,cost_micro_usd=121)])
def test_overrun_is_preserved_and_blocks_other_queued_dispatches(ledger,usage):
    store,_=ledger;store.create_account('a',policy(PAID,allow_paid=True,max_micro_usd=1000))
    for op in ('one','two'):store.reserve('a',request(op))
    store.claim('one');store.record('one',Outcome(kind='completed',http_status=200,usage=usage))
    assert store.report('a')['overrun']
    with pytest.raises(BudgetError,match='usage_overrun'):store.claim('two')
    assert store.reserve('a',request('three')).code=='usage_overrun'


def test_deadline_cannot_be_extended_by_replay_or_clock_rollback(ledger):
    store,clock=ledger;store.create_account('a',policy(lifetime_seconds=20));store.reserve('a',request())
    clock.advance(11)
    with pytest.raises(BudgetError,match='deadline_exhausted'):store.claim('one')
    clock.value-=1000
    with pytest.raises(BudgetError,match='clock_regressed'):store.claim('one')
    store.create_account('a',policy(lifetime_seconds=20))
    assert store.report('a')['deadline_ms']==1_020_000


@pytest.mark.parametrize('bad',[True,1.5,-1,float('nan'),float('inf'),'100'])
def test_numeric_budget_values_are_strict_and_do_not_echo_input(bad):
    with pytest.raises(ValidationError):Limits(max_micro_usd=bad)
    with pytest.raises(ValidationError):Usage(input_tokens=bad,output_tokens=0)
    with pytest.raises(ValidationError):Tariff(input_micro_usd_per_million=bad,output_micro_usd_per_million=0)


def test_unsupported_schema_and_corruption_fail_closed(tmp_path):
    path=tmp_path/'future.sqlite3'
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute('CREATE TABLE budget_version(version INTEGER PRIMARY KEY)');conn.execute('INSERT INTO budget_version VALUES(2)')
    store=BudgetLedger(path)
    with pytest.raises(BudgetError,match='unsupported_ledger_version'):store.initialize()
    with closing(sqlite3.connect(path)) as conn, conn:assert conn.execute("SELECT name FROM sqlite_master WHERE name='budget_accounts'").fetchone() is None
    with pytest.raises(BudgetError,match='unsupported_ledger_version'):store.create_account('a',policy())
    safe_path=tmp_path/'corrupt.sqlite3';safe=BudgetLedger(safe_path);safe.initialize();safe.create_account('a',policy())
    with closing(sqlite3.connect(safe_path)) as conn, conn:
        conn.execute("UPDATE budget_accounts SET policy_json='synthetic-private-corrupt-value'")
    with pytest.raises(BudgetError,match='ledger_corrupt') as exc:safe.report('a')
    assert 'synthetic-private-corrupt-value' not in str(exc.value)


def test_secrets_prompts_and_raw_provider_errors_are_not_metadata(ledger):
    store,_=ledger
    secret='synthetic-private-value-never-store'
    with pytest.raises(ValidationError) as exc:Outcome(kind='unknown',raw_error=secret)
    assert secret not in str(exc.value)
    store.create_account('a',policy());store.reserve('a',request());store.claim('one');store.record('one',Outcome(kind='unknown'))
    assert secret not in json.dumps(store.report('a'))
    with pytest.raises(BudgetError,match='invalid_identifier') as exc:store.report('Bearer '+secret)
    assert secret not in str(exc.value)


def test_mutated_models_do_not_bypass_validation(ledger):
    store,_=ledger;store.create_account('a',policy())
    with pytest.raises(ValidationError):store.reserve('a',request().model_copy(update={'output_tokens':-1}))
    store.reserve('a',request());store.claim('one')
    with pytest.raises(ValidationError):store.record('one',Outcome(kind='completed',http_status=200).model_copy(update={'usage':{'input_tokens':-1,'output_tokens':0}}))
    assert store.report('a')['states']=={'dispatched':1}


def test_synthetic_example_matches_published_report_and_does_not_send_requests():
    from pathlib import Path
    from backend.app.budgets.demo import synthetic_report
    result=synthetic_report()
    assert result['live_calls']==0
    assert [d['code'] for d in result['decisions']]==['allowed_declared_free','provider_cooldown','allowed_declared_free','request_limit','outcome_unknown','pricing_unknown']
    assert result['accounts'][0]['states']=={'quota':1,'unknown':1}
    assert result['accounts'][0]['reported_cost_micro_usd'] is None
    contract=Path(__file__).resolve().parents[1]/'docs/contracts/budget-offline.example.json'
    assert result==json.loads(contract.read_text())


def test_policy_schema_export_is_current():
    from pathlib import Path
    contract=Path(__file__).resolve().parents[1]/'docs/contracts/budget-policy-v1.schema.json'
    assert json.loads(contract.read_text())==Policy.model_json_schema()



def test_unknown_outcome_fences_new_and_previously_reserved_requests(ledger):
    store,_=ledger;store.create_account('a',policy())
    store.reserve('a',request('one'));store.reserve('a',request('queued'));store.claim('one')
    store.record('one',Outcome(kind='unknown'))
    assert store.reserve('a',request('new')).code=='outcome_unknown'
    with pytest.raises(BudgetError,match='outcome_unknown'):store.claim('queued')
    assert store.report('a')['tokens_committed']==200
