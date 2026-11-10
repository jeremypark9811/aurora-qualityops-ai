from __future__ import annotations

import os
import secrets
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session, g
from sqlalchemy import select, text, delete
from werkzeug.exceptions import HTTPException

from qualityops.catalog import Catalog
from qualityops.models import (database, Claim, Analysis, Approval, BatchState, Task, Evidence,
                               Audit, Plan, Setting, serialize)
from qualityops.service import Operations, DomainError, ROLES, get, required, AS_OF

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


def create_app(config=None, catalog=None):
    app = Flask(__name__)
    instance = ROOT / 'instance'
    instance.mkdir(exist_ok=True)
    secret_file = instance / 'session.key'
    if not secret_file.exists():
        secret_file.write_text(secrets.token_hex(32), encoding='ascii')
    app.config.update(SECRET_KEY=os.getenv('SESSION_SECRET') or secret_file.read_text(encoding='ascii'),
                      DATABASE_URL=os.getenv('QUALITYOPS_DATABASE_URL', 'sqlite:///' + (instance / 'qualityops.db').as_posix()),
                      MAX_CONTENT_LENGTH=128 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      DEMO_MODE=True)
    if config:
        app.config.update(config)
    catalog = catalog or Catalog(ROOT)
    ops = Operations(catalog)
    engine, sessions = database(app.config['DATABASE_URL'])
    app.extensions.update(catalog=catalog, ops=ops, db_engine=engine, db_sessions=sessions)
    with sessions.begin() as db:
        ops.import_sources(db)

    @app.before_request
    def begin():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(24)
        if 'role' not in session:
            session['role'], session['actor'] = '접수 담당', '접수 담당자'
        if request.method == 'POST':
            if not request.is_json:
                raise DomainError('JSON 요청이 필요합니다.', 415)
            if not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), session['csrf']):
                raise DomainError('보안 토큰이 만료됐습니다. 새로고침하세요.', 403)
            if request.headers.get('Sec-Fetch-Site') == 'cross-site':
                raise DomainError('다른 사이트에서의 상태 변경은 허용하지 않습니다.', 403)
        g.db = sessions()
        if request.method == 'POST':
            # Serialize read/check/write as one SQLite transaction to prevent double approvals.
            g.db.execute(text('BEGIN IMMEDIATE'))

    @app.after_request
    def end(response):
        if hasattr(g, 'db'):
            if response.status_code < 400:
                g.db.commit()
            else:
                g.db.rollback()
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.teardown_request
    def close(error):
        if hasattr(g, 'db'):
            if error:
                g.db.rollback()
            g.db.close()

    @app.errorhandler(DomainError)
    def domain_error(error):
        return jsonify(error=str(error)), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error='요청 경로·형식·크기를 확인하세요.'), error.code

    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.exception('QualityOps request failed')
        return jsonify(error='처리 중 오류가 발생했습니다. 변경 내용은 저장되지 않았습니다.'), 500

    def identity(allowed=None):
        role, actor = session['role'], session['actor']
        if allowed and role not in allowed:
            raise DomainError('이 작업의 담당 역할로 전환하세요.', 403)
        return role, actor

    def data():
        value = request.get_json()
        if not isinstance(value, dict):
            raise DomainError('JSON 객체가 필요합니다.')
        return value

    @app.get('/')
    @app.get('/workspace/<section>')
    def index(section='dashboard'):
        return render_template('index.html', csrf=session['csrf'])

    @app.get('/healthz')
    def health():
        return jsonify(status='ok')

    @app.get('/api/bootstrap')
    def bootstrap():
        return jsonify(role=session['role'], actor=session['actor'], roles=ROLES, csrf=session['csrf'],
                       as_of=AS_OF, demo_mode=True, llm_configured=bool(os.getenv('OPENAI_API_KEY')),
                       products=catalog.rows('products'), customers=catalog.rows('customers'),
                       batches=catalog.rows('batches'), sources=catalog.sources,
                       priority=(g.db.get(Setting, 'priority').data if g.db.get(Setting, 'priority') else {'method': '출하 수량 우선'}))

    @app.post('/api/role')
    def role():
        payload = data()
        role_name, actor = required(payload, 'role', 40), required(payload, 'actor', 80)
        if role_name not in ROLES:
            raise DomainError('알 수 없는 역할입니다.')
        session['role'], session['actor'] = role_name, actor
        ops.audit(g.db, None, actor, '시연용 역할 전환', None, role_name, '실제 기업 인증이 아닌 모의 권한')
        return jsonify(role=role_name, actor=actor)

    @app.get('/api/dashboard')
    def dashboard():
        claims = list(g.db.scalars(select(Claim).order_by(Claim.id.desc())))
        tasks = list(g.db.scalars(select(Task)))
        statuses = Counter(c.status for c in claims)
        timeline = Counter(c.occurred_on[:7] for c in claims)
        original = Counter(r['claim_date'][:7] for r in catalog.rows('qc'))
        return jsonify(kpis={'전체 클레임': len(claims), '승인 대기': sum(1 for a in g.db.scalars(select(Approval)) if a.status in ('대기', '보류')),
                             '정보 확인 필요': statuses['정보 확인 필요'], '회수 진행': sum(1 for s in g.db.scalars(select(BatchState)) if s.recall_approved and s.status != '처리 완료'),
                             '처리 완료': statuses['처리 완료'], '후속 작업': len(tasks)},
                       original_claim_count=len(catalog.rows('qc')), recent=[serialize(c) for c in claims[:8]],
                       trend=[{'month': k, 'original': original[k], 'operations': timeline[k]} for k in sorted(set(original) | set(timeline))],
                       warnings=[serialize(t) for t in tasks if t.priority in ('높음', '긴급') and t.status != '완료'][:8],
                       status_counts=dict(statuses), source_files=len(catalog.entries), batch_count=len(catalog.rows('batches')))

    @app.get('/api/datasets')
    def datasets():
        query = request.args.get('q', '').lower()
        return jsonify(items=[e for e in catalog.entries if query in str(e).lower()], sources=catalog.sources,
                       notice='파일명과 내용 불일치 발견. 실제 헤더로 식별했으며 원본 바이트는 보존했습니다.')

    @app.get('/api/documents/<name>')
    def documents(name):
        allowed = {p.name for p in (ROOT / 'docs').glob('*.md')}
        if name not in allowed:
            raise DomainError('허용된 문서가 아닙니다.', 404)
        return jsonify(name=name, content=(ROOT / 'docs' / name).read_text(encoding='utf-8'))

    @app.get('/api/claims')
    def claims():
        items = list(g.db.scalars(select(Claim).order_by(Claim.id.desc())))
        for key in ('status', 'product_id', 'customer_id', 'batch_id'):
            if request.args.get(key):
                items = [c for c in items if getattr(c, key) == request.args[key]]
        if request.args.get('from'):
            items = [c for c in items if c.occurred_on >= request.args['from']]
        if request.args.get('to'):
            items = [c for c in items if c.occurred_on <= request.args['to']]
        output = []
        for claim in items:
            latest = g.db.scalar(select(Analysis).where(Analysis.claim_id == claim.id).order_by(Analysis.id.desc()))
            risk = latest.result['risk'] if latest else '미분석'
            if request.args.get('risk') and request.args['risk'] != risk:
                continue
            output.append(dict(serialize(claim), risk=risk))
        return jsonify(items=output)

    @app.get('/api/batches/<batch_id>')
    def batch_detail(batch_id):
        batch = ops.index['batches'].get(batch_id)
        if not batch:
            raise DomainError('생산 배치가 없습니다.', 404)
        references = [catalog.reference('batches', batch)]
        references += [catalog.reference('qc', r) for r in catalog.rows('qc') if r['batch_id'] == batch_id]
        references += [catalog.reference('links', r) for r in catalog.rows('links') if r['batch_id'] == batch_id]
        state = g.db.get(BatchState, batch_id)
        return jsonify(batch=batch, state=serialize(state) if state else None, sources=references,
                       claims=[serialize(c) for c in g.db.scalars(select(Claim).where(Claim.batch_id == batch_id))],
                       capacity=[r for r in catalog.rows('capacity') if r['product_id'] == batch['product_id']],
                       unknown=['Corevia 정상 완제품 재고', '주문 납기와 배치 직접 연결', '일자별 순가용 생산량'])

    @app.post('/api/claims')
    def create_claim():
        _, actor = identity(['접수 담당', '품질팀'])
        return jsonify(serialize(ops.create_claim(g.db, data(), actor))), 201

    def detail(claim_id):
        claim = get(g.db, Claim, claim_id)
        analyses = list(g.db.scalars(select(Analysis).where(Analysis.claim_id == claim_id).order_by(Analysis.id.desc())))
        state = ops.batch(g.db, claim.batch_id)
        inherited = g.db.get(Approval, state.approval_id) if state.approval_id else None
        return {'claim': serialize(claim), 'analyses': [serialize(a) for a in analyses],
                'inherited_approval': serialize(inherited) if inherited and inherited.claim_id != claim_id else None,
                'approvals': [serialize(a) for a in g.db.scalars(select(Approval).where(Approval.claim_id == claim_id).order_by(Approval.id.desc()))],
                'tasks': [serialize(t) for t in g.db.scalars(select(Task).where(Task.batch_id == claim.batch_id))],
                'batch_state': serialize(state),
                'audit': [serialize(a) for a in g.db.scalars(select(Audit).where(Audit.claim_id == claim_id).order_by(Audit.id))],
                'plans': [serialize(p) for p in g.db.scalars(select(Plan).where(Plan.batch_id == claim.batch_id))]}

    @app.get('/api/claims/<int:claim_id>')
    @app.get('/api/claims/<int:claim_id>/workflow')
    def claim_detail(claim_id):
        return jsonify(detail(claim_id))

    @app.post('/api/claims/<int:claim_id>/analyze')
    def analyze(claim_id):
        _, actor = identity(['접수 담당', '품질팀'])
        return jsonify(serialize(ops.analyze(g.db, claim_id, actor)))

    @app.post('/api/claims/<int:claim_id>/new-evidence')
    def evidence(claim_id):
        _, actor = identity(['접수 담당', '품질팀'])
        return jsonify(serialize(ops.evidence(g.db, claim_id, data(), actor)))

    @app.post('/api/claims/<int:claim_id>/finish')
    def finish(claim_id):
        _, actor = identity(['품질팀'])
        return jsonify(serialize(ops.finish(g.db, claim_id, actor)))

    @app.post('/api/claims/<int:claim_id>/inspection')
    def inspection(claim_id):
        role, actor = identity(['품질팀'])
        return jsonify(serialize(ops.inspection(g.db, claim_id, data(), role, actor)))

    @app.get('/api/approvals')
    def approvals():
        return jsonify(items=[dict(serialize(a), claim=serialize(get(g.db, Claim, a.claim_id)),
                                   analysis=get(g.db, Analysis, a.analysis_id).result) for a in g.db.scalars(select(Approval).order_by(Approval.id.desc()))])

    @app.post('/api/approvals/<int:approval_id>/decision')
    def decision(approval_id):
        role, actor = identity()
        return jsonify(serialize(ops.decide(g.db, approval_id, data(), role, actor)))

    @app.get('/api/department-tasks')
    def tasks():
        items = list(g.db.scalars(select(Task).order_by(Task.id.desc())))
        if request.args.get('department'):
            items = [t for t in items if t.department == request.args['department']]
        return jsonify(items=[serialize(t) for t in items], plans=[serialize(p) for p in g.db.scalars(select(Plan))])

    @app.post('/api/department-tasks/<int:task_id>/update')
    def task_update(task_id):
        role, actor = identity()
        return jsonify(serialize(ops.update_task(g.db, task_id, data(), role, actor)))

    @app.post('/api/settings/priority')
    def priority():
        _, actor = identity(['영업팀'])
        value = required(data(), 'method', 40)
        if value not in ('출하 수량 우선', '고객 코드 순'):
            raise DomainError('지원하지 않는 우선순위입니다.')
        setting = g.db.get(Setting, 'priority')
        if not setting:
            g.db.add(Setting(key='priority', data={'method': value, 'is_assumption': True}))
        else:
            setting.data = {'method': value, 'is_assumption': True}
        g.db.flush()
        for plan in g.db.scalars(select(Plan)):
            claim = get(g.db, Claim, plan.claim_id)
            ops.recovery_plan(g.db, claim, ops.facts(g.db, claim), plan.data.get('reply'))
        ops.audit(g.db, None, actor, '시연 우선순위 변경', None, value, '공식 규정이 아닌 조정 가능한 공급 배분 가정')
        return jsonify(method=value)

    @app.get('/api/audit-logs')
    def logs():
        query = select(Audit).order_by(Audit.id.desc())
        if request.args.get('claim_id'):
            query = query.where(Audit.claim_id == request.args.get('claim_id', type=int))
        return jsonify(items=[serialize(a) for a in g.db.scalars(query.limit(500))])

    @app.get('/api/extensions')
    def extensions():
        analyses = list(g.db.scalars(select(Analysis).order_by(Analysis.id.desc())))
        latest = {}
        for a in analyses:
            latest.setdefault(a.claim_id, serialize(a))
        return jsonify(trace=list(latest.values()), alerts=[serialize(t) for t in g.db.scalars(select(Task).where(Task.dedupe_key.like('repeat:%')))],
                       definition='고객 식별·제품·날짜·수량이 유효한 출하량 / 기록된 배치 출하 총량 × 100. 전체 물류 누락률을 뜻하지 않음.')

    @app.post('/api/demo/scenario')
    def scenario():
        _, actor = identity(['접수 담당', '품질팀'])
        payload = data()
        kind = payload.get('scenario')
        if kind not in ('normal', 'changed', 'missing', 'rejected'):
            raise DomainError('시연 시나리오를 선택하세요.')
        batch_id = 'B-02-2603-01' if kind in ('missing', 'rejected') else 'B-02-2602-01'
        if batch_id not in ops.index['batches']:
            raise DomainError('시연에 필요한 실제 배치가 없습니다. 가짜 결과를 생성하지 않습니다.', 409)
        claim = ops.create_claim(g.db, {'batch_id': batch_id, 'customer_id': 'C-101', 'product_id': 'PL-02',
                    'claim_type': '피부트러블', 'occurred_on': '2026-06-30', 'description': '시연용 신규 클레임 — 실제 배치·확정 검사에 연결',
                    'evidence_present': True}, actor, demo=True)
        if kind == 'missing':
            session_event = Evidence(claim_id=claim.id, kind='trace_gap', payload={'text': '시연용 출하 고객 확인 보류. 원본은 변경하지 않음.'}, actor=actor, is_simulated=True)
            g.db.add(session_event)
            g.db.flush()
        ops.analyze(g.db, claim.id, actor)
        if kind == 'changed':
            ops.evidence(g.db, claim.id, {'kind': 'news', 'text': '시연용 언론 보도 추가 — 검사 확정 수량 변경 없음'}, actor)
        return jsonify(detail(claim.id)), 201

    @app.post('/api/demo/reset')
    def reset():
        _, actor = identity(['품질팀'])
        if data().get('confirmation') != '시연 데이터 초기화':
            raise DomainError('시연 데이터 초기화 확인 문구가 필요합니다.')
        demos = list(g.db.scalars(select(Claim).where(Claim.is_demo.is_(True))))
        # Restrict reset to demo-only batches; original source snapshot and real operations stay intact.
        ids = [c.id for c in demos]
        batch_ids = {c.batch_id for c in demos}
        for batch_id in batch_ids:
            if g.db.scalar(select(Claim).where(Claim.batch_id == batch_id, Claim.is_demo.is_(False))):
                raise DomainError('같은 배치의 실제 운영 클레임이 있어 초기화를 보류합니다. 별도 시연 DB를 사용하세요.', 409)
        for model in (Task, Plan, Evidence):
            g.db.execute(delete(model).where(model.claim_id.in_(ids)))
        for batch_id in batch_ids:
            g.db.execute(delete(BatchState).where(BatchState.batch_id == batch_id))
        g.db.execute(delete(Approval).where(Approval.claim_id.in_(ids)))
        g.db.execute(delete(Analysis).where(Analysis.claim_id.in_(ids)))
        g.db.execute(delete(Claim).where(Claim.id.in_(ids)))
        # Keep the audit trail, including reset itself.
        ops.audit(g.db, None, actor, '시연 초기화', None, None, '시연 클레임·운영 파생 자료만 초기화. 원본과 감사 이력 보존', {'claim_ids': ids})
        return jsonify(reset_count=len(ids))

    return app


if __name__ == '__main__':
    from waitress import serve
    app = create_app()
    print('Aurora QualityOps AI: http://127.0.0.1:' + os.getenv('PORT', '5000'), flush=True)
    serve(app, host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '5000')), threads=4)
