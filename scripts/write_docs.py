"""Regenerate evidence-backed documentation without changing source files."""
from pathlib import Path
from qualityops.catalog import Catalog

ROOT = Path(__file__).resolve().parents[1]


def write(name, text):
    (ROOT / 'docs' / name).write_text(text.strip() + '\n', encoding='utf-8')


def main():
    c = Catalog(ROOT)
    c.write_reports()
    relations = ['# 데이터 관계와 조인 검증', '', '파일 이름은 의미 근거가 아니다. 아래 연결은 실제 헤더·식별자·값으로 검증했다.', '',
                 '|참조 측 실제 파일 / 컬럼|마스터 측 실제 파일 / 컬럼|미연결 / 전체|마스터 키 중복|', '|---|---|---|---|']
    for src, key, target, target_key in [('qc','batch_id','batches','batch_id'),('qc','customer_id','customers','customer_id'),
            ('links','batch_id','batches','batch_id'),('links','customer_id','customers','customer_id'),
            ('batches','product_id','products','product_id'),('consumption','batch_id','batches','batch_id'),('consumption','lot_id','lots','lot_id'),
            ('shipments','order_id','orders','order_id'),('inventory','sku_id','sku','sku_id')]:
        keys = [r[target_key] for r in c.rows(target)]
        key_set = set(keys)
        unmatched = sum(r[key] not in key_set for r in c.rows(src))
        relations.append(f'|{c.sources[src]} / `{key}`|{c.sources[target]} / `{target_key}`|{unmatched} / {len(c.rows(src))}|{len(keys)-len(set(keys))}|')
    sbl = {r['shipment_id'] for r in c.rows('links')}
    sh = {r['shipment_id'] for r in c.rows('shipments')}
    relations += ['', '## 연결 미확인과 사용 제한', f'- 배치 출하 추적(SBL)과 주문 출하(SH)의 shipment_id 교집합: {len(sbl & sh)}건. 직접 연결 불가.',
                  '- 배치 출하 표에 order_id가 없다. 고객·제품이 같다는 이유로 특정 주문을 해당 배치에 연결하지 않는다.',
                  '- 배치 production_line은 F1/F2 공장 코드, 능력표 line_id는 L-xx 라인 코드다. 이름만 보고 조인하지 않는다. 능력은 제품군·공장 스냅샷 참고값으로만 표시.',
                  '- Masil SKU 재고는 Corevia 제조 정상 재고가 아니다. 공급 복구 가용량에서 제외한다.',
                  '- 주문에 납기일 컬럼 없음. 지연 일수·납기 우선순위를 원본 확정값으로 산출할 수 없다.',
                  '- 모든 분석은 배치 생산일 ≤ 검사·출하일, 출하일 ≥ 주문일, 제품 ID 일치를 검증한다. 충돌이 있으면 승인 실행 차단.']
    write('DATA_RELATIONSHIPS.md', '\n'.join(relations))
    write('DATA_LINEAGE.md', f'''# 지표별 데이터 계보

|지표|실제 원본 경로·컬럼|계산·해석|
|---|---|---|
|생산량|{c.sources['batches']} / batch_id, produced_qty|해당 배치 1행, 0·누락이면 계산 차단|
|확정 불량|{c.sources['qc']} / batch_id, claim_id, defect_confirmed, qty_affected|True만 합산. 보류·False·신규 고객 주장·언론 제외|
|불량률|위 두 표|확정 불량 합 / produced_qty × 100; 분모는 생산량으로 고정. 출하량을 대체 분모로 혼용하지 않음|
|기록된 출하 범위|{c.sources['links']} / batch_id, shipment_id, customer_id, product_id, ship_date, shipped_qty|유효한 배치·제품·날짜·양수/0 수량 확인. 고객별 합산|
|추적 완전성|위 출하 표 + {c.sources['customers']} / customer_id|유효 고객 식별 출하 수량 / 기록된 총 출하 수량 × 100. 전체 출하 누락률 아님|
|미대사 수량|produced_qty − shipped_qty 합|현재 재고로 단정 금지|
|필요 재공급량|기록된 배치 shipped_qty 합|전체 기록 출하량을 교체 요청 범위로 쓰는 보수적 계획 가정. 반품 실제 수거량과 다름|
|공급 부족|생산팀 모의 회신 normal_stock_qty, free_capacity_qty|필요량 − 정상 재고 − 기존 약속 차감 후 순가용 생산량, 최소 0. 회신 없으면 NULL|
|고객별 배분|확인된 출하 고객·수량 + 가용량|출하량 우선 또는 고객 코드 순. 앱에서 조정 가능한 시연 가정|
|반복 경보|원본 claim_date, product_id, claim_type + 신규 claims|발생일 직전 30일 포함 총 31일, 동일 제품·유형 3건 이상. 직전 31일과 비교. 고객별·배치별 분포 표시|
|대시보드 KPI|claims, approvals, batch_states, department_tasks|원본 165개 검사·클레임 기록과 운영 신규 접수 KPI를 구분|

검사 합산의 비중복은 원문 정의와 claim_id 유일성에 의존한다. 물품 단위 중복 여부는 원본 필드로 검증 불가능하다. 추가 검사 회신은 품질팀 확인·비중복 확인·고유 검사 ID·시연 표기가 있어야 반영한다.
''')
    write('ASSUMPTIONS.md', '''# 원본 사실, 가정과 자료 공백

## 확인한 원본 사실
- 품질 정책 실제 경로: `04_원본데이터/fin_ar_aging_ms (2).csv` (본문은 Markdown 정책).
- 수식 실제 경로: `04_원본데이터/id_conventions (2).md`, 1.9 배치 불량률.
- 승인 권한 실제 경로: `04_원본데이터/calculation_definitions (2).md` (본문은 권한 정책).
- 기준일·EA·kg·KRW·NONE 정의: `04_원본데이터/mkt_meeting_notes_ms (2).md`.
- 회수 요건: 규격 이탈 확정 + 배치 불량률 10% 이상. 품질위원회 의결 후 실행. 원인 조사는 회수와 별개 트랙.
- B-02-2602-01: 17,900 / 150,745 ≈ 11.87436%. B-02-2603-01: 18,622 / 160,733 ≈ 11.58568%.

## 명시한 개발·시연 가정
- 모의 역할 전환은 실제 기업 로그인·전자서명이 아니다. 서버 세션으로 역할을 검사하고 접수자·승인자를 분리한다. 인터넷 공개 운영 전 실인증이 필요하다.
- 출하 고객 확인 보류는 시연 이벤트 오버레이다. 원본을 지우거나 변경하지 않는다. 물류 회신은 원본 고객과 충돌할 수 없다.
- 반복 이슈 임계값(31일·3건)은 공식 회수 기준이 아닌 운영 경보 가정이다.
- 공급 배분 기본값은 출하량 내림차순이며 코드 순으로 변경 가능하다. 고객 납기 우선순위가 아니다.
- 필요 교체량은 기록된 출하 전체를 보수적으로 사용한다. 실제 수거량·법적 회수 범위를 확정하지 않는다.
- 생산 회신의 정상 재고·순가용량·기간은 모의 확인값이다. 원본 생산능력을 무제한으로 늘리거나 기존 고객 약속을 취소하는 사실로 사용하지 않는다.
- 신규 접수는 확정 검사와 별개. 추가 검사 수량은 별도 품질팀 확인 기록으로만 반영한다.
- OPENAI_API_KEY가 없으면 규칙 기반 분석. 실제 LLM 실행이라고 표시하지 않는다.

## 찾지 못한 자료와 제한
- 프로젝트에서 W03 개별 안내와 A01~A05 이름의 별도 문서는 발견하지 못했다. 배경·권한·수식·공통 사전은 내용으로 식별했다.
- A04 원문과 제출 화면 6문항의 정확한 제목은 확인하지 못했다. 제출 초안의 6개 구분은 잠정이며 실제 양식 대조가 필요하다.
- Corevia 정상 완제품 재고, 일자별 생산 일정·예약, 주문 납기일, 배치↔주문 직접 조인, 실제 외부 통보·물류 완료는 없다.
- 원료 로트 마스터에 문제 배치의 특수 로트가 없을 수 있다. 누락을 정상 검사로 채우지 않는다.
- 생산능력 capacity_qty의 기간 단위가 없어 월 순가용량으로 직접 환산하지 않는다.
- SQLite는 로컬 실행 지속성 검증용. 현 Axhub의 일반 컨테이너 디스크에 올리면 재배포 후 보존을 보장할 수 없으므로 이번 Python 앱은 자동 재배포하지 않는다. Axhub 운영 시 PostgreSQL로 전환해야 한다.
''')
    write('OFFICIAL_REQUIREMENTS.md', '''# 공식 과제 확인 기록

- 출처: https://axacademy.ai/axwar/samilpwc-1 (2026-11-10 확인)
- 선택 업무 W03, Corevia 품질·영업·생산의 품질 이슈 및 공급 복구.
- 평가: 업무 이해, 데이터 근거, 실제 운영 처리, 변경·예외 대응.
- 접수→확인→판단→사람 승인→후속 작업→상태 반영이 연결되어야 한다.
- 정상·조건 변경·정보 부족/거절을 시연하고, 확장과 부서 영향을 제시하며 원본과 가정을 구분한다.
- 제출은 Axhub 앱 또는 소스 zip. 실행 안내·소스·환경 변수 이름 예시를 제공하며 키·가상환경·빌드 산출물은 제외한다.
- 설계 설명은 필수 6문항, 문항별 최대 1,000자. A04의 정확한 문항은 별도 확인 필요.
- 영상은 실제 작동 화면·음성 해설, 5분 이내 권장. 모의 처리는 구분 설명한다.
- 이번 구현은 로컬 Python 앱과 실행·테스트 증빙을 제공한다. 영상 촬영, 제출, 실제 API 키 호출 검증, Python 앱의 원격 배포는 수행하지 않았다.
''')


if __name__ == '__main__':
    main()
