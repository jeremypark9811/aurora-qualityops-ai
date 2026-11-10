import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import select, func

from app import create_app
from qualityops.catalog import Catalog
from qualityops.models import Source, Claim, Analysis, Approval, BatchState, Task, Audit
from qualityops.service import DomainError
from qualityops.ai import explain

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session')
def full_catalog():
    return Catalog(ROOT)


@pytest.fixture
def catalog(full_catalog):
    cat = copy.copy(full_catalog)
    cat.tables = copy.deepcopy(full_catalog.tables)
    # Tests use real W03 fixtures; unrelated high-volume commercial tables are not required.
    for key in ('orders', 'shipments', 'consumption'):
        cat.tables[key] = cat.tables[key][:5]
    return cat


@pytest.fixture
def app(catalog, tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    return create_app({'TESTING': True, 'DATABASE_URL': 'sqlite:///' + (tmp_path/'test.db').as_posix()}, catalog)


class Client:
    def __init__(self, app):
        self.client = app.test_client()
        self.csrf = self.client.get('/api/bootstrap').json['csrf']

    def post(self, path, data, status=200):
        response = self.client.post(path, json=data, headers={'X-CSRF-Token': self.csrf})
        assert response.status_code == status, response.json
        return response.json

    def role(self, role, actor=None):
        return self.post('/api/role', {'role': role, 'actor': actor or role + ' 검토자'})

    def scenario(self, kind='normal'):
        return self.post('/api/demo/scenario', {'scenario': kind}, 201)

    def detail(self, identity):
        return self.client.get('/api/claims/' + str(identity)).json


@pytest.fixture
def c(app):
    return Client(app)


def decision(c, approval, value='승인', status=200):
    return c.post('/api/approvals/%s/decision' % approval, {'decision': value, 'reason': '원본 근거 검토에 따른 위원회 의결'}, status)


def test_catalog_content_not_names(full_catalog):
    assert len(full_catalog.entries) == 54
    assert full_catalog.sources['qc'].endswith('fin_ap_aging_ms (2).csv')
    assert full_catalog.sources['batches'].endswith('sales_meeting_notes_cv (2).md')
    assert len(full_catalog.rows('batches')) == 480
    assert len(full_catalog.rows('qc')) == 165
    assert full_catalog.document('# quality_policy')[0].endswith('fin_ar_aging_ms (2).csv')


def test_normal_approval_creates_actual_tasks(c, app):
    d = c.scenario()
    f = d['analyses'][0]['result']
    assert f['confirmed_qty'] == 17900
    assert f['produced_qty'] == 150745
    assert f['rate_pct'] == pytest.approx(17900/150745*100)
    assert f['trace_coverage_pct'] == 100
    assert d['claim']['status'] == '승인 대기'
    c.role('품질위원회')
    decision(c, d['approvals'][0]['id'])
    after = c.detail(d['claim']['id'])
    assert after['claim']['status'] == '회수 진행'
    assert after['batch_state']['recall_approved']
    assert {'영업팀', '생산팀'} <= {t['department'] for t in after['tasks']}
    assert after['plans'][0]['status'] == '생산 여력 확인 필요'
    assert after['plans'][0]['data']['shortage_qty'] is None
    assert after['audit'][-1]['action'] == '재공급 계획 재계산'


def test_no_approval_no_recall(c):
    d = c.scenario()
    assert not d['batch_state']['recall_approved']
    assert not any(t['department'] == '영업팀' for t in d['tasks'])
    decision(c, d['approvals'][0]['id'], status=403)
    assert not c.detail(d['claim']['id'])['batch_state']['recall_approved']


def test_double_decision_conflict(c):
    d = c.scenario()
    c.role('품질위원회')
    aid = d['approvals'][0]['id']
    decision(c, aid)
    count = len(c.detail(d['claim']['id'])['tasks'])
    decision(c, aid, status=409)
    assert len(c.detail(d['claim']['id'])['tasks']) == count


def test_same_actor_cannot_approve(c):
    d = c.scenario()
    c.role('품질위원회', d['claim']['reporter'])
    decision(c, d['approvals'][0]['id'], status=403)


@pytest.mark.parametrize('value,status', [('거절','원인 조사'), ('추가 정보 요청','정보 확인 필요'), ('보류','보류')])
def test_other_decisions(c, value, status):
    d = c.scenario('rejected')
    c.role('품질위원회')
    decision(c, d['approvals'][0]['id'], value)
    after = c.detail(d['claim']['id'])
    assert after['claim']['status'] == status
    assert not after['batch_state']['recall_approved']
    assert not any(t['department'] in ('영업팀','생산팀') for t in after['tasks'])


def test_missing_trace_reply_restarts_same_workflow(c):
    d = c.scenario('missing')
    assert d['claim']['status'] == '정보 확인 필요'
    assert d['analyses'][0]['result']['trace_coverage_pct'] == 0
    assert not d['approvals']
    task = next(t for t in d['tasks'] if t['department']=='물류팀')
    mapping = {r['shipment_id']:r['customer_id'] for r in task['details']['links']}
    c.role('물류팀')
    c.post(f"/api/department-tasks/{task['id']}/update", {'status':'완료','reason':'원본 출하처 대조 완료','reply':{'mapping':mapping}})
    after = c.detail(d['claim']['id'])
    assert after['claim']['status']=='승인 대기'
    assert after['analyses'][0]['result']['trace_coverage_pct']==100
    assert after['approvals']


def test_reply_cannot_invent_or_reassign_customer(c):
    d = c.scenario('missing')
    task = next(t for t in d['tasks'] if t['department']=='물류팀')
    mapping = {r['shipment_id']:'C-101' for r in task['details']['links']}
    c.role('물류팀')
    c.post(f"/api/department-tasks/{task['id']}/update", {'status':'완료','reason':'확인','reply':{'mapping':mapping}}, 400)
    assert c.detail(d['claim']['id'])['claim']['status']=='정보 확인 필요'


def test_news_keeps_numbers_and_prioritizes_investigation(c):
    d = c.scenario('changed')
    old, latest = d['analyses'][1]['result'], d['analyses'][0]['result']
    assert old['rate_pct'] == latest['rate_pct']
    assert old['confirmed_qty'] == latest['confirmed_qty']
    assert any(t['priority']=='긴급' and t['dedupe_key'].startswith('news:') for t in d['tasks'])
    assert d['approvals'][-1]['status']=='재분석으로 대체'


def test_repeated_same_batch_uses_existing_recall(c):
    first = c.scenario()
    c.role('품질위원회')
    decision(c, first['approvals'][0]['id'])
    count = len(first['tasks'])
    c.role('접수 담당')
    second = c.scenario()
    assert second['analyses'][0]['result']['existing_recall']
    assert not second['approvals']
    assert second['inherited_approval']['status']=='승인'
    assert second['claim']['status']=='회수 진행'
    assert len([t for t in second['tasks'] if t['department']=='영업팀'])==2


@pytest.mark.parametrize('field,value', [('batch_id','MISSING'),('customer_id','NONE'),('product_id','PL-03'),('occurred_on','2025-01-01'),('occurred_on','bad'),('description','')])
def test_claim_validation(c, field, value):
    payload={'batch_id':'B-02-2602-01','customer_id':'C-101','product_id':'PL-02','claim_type':'피부트러블','occurred_on':'2026-06-30','description':'고객 주장'}
    payload[field]=value
    response=c.client.post('/api/claims',json=payload,headers={'X-CSRF-Token':c.csrf})
    assert response.status_code in (400,404)
    assert c.client.get('/api/claims').json['items']==[]


@pytest.mark.parametrize('kind', ['zero','unknown','no_links','date_conflict','qty_conflict'])
def test_bad_source_values_block_action(catalog, tmp_path, kind, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    batch=next(r for r in catalog.rows('batches') if r['batch_id']=='B-02-2602-01')
    if kind=='zero':batch['produced_qty']='0'
    if kind=='unknown':
        for row in catalog.rows('qc'):
            if row['batch_id']==batch['batch_id']:row['defect_confirmed']='보류'
    if kind=='no_links':catalog.tables['links']=[r for r in catalog.rows('links') if r['batch_id']!=batch['batch_id']]
    if kind in ('date_conflict','qty_conflict'):
        row=next(r for r in catalog.rows('links') if r['batch_id']==batch['batch_id'])
        row['ship_date' if kind=='date_conflict' else 'shipped_qty']='2025-01-01' if kind=='date_conflict' else '999999999'
    client=Client(create_app({'TESTING':True,'DATABASE_URL':'sqlite:///' + (tmp_path/'edge.db').as_posix()},catalog))
    d=client.scenario()
    assert d['claim']['status']=='정보 확인 필요'
    assert not d['approvals']
    assert d['analyses'][0]['result']['missing']


def test_capacity_shortage_changes_sales_and_priority(c):
    d=c.scenario()
    c.role('품질위원회');decision(c,d['approvals'][0]['id'])
    d=c.detail(d['claim']['id'])
    task=next(t for t in d['tasks'] if t['department']=='생산팀')
    c.role('생산팀')
    reply={'normal_stock_qty':100,'free_capacity_qty':200,'capacity_period':'2026-07 시연','existing_commitments_protected':True}
    c.post(f"/api/department-tasks/{task['id']}/update",{'status':'완료','reason':'수량·기간·기존 약속 확인','reply':reply})
    d=c.detail(d['claim']['id'])
    assert d['plans'][0]['data']['shortage_qty']==d['plans'][0]['data']['required_qty']-300
    assert any(t['department']=='생산팀' and t['status']!='완료' for t in d['tasks'])
    assert all(t['details'].get('recovery') for t in d['tasks'] if t['department']=='영업팀')
    c.role('영업팀');c.post('/api/settings/priority',{'method':'고객 코드 순'})
    assert c.detail(d['claim']['id'])['plans'][0]['data']['allocations'][0]['customer_id']=='C-101'


def test_capacity_reply_requires_protecting_commitments(c):
    d=c.scenario();c.role('품질위원회');decision(c,d['approvals'][0]['id'])
    task=next(t for t in c.detail(d['claim']['id'])['tasks'] if t['department']=='생산팀')
    c.role('생산팀')
    c.post(f"/api/department-tasks/{task['id']}/update",{'status':'완료','reason':'확인','reply':{'normal_stock_qty':1,'free_capacity_qty':1}},400)


def test_repeat_alert_creates_task(c, app):
    # Original PL-02 / skin complaints in March are real records, not invented observations.
    for index in range(3):
        c.post('/api/claims',{'batch_id':'B-02-2602-01','customer_id':'C-101','product_id':'PL-02','claim_type':'반복시연','occurred_on':'2026-06-30','description':'시연 입력'},201)
    c.post('/api/claims/3/analyze',{})
    alerts=c.client.get('/api/extensions').json['alerts']
    assert alerts and alerts[0]['details']['count']==3
    assert not c.detail(3)['batch_state']['recall_approved']


def test_persistence_and_idempotent_import(app, catalog):
    c=Client(app);d=c.scenario()
    with app.extensions['db_sessions']() as db:
        count=db.scalar(select(func.count()).select_from(Source))
    restarted=create_app({'TESTING':True,'DATABASE_URL':app.config['DATABASE_URL']},catalog)
    c2=Client(restarted)
    assert c2.detail(d['claim']['id'])['claim']['status']=='승인 대기'
    with restarted.extensions['db_sessions']() as db:
        assert db.scalar(select(func.count()).select_from(Source))==count


def test_demo_reset_preserves_source_and_audit(c, app):
    c.scenario();c.role('품질팀')
    with app.extensions['db_sessions']() as db:
        count=db.scalar(select(func.count()).select_from(Source))
    c.post('/api/demo/reset',{'confirmation':'시연 데이터 초기화'})
    assert c.client.get('/api/claims').json['items']==[]
    assert c.client.get('/api/audit-logs').json['items']
    with app.extensions['db_sessions']() as db:
        assert db.scalar(select(func.count()).select_from(Source))==count


def test_demo_reset_cannot_remove_real_operations(c):
    c.scenario()
    c.post('/api/claims',{'batch_id':'B-02-2602-01','customer_id':'C-101','product_id':'PL-02','claim_type':'피부트러블','occurred_on':'2026-06-30','description':'실제 신규 운영 입력'},201)
    c.role('품질팀')
    c.post('/api/demo/reset',{'confirmation':'시연 데이터 초기화'},409)


def test_csrf_and_role_checks(c):
    assert c.client.post('/api/demo/scenario',json={'scenario':'normal'}).status_code==403
    d=c.scenario();c.role('영업팀')
    c.post(f"/api/claims/{d['claim']['id']}/analyze",{},403)


def test_api_failure_and_no_key_fallback(monkeypatch):
    f={'conclusion':'회수 심사 대상','missing':[],'rate_pct':11.87,'produced_qty':150745,'confirmed_qty':17900,'recall_eligible':True}
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert explain(f,'설명')['mode']=='규칙 기반 분석'
    monkeypatch.setenv('OPENAI_API_KEY','test-placeholder')
    with patch('qualityops.ai.urlopen',side_effect=TimeoutError):
        result=explain(f,'설명')
    assert result['mode']=='규칙 기반 분석'
    assert 'warning' in result


def test_inspection_re_submission_and_dedup(c):
    d=c.scenario('rejected');c.role('품질위원회');decision(c,d['approvals'][0]['id'],'거절')
    c.role('품질팀')
    payload={'inspection_id':'SIM-QC-RETEST','qty_affected':10,'defect_confirmed':True,'non_overlapping':True,'basis':'추가 비중복 시연 검사'}
    result=c.post(f"/api/claims/{d['claim']['id']}/inspection",payload)
    assert result['result']['confirmed_qty']==d['analyses'][0]['result']['confirmed_qty']+10
    assert c.detail(d['claim']['id'])['claim']['status']=='승인 대기'
    c.post(f"/api/claims/{d['claim']['id']}/inspection",payload,409)


def test_original_files_unchanged(full_catalog):
    for e in full_catalog.entries:
        assert hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()==e['sha256']


def test_concurrent_approval_single_commit(app):
    c=Client(app);d=c.scenario();aid=d['approvals'][0]['id']
    def run(_):
        client=Client(app);client.role('품질위원회')
        return client.client.post(f'/api/approvals/{aid}/decision',json={'decision':'승인','reason':'동시 요청 검증'},headers={'X-CSRF-Token':client.csrf}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=sorted(pool.map(run,range(2)))
    assert statuses==[200,409]
    assert len([t for t in c.detail(d['claim']['id'])['tasks'] if t['department']=='영업팀'])==2


def test_all_views_and_api_reads(c):
    for path in ('/','/workspace/claims','/healthz','/api/dashboard','/api/datasets','/api/claims','/api/approvals','/api/department-tasks','/api/extensions','/api/audit-logs','/api/batches/B-02-2602-01'):
        assert c.client.get(path).status_code==200,path


def test_source_snapshot_cannot_be_updated(app):
    from sqlalchemy import update
    from sqlalchemy.exc import IntegrityError
    with app.extensions['db_sessions']() as db:
        source=db.scalar(select(Source))
        with pytest.raises(IntegrityError):
            db.execute(update(Source).where(Source.id==source.id).values(kind='tampered'))


@pytest.mark.parametrize('rate,eligible', [(9,False),(10,True),(11,True)])
def test_exact_threshold(catalog, tmp_path, monkeypatch, rate, eligible):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    batch=next(r for r in catalog.rows('batches') if r['batch_id']=='B-02-2602-01')
    batch['produced_qty']='1000000'
    rows=[r for r in catalog.rows('qc') if r['batch_id']==batch['batch_id'] and r['defect_confirmed']=='True']
    for row in rows:row['qty_affected']='0'
    rows[0]['qty_affected']=str(rate*10000)
    client=Client(create_app({'TESTING':True,'DATABASE_URL':'sqlite:///' + (tmp_path/'threshold.db').as_posix()},catalog))
    d=client.scenario()
    assert d['analyses'][0]['result']['rate_pct']==rate
    assert d['analyses'][0]['result']['recall_eligible']==eligible
    assert d['approvals'][0]['action']==('회수' if eligible else '추가 검사')


def test_process_completion_requires_no_open_tasks(c):
    d=c.scenario();c.role('품질팀')
    c.post(f"/api/claims/{d['claim']['id']}/finish",{},409)
    c.role('품질위원회');decision(c,d['approvals'][0]['id'])
    d=c.detail(d['claim']['id'])
    for task in d['tasks']:
        c.role(task['department'])
        payload={'status':'완료','reason':'모의 외부 처리 완료 확인'}
        if task['department']=='생산팀':
            payload['reply']={'normal_stock_qty':200000,'free_capacity_qty':0,'capacity_period':'2026-07 확인','existing_commitments_protected':True}
        c.post(f"/api/department-tasks/{task['id']}/update",payload)
    c.role('품질팀')
    result=c.post(f"/api/claims/{d['claim']['id']}/finish",{})
    assert result['status']=='처리 완료'
    assert c.detail(d['claim']['id'])['batch_state']['status']=='처리 완료'


def test_role_protects_department_work(c):
    d=c.scenario('missing')
    task=next(t for t in d['tasks'] if t['department']=='물류팀')
    c.role('영업팀')
    c.post(f"/api/department-tasks/{task['id']}/update",{'status':'진행','reason':'다른 부서'},403)


def test_unsafe_json_ai_response_is_rejected(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-placeholder')
    f={'conclusion':'규칙 결과','missing':[],'rate_pct':11,'produced_qty':100,'confirmed_qty':11,'recall_eligible':True}
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return json.dumps({'choices':[{'message':{'content':'{"summary": 123}'}}]}).encode()
    with patch('qualityops.ai.urlopen',return_value=Response()):
        result=explain(f,'설명')
    assert result['mode']=='규칙 기반 분석'
    assert result['summary']=='규칙 결과'
