"""Content-based, read-only source discovery. Filenames are deliberately not trusted."""
from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path

import pandas as pd

SIGNATURES = {
    'batches': ({'batch_id', 'produced_qty', 'qc_result'}, '품질·생산', '생산 배치 및 검사 판정'),
    'qc': ({'claim_id', 'defect_confirmed', 'qty_affected'}, '품질', '원본 품질 클레임·확정 검사'),
    'links': ({'shipment_id', 'batch_id', 'shipped_qty'}, '물류', '배치별 출하 추적'),
    'shipments': ({'shipment_id', 'order_id', 'revenue_krw'}, '영업·물류', '주문별 출하 실적'),
    'orders': ({'order_id', 'customer_id', 'order_qty'}, '영업', '고객 주문·납품 약속'),
    'customers': ({'customer_id', 'customer_name'}, '영업', '고객 마스터'),
    'products': ({'product_id', 'product_name'}, '생산', '제품군 마스터'),
    'capacity': ({'capacity_qty', 'utilization_pct'}, '생산', '라인별 생산능력 스냅샷'),
    'inventory': ({'sku_id', 'on_hand_qty'}, 'Masil 공급망', '유통 재고 — 제조 재고와 별개'),
    'sku': ({'sku_id', 'source_company', 'product_id'}, 'Masil 공급망', 'SKU·Corevia 제품군 대응'),
    'lots': ({'lot_id', 'inspection_result', 'received_qty'}, '품질·조달', '원료 로트 검사'),
    'consumption': ({'consumption_id', 'batch_id', 'lot_id'}, '생산', '배치 원료 투입'),
}

# Department names below describe the business process, not an unverified author identity.
REFERENCE_SIGNATURES = [
    ({'sku_id','channel_id','product_cost_krw'}, 'Masil 재무·운영', 'SKU·채널별 원가·물류 기준'),
    ({'coupon_use_id','stacked_flag'}, 'Masil 마케팅', '주문별 쿠폰 할인·중복 적용'),
    ({'inflow_id','impressions','conversions'}, 'Masil 마케팅', '매체 유입·클릭·전환'),
    ({'customer_ref','first_order_date','reorder_within_90d'}, 'Masil 마케팅', '고객별 재구매 이력'),
    ({'return_id','refund_completed_date'}, 'Masil 고객지원·재무', '반품·환불 승인 실적'),
    ({'customer_ref','gmv_krw','campaign_id'}, 'Masil 커머스·마케팅', '캠페인 귀속 주문 표본'),
    ({'campaign_name','attribution_window_days'}, 'Masil 마케팅', '캠페인 마스터'),
    ({'channel_name','payment_terms_days'}, 'Masil 영업·운영', '판매 채널 마스터'),
    ({'booking_amount_krw','shipment_revenue_krw'}, 'Corevia 영업·재무', '수주·출하 실적 월별 집계'),
    ({'spend_id','ad_cost_krw'}, 'Masil 마케팅', '캠페인 광고 집행 비용'),
    ({'ar_id','agency_id','outstanding_krw'}, 'Corevia 재무', '고객·대리점 매출채권'),
    ({'po_id','sku_id','moq'}, 'Masil 공급망', 'SKU 구매 발주·납부 일정'),
    ({'opening_balance','covenant_min_krw'}, 'Masil 재무', '일별 현금·차입약정 실적'),
    ({'opening_balance','closing_balance'}, '재무 — 회사 구분 원문 확인', '일별 현금 입출금'),
    ({'deposit_id','matched_ar_id'}, 'Corevia 재무', '대리점 입금·채권 매칭'),
    ({'product_id','gross_profit_krw','opex_krw'}, 'Corevia 재무', '제품군별 손익'),
    ({'week','sku_id','sold_qty'}, 'Masil 영업·공급망', 'SKU 주간 판매 실적'),
    ({'ap_id','payment_due_date','supplier_id'}, 'Masil 재무', '매입채무·지급 예정'),
    ({'ar_id','channel_id','outstanding_krw'}, 'Masil 재무', '채널별 매출채권'),
    ({'forecast_date','projected_closing_krw'}, 'Masil 재무', '현금 전망 — 작성자 주장, 확정 사실 아님'),
    ({'expected_amount_krw','collected_amount_krw'}, 'Masil 재무', '채널 정산·회수 실적'),
    ({'agency_id','representative_name','rebate_eligible'}, 'Corevia 영업지원', '대리점 식별 마스터'),
    ({'option_id','capex_krw','added_capacity_qty'}, '그룹 전략·생산', '설비 증설 대안·제약'),
    ({'po_id','unit_price_fx','material_id'}, 'Corevia 조달', '원료 구매·환율 적용'),
    ({'rebate_id','rebate_amount_krw'}, 'Corevia 영업지원', '판매장려금 지급·승인 기록'),
    ({'material_name','is_exclusive'}, 'Corevia 조달', '원료·공급계약 마스터'),
    ({'plan_id','requested_budget_krw','campaign_id'}, 'Masil 마케팅', '캠페인 예산 기안'),
    ({'influencer_name','fee_type'}, 'Masil 마케팅', '인플루언서 계약 유형 마스터'),
]

MEANINGS = {'batch_id': '한 번에 같이 생산한 제품 묶음 식별자', 'product_id': 'Corevia 제품군 식별자; 개별 SKU 아님',
            'produced_qty': '배치 생산량; 불량률 분모', 'qty_affected': '검사·클레임 영향 수량; 확정 True만 합산',
            'defect_confirmed': '규격 이탈 확정 여부; 보류·False는 미확정', 'claim_id': '품질 검사·클레임 고유 기록',
            'customer_id': '기업 고객 식별자; customer_ref와 다른 체계', 'shipment_id': '출하 식별자; SBL과 SH는 별도 체계',
            'order_id': '수주 식별자; 배치 연결 표에는 없음', 'lot_id': '원료 로트 식별자; 생산 배치와 다른 단위',
            'input_lot_ids': '배치에 투입한 원료 로트 목록', 'qc_result': '배치 품질 판정; 보류는 확정 불량과 다름',
            'production_date': '생산 실행일', 'ship_date': '출하일; 수주일과 구분', 'claim_date': '원본 클레임 발생일',
            'shipped_qty': '해당 출하 기록 수량', 'capacity_qty': '라인 생산능력; 기간 단위가 없으므로 월 가용량으로 단정 금지',
            'utilization_pct': '라인 단위 가동률(%)', 'on_hand_qty': 'Masil 유통 현재고; Corevia 제조 재고 아님',
            'in_transit_qty': '유통 운송 중 물량; 현재고와 구분', 'snapshot_date': '재고·생산능력 스냅샷 기준일',
            'order_qty': '수주 총량; 납기일 컬럼 별도 미제공', 'customer_name': '기업 고객 명칭', 'product_name': '제품군 명칭'}


def decode(raw):
    for encoding in ('utf-8-sig', 'cp949', 'euc-kr'):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise ValueError('지원 인코딩으로 읽을 수 없음')


def unit(column, logical=None):
    if column.endswith('_krw') or column in ('opening_balance', 'closing_balance'):
        return 'KRW·부가세 제외'
    if 'pct' in column or column.endswith('_rate'):
        return '% 여부는 정의 확인; pct는 %'
    if 'qty' in column:
        return 'kg' if logical in ('lots','consumption') and column in ('consumed_qty','received_qty') else 'EA' if logical in ('batches','qc','links','shipments','orders','inventory','sku','capacity') else '제품 EA / 원료 kg (본문 정의 기준)'
    return '식별자·날짜·범주 또는 정의 확인'


class Catalog:
    def __init__(self, root):
        self.root = Path(root)
        self.entries, self.tables, self.sources, self.documents = [], {}, {}, []
        self.scan()

    def scan(self):
        folder = self.root / '04_원본데이터'
        if not folder.exists():
            return
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            entry = {'path': path.relative_to(self.root).as_posix(), 'filename': path.name,
                     'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                     'modified_at': pd.Timestamp(path.stat().st_mtime, unit='s').isoformat()}
            try:
                content, encoding = decode(raw)
                entry['encoding'] = encoding
                first = content.splitlines()[0] if content else ''
                if '|' not in first or first.startswith('#'):
                    entry.update(kind='document', title=first, rows=0, columns=[], warning='CSV 확장자이지만 본문 문서' if path.suffix == '.csv' else '')
                    self.documents.append((entry['path'], content))
                else:
                    df = pd.read_csv(io.StringIO(content), sep='|', dtype=str, keep_default_na=False)
                    if len(df.columns) < 2:
                        raise ValueError('파이프 구분자 검증 실패')
                    logical = next((key for key, (sig, _, _) in SIGNATURES.items() if sig <= set(df.columns)), None)
                    meaning = SIGNATURES.get(logical) or next((item for item in REFERENCE_SIGNATURES if item[0] <= set(df.columns)), (set(), '담당 부서 원문 확인 필요', '업무 의미 확인 필요'))
                    key_columns = [c for c in df if c.endswith('_id') or c.endswith('_ref')]
                    columns = []
                    dates = {}
                    for col in df:
                        series = df[col]
                        missing = series.isin(['', 'NONE', 'NULL', 'null', 'N/A'])
                        valid = series[~missing]
                        numbers = pd.to_numeric(valid, errors='coerce')
                        dtype = 'number' if len(valid) and numbers.notna().all() else 'string'
                        if len(valid) and valid.isin(['True', 'False']).all():
                            dtype = 'boolean'
                        invalid = 0
                        if re.search(r'date|^week$|period_ym', col):
                            parsed = pd.to_datetime(valid, errors='coerce', format='mixed')
                            invalid = int(parsed.isna().sum())
                            if parsed.notna().any():
                                dates[col] = {'min': str(parsed.min().date()), 'max': str(parsed.max().date())}
                                dtype = 'date'
                        negative = int((numbers < 0).sum()) if dtype == 'number' else 0
                        columns.append({'name': col, 'meaning': MEANINGS.get(col, '업무 의미는 해당 원본 정의와 함께 확인; 자동 추정하지 않음'), 'dtype': dtype, 'null_pct': round(float(missing.mean()) * 100, 3),
                                        'invalid_count': invalid, 'invalid_pct': round(invalid / len(df) * 100, 3) if len(df) else 0,
                                        'negative_count': negative, 'unit': unit(col, logical),
                                        'unique': int(series.nunique()), 'sample': valid.head(3).tolist()})
                    entry.update(kind='table', logical=logical, department=meaning[1], description=meaning[2],
                                 rows=len(df), column_count=len(df.columns), columns=columns, identifiers=key_columns,
                                 dates=dates, duplicate_count=int(df.duplicated().sum()),
                                 duplicate_pct=round(float(df.duplicated().mean()) * 100, 3),
                                 warning='이름·확장자로 의미를 추정하지 않음; 헤더 기반 검증', usage=meaning[2] if logical else '목록·품질 검증만')
                    if logical:
                        if logical in self.tables:
                            entry['warning'] = '같은 구조 중복 발견 — 자동 채택 보류'
                        else:
                            self.tables[logical] = df.to_dict('records')
                            self.sources[logical] = entry['path']
            except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
                entry.update(kind='error', error=str(exc), rows=0, columns=[])
            self.entries.append(entry)

    def rows(self, key):
        return self.tables.get(key, [])

    def document(self, title):
        return next(((path, text) for path, text in self.documents if title in text.splitlines()[0]), None)

    def reference(self, key, row):
        ids = {k: v for k, v in row.items() if k.endswith('_id')}
        return {'file': self.sources.get(key), 'identifiers': ids, 'record': row}

    def write_reports(self):
        docs = self.root / 'docs'
        docs.mkdir(exist_ok=True)
        (docs / 'catalog.json').write_text(json.dumps(self.entries, ensure_ascii=False, indent=2), encoding='utf-8')
        dictionary = ['# 원본 데이터 사전', '', '전체 파일을 실제 헤더로 식별. 원본은 변경하지 않음. 수량=제품 EA·원료 kg, 금액=KRW(VAT 제외).', '', '|실제 경로|확인된 의미·부서|행×열|활용|', '|---|---|---|---|']
        quality = ['# 데이터 품질 검사', '', 'NONE은 원본의 해당 없음 코드이며 SQL NULL과 구분한다. 날짜 범위는 실제 값, modified_at은 로컬 파일 시각이며 업무 갱신일이 아니다.', '']
        for entry in self.entries:
            dictionary.append(f"|{entry['path']}|{entry.get('description', entry.get('title', '읽기 오류'))} · {entry.get('department', '')}|{entry['rows']}×{entry.get('column_count', 0)}|{entry.get('usage', '정책·문서')}|")
            quality += [f"## {entry['path']}", f"- SHA256: `{entry['sha256']}` · 인코딩: {entry.get('encoding')} · 형태: {entry['kind']}", f"- 날짜 범위: {json.dumps(entry.get('dates', {}), ensure_ascii=False)}", f"- 중복행: {entry.get('duplicate_count', 0)} ({entry.get('duplicate_pct', 0)}%) · {entry.get('warning', '')}"]
            if entry['kind'] == 'table':
                dictionary += [f"\n## {entry['path']}", '|컬럼|실제 추론 타입|단위·해석|결측%|', '|---|---|---|---|']
                for col in entry['columns']:
                    dictionary.append(f"|{col['name']} — {col['meaning']}|{col['dtype']}|{col['unit']}|{col['null_pct']}|")
                    if col['null_pct'] or col['invalid_count'] or col['negative_count']:
                        quality.append(f"- {col['name']}: 결측 {col['null_pct']}%, 날짜 오류 {col['invalid_count']}, 음수 {col['negative_count']} (음수가 항상 오류인 것은 아님)")
        for name, lines in [('DATA_DICTIONARY.md', dictionary), ('DATA_QUALITY.md', quality)]:
            (docs / name).write_text('\n'.join(lines), encoding='utf-8')
