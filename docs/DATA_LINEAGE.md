# 지표별 데이터 계보

|지표|실제 원본 경로·컬럼|계산·해석|
|---|---|---|
|생산량|04_원본데이터/sales_meeting_notes_cv (2).md / batch_id, produced_qty|해당 배치 1행, 0·누락이면 계산 차단|
|확정 불량|04_원본데이터/fin_ap_aging_ms (2).csv / batch_id, claim_id, defect_confirmed, qty_affected|True만 합산. 보류·False·신규 고객 주장·언론 제외|
|불량률|위 두 표|확정 불량 합 / produced_qty × 100; 분모는 생산량으로 고정. 출하량을 대체 분모로 혼용하지 않음|
|기록된 출하 범위|04_원본데이터/fin_cash_daily_ms (2).csv / batch_id, shipment_id, customer_id, product_id, ship_date, shipped_qty|유효한 배치·제품·날짜·양수/0 수량 확인. 고객별 합산|
|추적 완전성|위 출하 표 + 04_원본데이터/production_material_consumption_cv (2).csv / customer_id|유효 고객 식별 출하 수량 / 기록된 총 출하 수량 × 100. 전체 출하 누락률 아님|
|미대사 수량|produced_qty − shipped_qty 합|현재 재고로 단정 금지|
|필요 재공급량|기록된 배치 shipped_qty 합|전체 기록 출하량을 교체 요청 범위로 쓰는 보수적 계획 가정. 반품 실제 수거량과 다름|
|공급 부족|생산팀 모의 회신 normal_stock_qty, free_capacity_qty|필요량 − 정상 재고 − 기존 약속 차감 후 순가용 생산량, 최소 0. 회신 없으면 NULL|
|고객별 배분|확인된 출하 고객·수량 + 가용량|출하량 우선 또는 고객 코드 순. 앱에서 조정 가능한 시연 가정|
|반복 경보|원본 claim_date, product_id, claim_type + 신규 claims|발생일 직전 30일 포함 총 31일, 동일 제품·유형 3건 이상. 직전 31일과 비교. 고객별·배치별 분포 표시|
|대시보드 KPI|claims, approvals, batch_states, department_tasks|원본 165개 검사·클레임 기록과 운영 신규 접수 KPI를 구분|

검사 합산의 비중복은 원문 정의와 claim_id 유일성에 의존한다. 물품 단위 중복 여부는 원본 필드로 검증 불가능하다. 추가 검사 회신은 품질팀 확인·비중복 확인·고유 검사 ID·시연 표기가 있어야 반영한다.
