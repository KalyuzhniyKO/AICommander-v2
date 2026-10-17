"""Reproducible synthetic accounting exercise; no provider/SDK imports or HTTP."""
import json
from pathlib import Path
import tempfile

from .ledger import BudgetError, BudgetLedger
from .models import Limits, Outcome, Policy, Request, Route, Tariff


def synthetic_report():
    now=[1_000_000]
    with tempfile.TemporaryDirectory(prefix='aicommander-budget-fixture-') as scratch:
        ledger=BudgetLedger(Path(scratch)/'ledger.sqlite3',clock_ms=lambda:now[0])
        ledger.initialize()
        ledger.create_account('synthetic-free',Policy(routes=(Route(role='analyst',model_id='fixture/model',
            tariff=Tariff(input_micro_usd_per_million=0,output_micro_usd_per_million=0)),),
            limits=Limits(max_requests=2)))
        def request(operation):
            return Request(operation_id=operation,role='analyst',model_id='fixture/model',input_tokens=80,output_tokens=20,timeout_seconds=10)
        decisions=[]
        decisions.append(ledger.reserve('synthetic-free',request('quota')).model_dump())
        ledger.claim('quota') # A permission, not a network call.
        ledger.record('quota',Outcome(kind='quota',http_status=429,retry_after_seconds=60))
        decisions.append(ledger.reserve('synthetic-free',request('next')).model_dump())
        now[0]+=60_000 # Advance a fixture clock; no real sleep, scheduler or retry.
        decisions.append(ledger.reserve('synthetic-free',request('next')).model_dump())
        decisions.append(ledger.reserve('synthetic-free',request('limit')).model_dump())
        ledger.claim('next');ledger.record('next',Outcome(kind='unknown'))
        try:ledger.claim('next')
        except BudgetError as exc:blocked_claim=exc.code
        decisions.append(ledger.reserve('synthetic-free',request('unknown-block')).model_dump())
        ledger.create_account('synthetic-unpriced',Policy(routes=(Route(role='analyst',model_id='fixture/model'),)))
        decisions.append(ledger.reserve('synthetic-unpriced',request('unpriced')).model_dump())
        return {'schema_version':'1.0','kind':'synthetic_offline_example','live_calls':0,'actual_prices_verified':False,
            'decisions':decisions,'repeat_claim':blocked_claim,'accounts':[ledger.report('synthetic-free'),ledger.report('synthetic-unpriced')]}


if __name__=='__main__':
    print(json.dumps(synthetic_report(),indent=2,ensure_ascii=False))
