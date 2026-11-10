from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json

from sqlalchemy import select, delete
from .models import Source, Claim, Analysis, Approval, BatchState, Task, Evidence, Audit, Plan, Setting, now, serialize
from .ai import explain

AS_OF = '2026-07-01'
ROLES = ['접수 담당', '품질위원회', '영업팀', '생산팀', '물류팀', '품질팀']


class DomainError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def number(value):
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def required(data, key, maximum=2000):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise DomainError(f'{key}: 필수 문자열이며 {maximum}자 이하여야 합니다.')
    return value.strip()


def get(session, model, identity):
    obj = session.get(model, identity)
    if not obj:
        raise DomainError('해당 자료가 없습니다.', 404)
    return obj


class Operations:
    def __init__(self, catalog):
        self.catalog = catalog
        self.index = {key: {r[field]: r for r in catalog.rows(key)} for key, field in [
            ('batches', 'batch_id'), ('customers', 'customer_id'), ('products', 'product_id')]}
        for key in self.index:
            if len(self.index[key]) != len(catalog.rows(key)):
                raise DomainError(f'{key}: 마스터 식별자가 중복되어 안전하게 연결할 수 없습니다.', 409)

    def import_sources(self, session):
        # Content snapshots are append-only and idempotent, never UPDATE original records.
        existing = {r.source: r.digest for r in session.scalars(select(Source).where(Source.row_number == 1))}
        for key, rows in self.catalog.tables.items():
            source = self.catalog.sources[key]
            digest = next(e['sha256'] for e in self.catalog.entries if e['path'] == source)
            if source in existing:
                if existing[source] != digest:
                    raise DomainError('원본 파일이 기존 스냅샷과 다릅니다. 별도 DB에서 버전을 검증하세요.', 409)
                continue
            session.add_all([Source(source=source, row_number=i, digest=digest, kind=key, data=row) for i, row in enumerate(rows, 1)])

    def audit(self, session, claim, actor, action, before, after, reason, basis=None, task_id=None):
        session.add(Audit(claim_id=claim.id if claim else None, batch_id=claim.batch_id if claim else None,
                          actor=actor, action=action, before=before, after=after, reason=reason,
                          basis=basis or {}, task_id=task_id))

    def transition(self, session, claim, status, actor, reason, basis=None):
        old = claim.status
        claim.status = status
        self.audit(session, claim, actor, '상태 변경', old, status, reason, basis)

    def batch(self, session, batch_id):
        state = session.get(BatchState, batch_id)
        if not state:
            state = BatchState(batch_id=batch_id, status='정상')
            session.add(state)
            session.flush()
        return state

    def task(self, session, claim, department, title, key, details=None, priority='보통', status='대기'):
        found = session.scalar(select(Task).where(Task.dedupe_key == key))
        if found:
            return found
        task = Task(claim_id=claim.id, batch_id=claim.batch_id, department=department, title=title,
                    dedupe_key=key, details=details or {}, priority=priority, status=status)
        session.add(task)
        session.flush()
        self.audit(session, claim, 'SYSTEM', '부서 업무 생성', None, status, title, details, task.id)
        return task

    def create_claim(self, session, data, actor, demo=False):
        batch_id = required(data, 'batch_id', 80)
        batch = self.index['batches'].get(batch_id)
        if not batch:
            raise DomainError('batch_id: 실제 생산 배치가 존재하지 않습니다.', 404)
        customer = required(data, 'customer_id', 80)
        if customer not in self.index['customers']:
            raise DomainError('customer_id: 고객 마스터에 없습니다.')
        if data.get('product_id') != batch['product_id']:
            raise DomainError('product_id: 선택 배치의 제품과 일치하지 않습니다.')
        occurred = required(data, 'occurred_on', 10)
        try:
            date.fromisoformat(occurred)
        except ValueError:
            raise DomainError('occurred_on: YYYY-MM-DD 날짜를 입력하세요.')
        if occurred < batch['production_date']:
            raise DomainError('발생일이 배치 생산일보다 빠릅니다. 식별자·날짜를 확인하세요.')
        evidence = data.get('evidence_present', False)
        if not isinstance(evidence, bool):
            raise DomainError('evidence_present: 참/거짓 값이 필요합니다.')
        claim = Claim(customer_id=customer, product_id=batch['product_id'], batch_id=batch_id,
                      claim_type=required(data, 'claim_type', 100), occurred_on=occurred,
                      description=required(data, 'description'), reporter=actor, evidence_present=evidence,
                      status='신규 접수', is_demo=demo)
        session.add(claim)
        session.flush()
        self.batch(session, batch_id)
        self.audit(session, claim, actor, '클레임 접수', None, claim.status, claim.description,
                   {'source': '신규 운영 입력 · 확정 검사 아님', 'is_demo': demo})
        return claim

    def facts(self, session, claim):
        cat = self.catalog
        batch = self.index['batches'].get(claim.batch_id)
        missing, conflicts = [], []
        if not batch:
            raise DomainError('생산 배치 연결을 확인할 수 없습니다.', 409)
        produced = number(batch.get('produced_qty'))
        if produced is None or produced <= 0:
            missing.append('배치 생산 수량이 없거나 0 — 불량률 계산 불가')
        qc = [r for r in cat.rows('qc') if r['batch_id'] == claim.batch_id]
        confirmed_rows = [r for r in qc if str(r['defect_confirmed']).lower() == 'true']
        for row in qc:
            if row['product_id'] != claim.product_id or row['claim_date'] < batch['production_date']:
                conflicts.append('검사 레코드 제품·날짜 충돌: ' + row['claim_id'])
        confirmed = sum((number(r['qty_affected']) or Decimal(0) for r in confirmed_rows), Decimal(0)) if confirmed_rows else None
        additional = list(session.scalars(select(Evidence).where(Evidence.claim_id == claim.id, Evidence.kind == 'inspection_reply')))
        confirmed_extra = [e for e in additional if e.payload['defect_confirmed']]
        if confirmed_extra:
            confirmed = (confirmed or Decimal(0)) + sum((number(e.payload['qty_affected']) for e in confirmed_extra), Decimal(0))
        if any(number(r['qty_affected']) is None or number(r['qty_affected']) < 0 for r in confirmed_rows):
            confirmed = None
            conflicts.append('확정 불량 수량 형식 오류')
        if confirmed is None:
            missing.append('확정 검사 수량 확인 필요 — 클레임 주장은 확정 수량에 미포함')
        links = [dict(r) for r in cat.rows('links') if r['batch_id'] == claim.batch_id]
        evidence = list(session.scalars(select(Evidence).where(Evidence.claim_id == claim.id).order_by(Evidence.id)))
        trace_events = [e for e in evidence if e.kind in ('trace_gap', 'trace_reply')]
        trace_overlay = trace_events[-1] if trace_events else None
        simulated_gap = trace_overlay is not None and trace_overlay.kind == 'trace_gap'
        if simulated_gap:
            # A demo event masks routing only; raw shipments and quantities remain unchanged.
            for row in links:
                row['customer_id'] = 'NONE'
        if trace_overlay is not None and trace_overlay.kind == 'trace_reply':
            for row in links:
                if row['shipment_id'] in trace_overlay.payload['mapping']:
                    row['customer_id'] = trace_overlay.payload['mapping'][row['shipment_id']]
        if not links:
            missing.append('배치 출하 기록 없음 — 출하 고객 범위 확정 불가')
        valid_qty, shipped = Decimal(0), Decimal(0)
        customers = defaultdict(int)
        for row in links:
            qty = number(row['shipped_qty'])
            valid_date = True
            try:
                date.fromisoformat(row['ship_date'])
                valid_date = row['ship_date'] >= batch['production_date'] and row['ship_date'] >= row['order_date']
            except ValueError:
                valid_date = False
            if qty is None or qty < 0 or row['product_id'] != claim.product_id or not valid_date:
                conflicts.append('출하 수량·제품·날짜 충돌: ' + row['shipment_id'])
                continue
            shipped += qty
            if row['customer_id'] in self.index['customers']:
                valid_qty += qty
                customers[row['customer_id']] += int(qty)
        coverage = float(valid_qty / shipped * 100) if shipped > 0 else None
        if coverage is None or coverage < 100:
            missing.append('일부 또는 전체 출하 고객사 미확인 — 물류 회신 필요')
        if produced and produced > 0 and shipped > produced:
            conflicts.append('배치 출하 합계가 생산 수량을 초과함')
        if produced and confirmed is not None and confirmed > produced:
            conflicts.append('확정 불량 합계가 생산 수량을 초과함 — 중복 검사 확인 필요')
        rate = float(confirmed / produced * 100) if confirmed is not None and produced and produced > 0 else None
        eligible = rate is not None and rate >= 10 and not conflicts
        trace_ready = coverage == 100 and bool(links) and not conflicts
        policy = cat.document('# quality_policy')
        definitions = cat.document('# calculation_definitions')
        authority = cat.document('# approval_authority_policy')
        policy_verified = bool(policy and '10%' in policy[1] and '품질위원회' in policy[1] and definitions and authority)
        if not policy_verified:
            missing.append('품질 정책·수식·승인권한 원문 확인 필요')
        state = session.get(BatchState, claim.batch_id)
        existing_recall = bool(state and state.recall_approved)
        related = list(session.scalars(select(Claim).where(Claim.batch_id == claim.batch_id)))
        conclusion = ('기존 회수 승인에 연결 — 중복 회수 실행하지 않음' if existing_recall else
                      '회수 요건 충족 — 품질위원회 의결 필요' if eligible else
                      '확정 검사·분모 검증 필요' if rate is None or conflicts else '회수 기준 미달 — 조사·재검사 검토')
        missing += conflicts
        return {'batch_id': claim.batch_id, 'product_id': claim.product_id, 'produced_qty': float(produced) if produced is not None else None,
                'confirmed_qty': float(confirmed) if confirmed is not None else None, 'rate_pct': rate,
                'formula': '확정 검사 qty_affected 합 / 배치 produced_qty × 100',
                'threshold_pct': 10, 'recall_eligible': eligible and policy_verified,
                'trace_ready': trace_ready, 'trace_coverage_pct': coverage, 'known_customer_qty': float(valid_qty),
                'shipped_qty': float(shipped), 'unreconciled_qty': float(produced - shipped) if produced is not None else None,
                'inventory_note': '생산−출하 차이는 재고 확정값이 아님. Corevia 정상 재고 확인 필요. Masil 재고를 대체 재고로 전용하지 않음.',
                'customers': [{'customer_id': k, 'name': self.index['customers'][k]['customer_name'], 'qty': v} for k, v in customers.items()],
                'missing': missing, 'conflicts': conflicts, 'existing_recall': existing_recall, 'conclusion': conclusion,
                'risk': '높음' if eligible else '확인 필요' if missing else '보통', 'batch': batch,
                'policy': {'rule': '확정 불량률 ≥ 10% + 품질위원회 의결. 원인 조사는 별도 트랙. 언론 보도는 회수 근거가 아님.',
                           'source': policy[0] if policy else None, 'definition_source': definitions[0] if definitions else None,
                           'authority_source': authority[0] if authority else None},
                'sources': [cat.reference('batches', batch)] + [cat.reference('qc', r) for r in qc] + [cat.reference('links', r) for r in cat.rows('links') if r['batch_id'] == claim.batch_id],
                'related_claim_ids': [c.id for c in related], 'original_claim_count': len(qc),
                'assumptions': ['확정 검사 합산은 원문 수식 준수. 동일 물품 중복 여부는 검사 ID 기준만 검증 가능.',
                    '추가 검사 회신은 품질팀의 비중복 확인을 받은 시연 입력이며 원본 검사와 별도 표시.',
                    'SBL 출하추적과 SH 매출출하의 식별자는 별도 체계 — 주문을 배치에 임의 귀속하지 않음.'],
                'evidence': [serialize(e) for e in evidence]}

    def analyze(self, session, claim_id, actor):
        claim = get(session, Claim, claim_id)
        if claim.status == '처리 완료':
            raise DomainError('종료된 클레임은 재분석할 수 없습니다. 신규 접수하세요.', 409)
        self.transition(session, claim, '데이터 확인 중', 'SYSTEM', '실제 원본·운영 이력 조회')
        facts = self.facts(session, claim)
        commentary = explain(facts, claim.description)
        facts['ai'] = commentary
        analysis = Analysis(claim_id=claim.id, result=facts, mode=commentary['mode'])
        session.add(analysis)
        session.flush()
        # Re-analysis supersedes unresolved requests. Decisions are immutable.
        for approval in session.scalars(select(Approval).where(Approval.claim_id == claim.id, Approval.status.in_(['대기', '보류', '추가 정보 요청']))):
            approval.status = '재분석으로 대체'
        state = self.batch(session, claim.batch_id)
        if facts['existing_recall']:
            status = '원인 조사' if state.status == '처리 완료' else '회수 진행'
            self.transition(session, claim, status, 'SYSTEM', '기존 회수 승인 이력에 연결; 중복 회수하지 않음', {'approval_id': state.approval_id})
            self.task(session, claim, '품질팀', '회수 중 추가 클레임 확인', f'follow:{claim.id}', {'existing_approval': state.approval_id}, '높음')
        elif facts['missing']:
            self.transition(session, claim, '정보 확인 필요', 'SYSTEM', '처리 가능한 계산은 저장; 미확인 범위 실행 보류', {'missing': facts['missing']})
            if facts['recall_eligible']:
                state.shipment_hold = True  # temporary precaution, not recall execution
            if not facts['trace_ready']:
                self.task(session, claim, '물류팀', '출하 고객사·수량·날짜 확인', f'trace:{claim.id}:{analysis.id}',
                          {'missing': facts['missing'], 'links': [r for r in self.catalog.rows('links') if r['batch_id'] == claim.batch_id]}, '높음')
            if facts['rate_pct'] is None or facts['conflicts']:
                self.task(session, claim, '품질팀', '확정 검사·기준 수량 확인', f'qc:{claim.id}:{analysis.id}', {'missing': facts['missing']}, '높음')
        else:
            self.transition(session, claim, 'AI 분석 완료', commentary['mode'], facts['conclusion'], {'analysis_id': analysis.id})
            action = '회수' if facts['recall_eligible'] else '추가 검사'
            session.add(Approval(claim_id=claim.id, analysis_id=analysis.id, action=action))
            self.transition(session, claim, '승인 대기', 'SYSTEM', '품질위원회 심사 요청', {'analysis_id': analysis.id})
        self.detect_repeat(session, claim)
        return analysis

    def detect_repeat(self, session, claim):
        end = date.fromisoformat(claim.occurred_on)
        start = (end - timedelta(days=30)).isoformat()
        original = [r for r in self.catalog.rows('qc') if r['product_id'] == claim.product_id and r['claim_type'] == claim.claim_type and start <= r['claim_date'] <= claim.occurred_on]
        current = list(session.scalars(select(Claim).where(Claim.product_id == claim.product_id, Claim.claim_type == claim.claim_type,
                    Claim.occurred_on >= start, Claim.occurred_on <= claim.occurred_on)))
        batches = set([r['batch_id'] for r in original] + [r.batch_id for r in current])
        count = len(original) + len(current)
        previous_start = (end - timedelta(days=61)).isoformat()
        previous = len([r for r in self.catalog.rows('qc') if r['product_id'] == claim.product_id and r['claim_type'] == claim.claim_type and previous_start <= r['claim_date'] < start])
        by_customer = Counter([r['customer_id'] for r in original] + [r.customer_id for r in current])
        details = {'count': count, 'previous_count': previous, 'batch_count': len(batches), 'batches': sorted(batches),
                   'window': [start, claim.occurred_on], 'customer_counts': dict(by_customer),
                   'rule': '시연 정책: 최근 31일 동일 제품·동일 유형 3건 이상. 다배치·고객 반복도 표시. 회수 자동 승인 아님.'}
        if count >= 3:
            self.task(session, claim, '품질팀', '반복 품질 이슈 조기 경보·추가 검사', f'repeat:{claim.product_id}:{claim.claim_type}:{start}', details, '높음')
        return details

    def evidence(self, session, claim_id, data, actor):
        claim = get(session, Claim, claim_id)
        kind = required(data, 'kind', 40)
        if kind not in ('news', 'note', 'trace_gap'):
            raise DomainError('허용된 증빙 유형이 아닙니다.')
        if kind == 'trace_gap' and not claim.is_demo:
            raise DomainError('추적 누락 모의 이벤트는 시연 클레임에만 적용합니다.', 409)
        session.add(Evidence(claim_id=claim.id, kind=kind, payload={'text': required(data, 'text')}, actor=actor, is_simulated=True))
        session.flush()
        self.audit(session, claim, actor, '조건 변경 입력', claim.status, claim.status, '모의 회신·추가 정보. 확정 불량 수량 변경 없음.', {'kind': kind})
        if kind == 'news':
            self.task(session, claim, '품질팀', '언론 보도 사실 확인 및 조사 우선순위 상향', f'news:{claim.id}', {'is_simulated': True}, '긴급')
        return self.analyze(session, claim.id, actor)

    def inspection(self, session, claim_id, data, role, actor):
        if role != '품질팀':
            raise DomainError('품질팀만 검사 결과를 확인할 수 있습니다.', 403)
        claim = get(session, Claim, claim_id)
        inspection_id = required(data, 'inspection_id', 80)
        quantity = number(data.get('qty_affected'))
        if quantity is None or quantity < 0 or quantity != quantity.to_integral_value():
            raise DomainError('검사 수량은 0 이상의 정수여야 합니다.')
        if data.get('non_overlapping') is not True or not isinstance(data.get('defect_confirmed'), bool):
            raise DomainError('원본 검사와 비중복 확인 및 확정 여부가 필요합니다.')
        for e in session.scalars(select(Evidence).where(Evidence.kind == 'inspection_reply')):
            if e.payload['inspection_id'] == inspection_id:
                raise DomainError('같은 검사 ID는 한 번만 반영할 수 있습니다.', 409)
        if any(r['claim_id'] == inspection_id for r in self.catalog.rows('qc')):
            raise DomainError('원본 검사 ID와 중복됩니다.', 409)
        payload = {'inspection_id': inspection_id, 'qty_affected': int(quantity), 'defect_confirmed': data['defect_confirmed'],
                   'non_overlapping': True, 'basis': required(data, 'basis')}
        session.add(Evidence(claim_id=claim.id, kind='inspection_reply', payload=payload, actor=actor, is_simulated=True))
        session.flush()
        self.audit(session, claim, actor, '추가 검사 회신', None, '품질 확인', '원본과 별도 관리하는 시연 검사 결과', payload)
        return self.analyze(session, claim.id, actor)

    def decide(self, session, approval_id, data, role, actor):
        if role != '품질위원회':
            raise DomainError('품질위원회 역할만 의결할 수 있습니다.', 403)
        approval = get(session, Approval, approval_id)
        if approval.status not in ('대기', '보류'):
            raise DomainError('이미 결정되었거나 대체된 요청입니다. 중복 실행하지 않습니다.', 409)
        reason = required(data, 'reason')
        decision = required(data, 'decision', 40)
        if decision not in ('승인', '거절', '추가 정보 요청', '보류'):
            raise DomainError('승인·거절·추가 정보 요청·보류 중 선택하세요.')
        claim = get(session, Claim, approval.claim_id)
        if actor == claim.reporter:
            raise DomainError('접수자와 승인자는 구분해야 합니다. 시연용 역할과 이름을 바꾸세요.', 403)
        snapshot = get(session, Analysis, approval.analysis_id).result
        current = self.facts(session, claim)
        if decision == '승인':
            if current['existing_recall'] and approval.action == '회수':
                raise DomainError('동일 배치는 이미 회수가 승인됐습니다.', 409)
            if current['missing'] or not current['trace_ready'] or (approval.action == '회수' and not current['recall_eligible']):
                raise DomainError('최신 자료가 실행 요건을 충족하지 않습니다. 재분석이 필요합니다.', 409)
            if any(current[k] != snapshot[k] for k in ('confirmed_qty', 'produced_qty', 'shipped_qty', 'trace_coverage_pct')):
                raise DomainError('심사 자료 이후 수치가 변경됐습니다. 재분석하세요.', 409)
        approval.status, approval.reason, approval.decided_by, approval.decided_at = decision, reason, actor, now()
        state = self.batch(session, claim.batch_id)
        self.transition(session, claim, decision, actor, reason, {'approval_id': approval.id, 'analysis_id': approval.analysis_id})
        if decision == '승인' and approval.action == '회수':
            state.recall_approved, state.shipment_hold, state.status, state.approval_id = True, True, '회수 진행', approval.id
            self.transition(session, claim, '회수 진행', 'SYSTEM', '품질위원회 승인에 따른 내부 회수 절차 개시', {'approval_id': approval.id})
            for title in ('고객사 안내 및 영향 범위 확인', '납품 일정 재검토·대체 공급 협의'):
                self.task(session, claim, '영업팀', title, f'recall:{claim.batch_id}:영업:{title}', {'customers': current['customers'], 'shipped_qty': current['shipped_qty']}, '긴급')
            self.task(session, claim, '생산팀', '재공급 요청·정상 재고·가용 생산능력 확인', f'recall:{claim.batch_id}:생산',
                      {'required_qty': current['shipped_qty'], 'capacity': [r for r in self.catalog.rows('capacity') if r['product_id'] == claim.product_id],
                       'constraint': '생산능력 기간·확정 예약·정상 재고 확인 전 공급 가능 확정 금지'}, '긴급')
            self.task(session, claim, '품질팀', '회수와 별도 원인 조사', f'recall:{claim.batch_id}:조사', {'confirmed_qty': current['confirmed_qty']}, '높음')
            self.recovery_plan(session, claim, current)
        elif decision in ('거절', '승인'):
            if not state.recall_approved:
                state.status = '원인 조사'
            self.transition(session, claim, '원인 조사', 'SYSTEM', '회수 미실행. 원인 조사·재검사로 후속 처리')
            self.task(session, claim, '품질팀', '거절 사유 확인·원인 조사·재검사' if decision == '거절' else '추가 검사 실행',
                      f'investigate:{approval.id}', {'reason': reason}, '높음')
        elif decision == '추가 정보 요청':
            self.transition(session, claim, '정보 확인 필요', 'SYSTEM', reason)
            self.task(session, claim, '품질팀', '위원회 추가 정보 요청 회신', f'question:{approval.id}', {'reason': reason}, '높음')
        state.updated_at = now()
        return approval

    def recovery_plan(self, session, claim, facts, reply=None):
        plan = session.scalar(select(Plan).where(Plan.batch_id == claim.batch_id))
        policy = session.get(Setting, 'priority')
        priority = (policy.data if policy else {'method': '출하 수량 우선'})
        customers = sorted(facts['customers'], key=lambda r: (-r['qty'], r['customer_id']))
        if priority.get('method') == '고객 코드 순':
            customers.sort(key=lambda r: r['customer_id'])
        confirmed = reply or {}
        required_qty = facts['shipped_qty']
        stock = confirmed.get('normal_stock_qty')
        capacity = confirmed.get('free_capacity_qty')
        available = stock + capacity if stock is not None and capacity is not None else None
        shortage = max(required_qty - available, 0) if available is not None else None
        remaining = available
        allocations = []
        for customer in customers:
            allocated = min(customer['qty'], remaining) if remaining is not None else None
            allocations.append(dict(customer, allocated_qty=allocated, shortage_qty=customer['qty'] - allocated if allocated is not None else None))
            if remaining is not None:
                remaining -= allocated
        status = '생산 여력 확인 필요' if available is None else '공급 부족·납품 협의 필요' if shortage else '재공급 계획 검토 가능'
        data = {'required_qty': required_qty, 'normal_stock_qty': stock, 'free_capacity_qty': capacity,
                'shortage_qty': shortage, 'allocations': allocations, 'priority_policy': priority, 'reply': reply,
                'delivery_note': '원본 수주에는 납기일 컬럼이 없음. 실제 납기·가용 여력·예약 약속을 담당자 회신으로 검증. 주문-배치 직접 연결 미확인.',
                'capacity_context': [r for r in self.catalog.rows('capacity') if r['product_id'] == claim.product_id],
                'is_simulated': reply is not None}
        if plan:
            plan.status, plan.data, plan.updated_at = status, data, now()
        else:
            plan = Plan(batch_id=claim.batch_id, claim_id=claim.id, status=status, data=data)
            session.add(plan)
        for sales in session.scalars(select(Task).where(Task.batch_id == claim.batch_id, Task.department == '영업팀', Task.status != '완료')):
            sales.details = dict(sales.details, recovery=data)
        self.audit(session, claim, 'SYSTEM', '재공급 계획 재계산', None, status, '확정된 기존 고객 약속을 차감한 가용량 기준', data)
        return plan

    def update_task(self, session, task_id, data, role, actor):
        task = get(session, Task, task_id)
        if role != task.department:
            raise DomainError(f'{task.department} 역할만 이 업무를 처리할 수 있습니다.', 403)
        claim = get(session, Claim, task.claim_id)
        old = task.status
        status = required(data, 'status', 40)
        if status not in ('진행', '보류', '완료') or task.status == '완료':
            raise DomainError('허용되지 않은 상태 변경 또는 완료 업무의 중복 처리입니다.', 409)
        reason = required(data, 'reason')
        reply = data.get('reply')
        if role == '물류팀' and status == '완료':
            if not isinstance(reply, dict) or not isinstance(reply.get('mapping'), dict):
                raise DomainError('출하 기록별 고객 코드 mapping 회신이 필요합니다.')
            links = {r['shipment_id']: r for r in self.catalog.rows('links') if r['batch_id'] == task.batch_id}
            if set(reply['mapping']) != set(links) or not links:
                raise DomainError('실제 배치 출하 기록 전체를 확인해야 합니다. 없는 출하를 만들 수 없습니다.')
            if any(v not in self.index['customers'] for v in reply['mapping'].values()):
                raise DomainError('회신 고객이 원본 고객 마스터에 없습니다.')
            # Do not allow a demonstration reply to contradict a known source customer.
            if any(r['customer_id'] in self.index['customers'] and reply['mapping'][k] != r['customer_id'] for k, r in links.items()):
                raise DomainError('회신이 원본의 알려진 고객사와 충돌합니다.')
            session.add(Evidence(claim_id=claim.id, kind='trace_reply', payload=reply, actor=actor, is_simulated=True))
        if role == '생산팀' and status == '완료':
            if not isinstance(reply, dict):
                raise DomainError('정상 재고·순가용 여력과 기간·약속 보호 확인 회신이 필요합니다.')
            for key in ('normal_stock_qty', 'free_capacity_qty'):
                value = reply.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or number(value) is None or value < 0 or value > 10**9:
                    raise DomainError(key + ': 0 이상 유한 수량이 필요합니다.')
            if reply.get('existing_commitments_protected') is not True or not reply.get('capacity_period'):
                raise DomainError('기존 고객 약속 차감 여부와 여력의 적용 기간을 확인하세요.')
            self.recovery_plan(session, claim, self.facts(session, claim), reply)
            # Capacity shortages change actual sales task priority and content.
            plan = session.scalar(select(Plan).where(Plan.batch_id == task.batch_id))
            for sales in session.scalars(select(Task).where(Task.batch_id == task.batch_id, Task.department == '영업팀', Task.status != '완료')):
                sales.details = dict(sales.details, recovery=plan.data)
                sales.priority = '긴급' if plan.data['shortage_qty'] else '높음'
                self.audit(session, claim, 'SYSTEM', '영업 대안 갱신', sales.status, sales.status, plan.status, plan.data, sales.id)
            if plan.data['shortage_qty'] > 0:
                self.task(session, claim, '생산팀', '공급 부족 해소·생산 일정 재검토', f'capacity-shortage:{task.batch_id}:{task.id}',
                          {'shortage_qty': plan.data['shortage_qty'], 'required_qty': plan.data['required_qty'],
                           'constraint': '기존 고객 약속을 보호한 신규 회신 필요'}, '긴급')
        task.status, task.reply, task.updated_at = status, {'reason': reason, 'data': reply, 'is_simulated': True}, now()
        self.audit(session, claim, actor, '부서 업무 회신', old, status, reason, task.reply, task.id)
        session.flush()
        if role == '물류팀' and status == '완료':
            self.analyze(session, claim.id, actor)
        return task

    def finish(self, session, claim_id, actor):
        claim = get(session, Claim, claim_id)
        if claim.status == '처리 완료':
            raise DomainError('이미 종료됐습니다.', 409)
        pending = list(session.scalars(select(Task).where(Task.batch_id == claim.batch_id, Task.status != '완료')))
        if pending or claim.status not in ('회수 진행', '원인 조사'):
            raise DomainError('승인·조사 단계와 모든 배치 후속 업무 완료를 먼저 확인하세요.', 409)
        plan = session.scalar(select(Plan).where(Plan.batch_id == claim.batch_id))
        if plan and (plan.data.get('shortage_qty') is None or plan.data.get('shortage_qty') > 0):
            raise DomainError('재공급 부족 또는 여력 미확인 상태에서는 종료할 수 없습니다.', 409)
        self.transition(session, claim, '처리 완료', actor, '배치 후속 업무 및 재공급 요건 확인')
        others = list(session.scalars(select(Claim).where(Claim.batch_id == claim.batch_id, Claim.id != claim.id, Claim.status != '처리 완료')))
        if not others:
            state = self.batch(session, claim.batch_id)
            state.status, state.updated_at = '처리 완료', now()
        return claim
