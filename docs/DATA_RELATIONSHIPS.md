# 데이터 관계와 조인 검증

파일 이름은 의미 근거가 아니다. 아래 연결은 실제 헤더·식별자·값으로 검증했다.

|참조 측 실제 파일 / 컬럼|마스터 측 실제 파일 / 컬럼|미연결 / 전체|마스터 키 중복|
|---|---|---|---|
|04_원본데이터/fin_ap_aging_ms (2).csv / `batch_id`|04_원본데이터/sales_meeting_notes_cv (2).md / `batch_id`|0 / 165|0|
|04_원본데이터/fin_ap_aging_ms (2).csv / `customer_id`|04_원본데이터/production_material_consumption_cv (2).csv / `customer_id`|0 / 165|0|
|04_원본데이터/fin_cash_daily_ms (2).csv / `batch_id`|04_원본데이터/sales_meeting_notes_cv (2).md / `batch_id`|0 / 1431|0|
|04_원본데이터/fin_cash_daily_ms (2).csv / `customer_id`|04_원본데이터/production_material_consumption_cv (2).csv / `customer_id`|0 / 1431|0|
|04_원본데이터/sales_meeting_notes_cv (2).md / `product_id`|04_원본데이터/strat_capex_plan_cv (2).csv / `product_id`|0 / 480|0|
|04_원본데이터/sales_orders_cv (2).csv / `batch_id`|04_원본데이터/sales_meeting_notes_cv (2).md / `batch_id`|0 / 480|0|
|04_원본데이터/sales_orders_cv (2).csv / `lot_id`|04_원본데이터/quality_policy_cv (2).md / `lot_id`|0 / 480|0|
|04_원본데이터/sku_weekly_sales_ms (2).csv / `order_id`|04_원본데이터/sc_purchase_orders_ms (2).csv / `order_id`|0 / 17987|0|
|04_원본데이터/m_influencer_ms (2).csv / `sku_id`|04_원본데이터/ext_fx_daily (2).csv / `sku_id`|0 / 14|0|

## 연결 미확인과 사용 제한
- 배치 출하 추적(SBL)과 주문 출하(SH)의 shipment_id 교집합: 0건. 직접 연결 불가.
- 배치 출하 표에 order_id가 없다. 고객·제품이 같다는 이유로 특정 주문을 해당 배치에 연결하지 않는다.
- 배치 production_line은 F1/F2 공장 코드, 능력표 line_id는 L-xx 라인 코드다. 이름만 보고 조인하지 않는다. 능력은 제품군·공장 스냅샷 참고값으로만 표시.
- Masil SKU 재고는 Corevia 제조 정상 재고가 아니다. 공급 복구 가용량에서 제외한다.
- 주문에 납기일 컬럼 없음. 지연 일수·납기 우선순위를 원본 확정값으로 산출할 수 없다.
- 모든 분석은 배치 생산일 ≤ 검사·출하일, 출하일 ≥ 주문일, 제품 ID 일치를 검증한다. 충돌이 있으면 승인 실행 차단.
