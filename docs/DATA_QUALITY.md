# 데이터 품질 검사

NONE은 원본의 해당 없음 코드이며 SQL NULL과 구분한다. 날짜 범위는 실제 값, modified_at은 로컬 파일 시각이며 업무 갱신일이 아니다.

## 04_원본데이터/calculation_definitions (2).md
- SHA256: `889f7eb5018b455f05e9c934686c4926e97ef7624d5405975a3eedc5b107769d` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/celtonic_contract_summary (2).md
- SHA256: `07f5cb64341e89ec5c190e5de9c99e4a71c432d34814dc1a7d77bd5a03b35e4e` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/celtonic_customer_composition (2).csv
- SHA256: `d0b9806d32b859d96b6c3d18f7d30597b2993fd1068d2c3e0d2961bf1accb0b7` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/celtonic_financials_raw (2).csv
- SHA256: `6d49baa51fa822f401b75bf8bf850cca99541a07fe8464c0f0b75531576591c1` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"date": {"min": "2025-01-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- campaign_id: 결측 34.352%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- platform: 결측 34.352%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- sns_format: 결측 34.352%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/celtonic_management_interview (2).md
- SHA256: `ea2c732c939fb1cfa0aa628e3b0a1a850a84855015b073ebef98cdfecbc61cdd` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"first_order_date": {"min": "2025-01-01", "max": "2026-06-30"}, "reorder_date": {"min": "2025-01-06", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- reorder_date: 결측 84.38%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/celtonic_news_clippings (2).md
- SHA256: `45ac7d5007ccfdbe30eb409eea0e4b3ed90042ca5480f0abecff6fda9dad7bc4` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"refund_completed_date": {"min": "2025-01-13", "max": "2026-06-30"}, "original_order_date": {"min": "2025-01-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/celtonic_revenue_by_customer (2).csv
- SHA256: `adc5faf03f86021ffca2b9eeaada539411c3bbc88fe12fca0a7d7f86d4a8737a` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"order_date": {"min": "2025-01-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/data_dictionary (2).md
- SHA256: `672edfdb343ee1c668a511fafbb4ac51d498134340119a3069007b2b5b86a7d0` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/ext_channel_benchmark (2).csv
- SHA256: `91425e5078416e2168452441d398e72484a9b5882dc990a7cfc88d3104b4c4ce` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"start_date": {"min": "2025-01-01", "max": "2025-12-30"}, "end_date": {"min": "2025-07-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/ext_fx_daily (2).csv
- SHA256: `7df809c41142d702e09be67b510a65e6c638d59f1f0c43eb2d231c934faf1c64` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/ext_industry_benchmark (2).csv
- SHA256: `a4dd2066bb0e22b8e9cb7ecd215600b0b8acd47b00510d03fc35db232b06cb1c` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"effective_date": {"min": "2024-01-01", "max": "2024-01-01"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- partner_code: 결측 25.0%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/ext_news_quality_incident (2).md
- SHA256: `e004bd66caead04b7ad9000d8de643941a19375ffc8d062fec481c740581a111` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/fin_ap_aging_ms (2).csv
- SHA256: `97ab9691178f36ba5e6aae5dbe3004f767187500f2ed8ad6eb604d2e11c5b248` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"claim_date": {"min": "2024-02-23", "max": "2026-06-25"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/fin_ar_aging_cv (2).csv
- SHA256: `846125247bec79ca6a927cef1c61bca31b51145fc9b4f84e002073fcf3f7517b` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) · CSV 확장자이지만 본문 문서
## 04_원본데이터/fin_ar_aging_ms (2).csv
- SHA256: `352b77edaf66a4dd3bbb368ec9c778652898262bdc37761a70db51d401526a74` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) · CSV 확장자이지만 본문 문서
## 04_원본데이터/fin_cash_daily_ms (2).csv
- SHA256: `89a39a1774779ea6917ec0559007818c80067f29b68e44fb26a5d9d249afa01a` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"order_date": {"min": "2023-12-19", "max": "2026-06-15"}, "ship_date": {"min": "2024-01-10", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/fin_collection_history_ms (2).csv
- SHA256: `462d365af81d77de0d5962e8ab04c598b00b027c41fef3c9cfc96c8d3a0741e8` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"period_ym": {"min": "2024-01-01", "max": "2026-06-01"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- booking_yoy_pct: 결측 33.611%, 날짜 오류 0, 음수 118 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/fin_income_statement_cv (2).csv
- SHA256: `b495d4dafc23889efd3797664b49de64af584b75152ddd749b6ef0a92e060747` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) · CSV 확장자이지만 본문 문서
## 04_원본데이터/grp_available_cash (2).md
- SHA256: `dc394fd268c80e3243ae19c64dd989b71beb2982a466ab9e99528a4ba0a19d30` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/grp_investment_proposal_celtonic (2).md
- SHA256: `203d09a779358ad73d28631a193724313af54fb1634293f8018c3d766e36b870` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"spend_date": {"min": "2025-01-01", "max": "2026-06-26"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- platform: 결측 33.333%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- sns_format: 결측 33.333%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- influencer_fee_krw: 결측 66.667%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/id_conventions (2).md
- SHA256: `8a62b6f6752eb2f2f1a465aa2b95028fb78f8008d5b201407c269525eaf48ece` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/lc0001_payment_term_notice (2).md
- SHA256: `83a129a2c7f8f58f6f8c63b96bec64b3224b6d1324fa533ca877aa1800ad3c0b` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/m_agency_cv (2).csv
- SHA256: `b5abb8731b9711096df1651c19a80a2610aff63b2034ccb464eb430ddc1c8705` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"invoice_date": {"min": "2025-11-06", "max": "2026-06-25"}, "due_date": {"min": "2026-01-05", "max": "2026-08-24"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- agency_id: 결측 49.315%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- customer_id: 결측 50.685%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/m_channel_ms (2).csv
- SHA256: `2686b7e51395ff487b5cb37d7fe1a6f2f20c4ff77acea8164bee5e32918ebd44` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"order_date": {"min": "2026-06-22", "max": "2026-06-26"}, "payment_due_date": {"min": "2026-07-21", "max": "2026-07-21"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/m_customer_cv (2).csv
- SHA256: `dec4ad30f4d80312ea1817dcbe72b5c8b5ad4b679dd470f100a1c311c35dd792` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"date": {"min": "2024-01-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/m_influencer_ms (2).csv
- SHA256: `5ee7162933b1e30d779625ce5c384b8acc1d6e51636c083f49aaa6dab02548f8` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"snapshot_date": {"min": "2026-06-30", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/m_material_cv (2).csv
- SHA256: `65831ca36482ce21fa59ff7883ba64c15755280745fbf6bdc83562f7898be4fa` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"deposit_date": {"min": "2026-01-12", "max": "2026-06-23"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/m_product_cv (2).csv
- SHA256: `c934ec99cc41dad452ae2d1772c8c537c45e70dd768cc37e71a0b5412071e14a` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"period_ym": {"min": "2024-01-01", "max": "2026-06-01"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- operating_profit_krw: 결측 0.0%, 날짜 오류 0, 음수 20 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/m_sku_ms (2).csv
- SHA256: `a3fa428c227708fffaf78a52155a991b65d05075f8de04b85f944bd59cbaf54a` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"week": {"min": "2025-01-06", "max": "2026-06-29"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/material_lot_master_cv (2).csv
- SHA256: `7f12eaccb2261cdae9a540da25e2a5747a2100ff1940421af35d6813920acf49` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) · CSV 확장자이지만 본문 문서
## 04_원본데이터/mkt_budget_plan_ms (2).csv
- SHA256: `2c70e53dd4638935c80e3272b54466084d56c772399d77519b4f18039faf93d5` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) · CSV 확장자이지만 본문 문서
## 04_원본데이터/mkt_cost_master_ms (2).csv
- SHA256: `851c1d108caaad3c28a558a596f67459b520bc6828a00ca6e3bc3287017c4e11` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"invoice_date": {"min": "2026-05-07", "max": "2026-06-26"}, "payment_due_date": {"min": "2026-06-06", "max": "2026-07-25"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- po_id: 결측 41.667%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/mkt_coupons_ms (2).csv
- SHA256: `242e9d3d8805d29903fb1d6c269ea841489e7ed3d1a9ad54732732ab6bae1437` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"invoice_date": {"min": "2026-04-01", "max": "2026-06-30"}, "due_date": {"min": "2026-04-08", "max": "2026-09-06"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/mkt_meeting_notes_ms (2).md
- SHA256: `74c2aae386fe01e4b6f49029882d92f56644be23187bf2dcf9d778f2a0ddd677` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/mkt_orders_ms (2).csv
- SHA256: `6dd0d9f8ef3af047460ffaaea2d82a5eddd4a2fae74596507e7953809805129f` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"date": {"min": "2024-01-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/mkt_repurchase_ms (2).csv
- SHA256: `cd123e0a442745006348a4b6026e5c168336ababf2b8434df60ef4121095eca3` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"forecast_date": {"min": "2026-06-30", "max": "2026-06-30"}, "week": {"min": "2026-07-06", "max": "2026-09-28"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/mkt_returns_ms (2).csv
- SHA256: `21643d65ccced6fea3faa1b89e62c86e0f349b3607ed4eaef96335fc32c11ba5` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"period_ym": {"min": "2025-07-01", "max": "2026-06-01"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/mkt_traffic_inflow_ms (2).csv
- SHA256: `a8d635b8df8a6734bdfe5806c4d61e5c752c381056b7d5a756f65ec05a6ccefd` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) · CSV 확장자이지만 본문 문서
## 04_원본데이터/prod_batch_log_cv (2).csv
- SHA256: `10b959e3d1f13987c5da1d6cc81172de881f43b6f94e2d72267aa1e8a3f7bcc7` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"registered_date": {"min": "2020-02-08", "max": "2023-12-25"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/production_material_consumption_cv (2).csv
- SHA256: `451944a7bf1b77863e53c31fc222b014f84c7baa36b678ab2e6b9c8bc3701bf0` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"effective_date": {"min": "2024-01-01", "max": "2024-01-01"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/quality_policy_cv (2).md
- SHA256: `af28bc7e8946b0c3135ac841b9f097095a68e453960e638dce7e3c00b5632db7` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"receipt_date": {"min": "2024-01-02", "max": "2026-06-23"}, "inspection_date": {"min": "2024-01-05", "max": "2026-06-24"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/rfp_c201 (2).md
- SHA256: `4bd5aa852deb7449b5bb8bde77a5ed8d032b27d2592372a953db8d44e1efaceb` · 인코딩: utf-8-sig · 형태: document
- 날짜 범위: {}
- 중복행: 0 (0%) ·
## 04_원본데이터/sales_meeting_notes_cv (2).md
- SHA256: `6c49f0268bd75c21dee53bb8e7c6cedffcf825b836f1d42c822671fb1ebab408` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"production_date": {"min": "2024-01-02", "max": "2026-06-23"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/sales_orders_cv (2).csv
- SHA256: `59eda3edae91a304053d8865d67dbabb266567e7fbf5c3035bbd2768fa0d84fb` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"consumption_date": {"min": "2024-01-02", "max": "2026-06-23"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/sales_rebate_payment_cv (2).csv
- SHA256: `d8bff0e267868a1d736dfd309dc67ae5c9a46c73d98136c406f7f9df73b99636` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"snapshot_date": {"min": "2026-06-30", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/sales_shipments_cv (2).csv
- SHA256: `bafd2c76ee394e6d0a5bdf082c6b88a30ff636562a8ae28c5ef1baba7a277ebc` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/sc_purchase_orders_ms (2).csv
- SHA256: `1f0d49d7aca7c4550d378fd772155e4abf213218a166902a72a71423eed26d0e` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"order_date": {"min": "2023-11-01", "max": "2026-06-26"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- customer_id: 결측 3.035%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- agency_id: 결측 96.965%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/shipment_batch_link_cv (2).csv
- SHA256: `5ac7befd8c08a9d34c2a5fd063b1658a25e2fdb46ad727a2e54790dcaaf3f5b6` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"purchase_date": {"min": "2024-07-08", "max": "2026-06-25"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/sku_inventory_ms (2).csv
- SHA256: `820a4e96e2ae06b361a9b39d3de428af1c43c0a659c41e2dbd25a9b41c490ac5` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"period_ym": {"min": "2026-01-01", "max": "2026-06-01"}, "payment_date": {"min": "2026-02-04", "max": "2026-06-04"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- approver: 결측 16.667%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
- payment_date: 결측 18.333%, 날짜 오류 0, 음수 0 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/sku_weekly_sales_ms (2).csv
- SHA256: `86553f47628b0fa550af9b532b3d9ad5f1b778cc165e696544de34ae96dfed09` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"ship_date": {"min": "2024-01-01", "max": "2026-06-30"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/strat_capacity_cv (2).csv
- SHA256: `be05f5dd87eaa1443e95da0322cae5007ba89579af91aa3b3b512b5b5e6b30db` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"effective_date": {"min": "2024-01-01", "max": "2024-01-01"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/strat_capex_plan_cv (2).csv
- SHA256: `a4c6a68ca499fcd5667b45d4b4737cc7d46d430a685267e1f6eaaf54cf496bf6` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
- market_growth_pct: 결측 0.0%, 날짜 오류 0, 음수 1 (음수가 항상 오류인 것은 아님)
## 04_원본데이터/strat_celtonic_adjustment_analysis (2).csv
- SHA256: `c1696151998b68e3d8fa5e38e0d4f8fa91c0b4c45bffd743e4b59fd88cbf9df5` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {"settlement_date": {"min": "2026-07-17", "max": "2026-09-23"}}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
## 04_원본데이터/strat_valuation_multiples (2).csv
- SHA256: `5a6eb2c4b5942ae6485f85c353b2b196ddda8ce8eee787661c7fbc8054fdc8af` · 인코딩: utf-8-sig · 형태: table
- 날짜 범위: {}
- 중복행: 0 (0.0%) · 이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증
