# 확장 기능

## A. 출하 추적 완전성

실제 출처는 fin_cash_daily_ms (2).csv의 batch_id/shipment_id/customer_id/product_id/ship_date/shipped_qty, production_material_consumption_cv (2).csv의 customer_id다. 파일명만으로 의미를 정하지 않았다.

분자=유효 고객 식별 출하 수량, 분모=배치의 기록된 출하 수량. 전체 물류의 누락률은 아니다. 미확인 고객·기록 없음·날짜 충돌·출하>생산이면 실행 범위를 보류하고 물류 확인 작업을 만든다. 확정 불량 요건 충족 시 임시 출하 보류와 최종 회수 의결을 구분한다. 원본과 일치하는 모의 회신이 저장되면 재분석 후 요청을 생성한다.

## B. 반복 품질 이슈 조기 경보

실제 출처는 fin_ap_aging_ms (2).csv의 claim_date/product_id/claim_type/batch_id/customer_id와 신규 claims다. 기준일 직전 30일 포함 31일의 동일 제품·유형 3건 이상이면 품질 조사·추가 검사 작업을 만든다. 직전 31일과 빈도, 배치·고객 분포도 표시한다.

임계값은 공식 회수 기준이 아닌 시연 정책이다. 반복 주장을 확정 불량으로 합산하거나 자동 회수하지 않는다. 기간·제품·유형 키로 중복 작업을 막는다. 현재 분류는 유형 정확 일치이며 LLM 의미 유사 군집화는 미구현이다.
