# axhub 로 할 수 있는 것

> ⚠️ 이 파일은 자동 생성돼요. 고치려면 axhub-template 레포의 `shared/AXHUB.md` 를 고치고 `node scripts/sync-design.mjs` 를 돌려요.

이 앱은 axhub 위에서 돌아요. axhub 는 배포만 해 주는 곳이 아니라 **DB · 파일 저장 · 알림/메일 · 웹훅 · 로그인 · 권한 · 도메인** 을 앱에 붙여 주는 플랫폼이에요.
"이런 기능이 필요해" 싶으면 직접 만들기 전에 이 표부터 보세요. 대부분 **설정 한 줄 + 다시 배포** 로 끝나요.

| 하고 싶은 것 | 방법 | 아래 절 |
|---|---|---|
| 배포하기 · 배포 확인 | Claude Code 에서 `/axhub:deploy` | [1](#1-배포--확인--되돌리기) |
| 앱이 이상할 때 로그 보기 | `axhub deploy logs --app <슬러그> --follow` | [1](#1-배포--확인--되돌리기) |
| 이전 배포로 되돌리기 | `axhub deploy rollback` | [1](#1-배포--확인--되돌리기) |
| API 키 같은 비밀값 넣기 | `axhub env set … --secret` → 다시 배포 | [2](#2-환경변수--비밀값) |
| 데이터 저장 (DB) | `axhub.yaml` 의 `database:` 주석 해제 → 다시 배포 | [3](#3-db-켜기) |
| 사진·문서 같은 파일 저장 | `axhub.yaml` 에 `storage: enabled: true` → 다시 배포 | [4](#4-파일-저장-storage) |
| 사용자에게 알림·메일 보내기 | `@ax-hub/sdk` 의 `createAppMessagingClient()` | [5](#5-알림--메일) |
| 외부 서비스(결제·폼 등)에서 웹훅 받기 | `axhub relay create` → 라우트 핸들러 | [6](#6-웹훅-받기) |
| 로그인한 사람·역할 알기 | `lib/axhub-server.ts` 의 `me()` | [7](#7-로그인--권한--공개-범위) |
| 누가 쓸 수 있는지 정하기 · 공개 | `axhub publish` · `axhub access invite` | [7](#7-로그인--권한--공개-범위) |
| 공개 전에 따로 시험하기 | 스테이징 `axhub deploy staging enable` | [8](#8-스테이징--심사) |
| 회사 DB·SaaS 데이터 읽기 | `lib/axhub-server.ts` 의 `queryConnector()` | [9](#9-회사-데이터-connector) |
| 내 도메인 연결 | `axhub apps domains add` | [10](#10-커스텀-도메인) |
| 앱에서 AI 쓰기 | 공급사 키 또는 회사 AXRouter 키를 비밀값으로 | [11](#11-앱에서-ai-쓰기) |

> 명령의 `<슬러그>` 는 앱 주소의 앞부분이에요. 모르면 `axhub apps list` 로 확인해요.
> 대부분의 바꾸는 명령은 **미리보기가 기본**이에요. 실제로 하려면 `--execute` 를 붙여요.
> 자세한 설명: https://docs.axhub.ai/ko/docs

---

## 1. 배포 · 확인 · 되돌리기

- **가장 쉬운 길:** Claude Code 에서 `/axhub:deploy` — 미리보기 → 동의 → 배포 → 성공 확인까지 해 줘요.
- **직접:**
  ```bash
  axhub deploy create --app <슬러그> --execute     # --execute 가 없으면 미리보기만 해요
  axhub deploy status --app <슬러그> --watch       # 진행 상황
  axhub deploy logs --app <슬러그> --follow        # 앱이 찍는 로그 (오류 원인 찾기)
  ```
- **배포 전 검사:** `axhub.yaml` 의 `ci.commands` 가 배포 전에 돌아요 (이 템플릿은 디자인 규칙 검사).
- **처음 뜨는 시간은 60초까지예요.** `/healthz` 가 60초 안에 응답하지 않으면 배포가 실패해요. 시작할 때 오래 걸리는 일이 있으면 `axhub.yaml` 의 `runtime.healthcheck` 로 늘려요 (최대 5분).
- **되돌리기:** 코드만 되돌려요. DB 데이터는 그대로예요.
  ```bash
  axhub deploy releases --app <슬러그>                                   # 돌아갈 배포 고르기
  axhub deploy rollback --app <슬러그> --from-deployment <배포ID> --execute
  ```

## 2. 환경변수 · 비밀값

- **비밀값(API 키 등)** 은 코드에도 `axhub.yaml` 에도 적지 않아요. 값은 명령행에 남지 않게 stdin 으로 넣어요.
  ```bash
  printf %s "$MY_API_KEY" | axhub env set MY_API_KEY --app <슬러그> --secret --from-stdin --stage runtime
  ```
- **넣거나 바꾼 뒤엔 다시 배포해야 적용돼요.**
- `axhub.yaml` 의 `env:` 에는 **이름과 scope 만** 적어요. `required` 로 적으면 값이 없을 때 배포가 막혀요.
- 이름은 대문자·숫자·`_` 만, `AXHUB_` 로 시작할 수 없어요.
- `NEXT_PUBLIC_` 로 시작하는 값은 **브라우저에 그대로 보여요.** 비밀값엔 절대 쓰지 마세요.
- 로컬에서는 `.env.local` 에 넣어요 (커밋 금지).

## 3. DB 켜기

**DB 는 기본으로 꺼져 있어요.** 데이터를 저장해야 할 때만 켜요. 켜면 앱 전용 PostgreSQL 이 생기고, 코드는 `lib/db.ts` 의 `db()` 로 써요.

**로컬 (내 컴퓨터)**
1. Docker Desktop 을 켜요.
2. `npm run db:up` — 로컬 Postgres 가 떠요 (localhost:5432).
3. `.env.local` 의 `DATABASE_URL=` 줄 주석(`#`)을 지워요.
4. `npm run dev` 를 다시 띄워요.

**배포 (axhub)**
1. `axhub.yaml` 의 아래 두 줄 주석을 지워요.
   ```yaml
   database:
     engine: postgres
   ```
2. 커밋하고 다시 배포해요. axhub 가 DB 를 만들고 `DATABASE_URL` · `DIRECT_DATABASE_URL` 을 **자동으로** 넣어 줘요 (직접 넣지 않아요).

- 테이블은 `lib/db.ts` 의 `ensureSchema()` 에 `CREATE TABLE IF NOT EXISTS …` 로 적으면 처음 쓸 때 만들어져요.
- 운영과 스테이징은 DB 가 따로예요.
- 벡터 검색 같은 확장이 필요하면 `database.extensions: [pgvector]` 처럼 적어요.
- **바깥 고객 여럿의 데이터를 한 DB 에 담거나, 자체 회원·비밀번호 표가 있다면** DB 계정을 나눠요 (axhub 로그인만 쓰는 앱은 필요 없어요).
  ```yaml
  database:
    engine: postgres
    roles: [runtime, auth]     # → DATABASE_URL_RUNTIME · DATABASE_URL_AUTH 자동 주입
    owner_bypass_rls: true     # FORCE ROW LEVEL SECURITY 를 쓸 때만
  ```
  새 계정은 표 권한이 없어요 — `ensureSchema()`(기존 계정)에서 `current_database() || '_runtime'` 계정에 `GRANT` 하고 RLS 정책을 만들어요. 고객사 지정은 트랜잭션 안에서 `set_config('app.tenant_id', …, true)` 로 해요. 자세히: https://docs.axhub.ai/ko/docs/features/data#db-계정을-나눠-쓸-때
- 데이터 보기: `axhub tables db-list --app <슬러그>` · 로컬은 `npm run db:psql`.
- **백업·복원은 앱 콘솔의 백업 탭**에서 해요. 복원은 데이터만 되돌려요.

## 4. 파일 저장 (storage)

1. `axhub.yaml` 에 적고 다시 배포해요.
   ```yaml
   storage:
     enabled: true
   ```
2. `STORAGE_ENDPOINT` · `STORAGE_BUCKET` · `STORAGE_ACCESS_KEY` · `STORAGE_SECRET_KEY` 가 자동으로 들어와요.
3. S3 호환이라 `@aws-sdk/client-s3` 로 써요 (설치 필요). **아래 두 옵션은 꼭 넣어요** — 빼면 업로드가 `SignatureDoesNotMatch` 로 실패해요.
   ```ts
   import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3'
   const s3 = new S3Client({
     endpoint: process.env.STORAGE_ENDPOINT,
     region: 'auto',
     credentials: { accessKeyId: process.env.STORAGE_ACCESS_KEY!, secretAccessKey: process.env.STORAGE_SECRET_KEY! },
     requestChecksumCalculation: 'WHEN_REQUIRED',
     responseChecksumValidation: 'WHEN_REQUIRED',
   })
   await s3.send(new PutObjectCommand({ Bucket: process.env.STORAGE_BUCKET, Key: 'uploads/a.png', Body: buffer, ContentType: 'image/png' }))
   ```
- 브라우저에 파일을 보여줄 땐 `@aws-sdk/s3-request-presigner` 의 `getSignedUrl` 로 **잠깐 열리는 주소**를 만들어 넘겨요 (버킷은 비공개).
- 운영과 스테이징이 같은 버킷을 써요. 스테이징 파일은 `staging/` 같은 접두사로 나눠요.

## 5. 알림 · 메일

`@ax-hub/sdk` 에 이미 들어 있어요 (설치 불필요). 토큰과 주소는 배포 때 자동으로 들어와요 — 로컬에선 동작하지 않아요.

```ts
import { createAppMessagingClient } from '@ax-hub/sdk'
const app = createAppMessagingClient()
await app.sendNotification({ to: [userId], title: '결재 요청이 도착했어요', body: '휴가 신청 건', link: '/approvals/123' })
await app.sendMail({ to: [userId], subject: '결재 요청', html: '<p>확인해 주세요.</p>' })
```

- 받는 사람은 **이메일이 아니라 사용자 ID** 예요 — `me()` 의 `user_id`. 한 번에 1~100명.
- 하루 상한: 앱당 알림 5,000건 · 메일 1,000건.

## 6. 웹훅 받기

1. 접수 창구를 만들어요: `axhub relay create --app <슬러그> --name <이름> --target-path /api/hook`
2. 나온 주소를 외부 서비스에 등록해요.
3. `app/api/hook/route.ts` 에서 받아요. 진짜 axhub 를 거쳐 왔는지 서명을 확인해요 (`AXHUB_RELAY_SIGNING_SECRET` 은 자동으로 들어와요).
   ```ts
   import { createHmac, timingSafeEqual } from 'crypto'
   export async function POST(req: Request) {
     const secret = process.env.AXHUB_RELAY_SIGNING_SECRET ?? ''
     const raw = await req.text()
     const got = req.headers.get('x-axhub-signature') ?? ''
     const want = 'sha256=' + createHmac('sha256', secret).update(raw).digest('hex')
     if (!secret || got.length !== want.length || !timingSafeEqual(Buffer.from(got), Buffer.from(want)))
       return new Response('unauthorized', { status: 401 })
     // 같은 전달이 다시 올 수 있어요 — x-axhub-delivery 값으로 한 번만 처리
     return new Response('ok')
   }
   ```

## 7. 로그인 · 권한 · 공개 범위

- **누가 들어왔는지:** `const visitor = await me()` — 이름·이메일·`user_id`·`app_role`·`is_admin`. axhub 문이 요청마다 실어 주는 헤더를 읽어요.
  `authenticated=false` 는 오류가 아니라 **로그인 안 한 정상 상태**예요 → `loginUrl('/')` 로 로그인 버튼.
- **사용자별 데이터:** 테이블에 `user_key` 컬럼을 두고 `visitor.user_id` 로 늘 걸러요. 자동으로 갈라 주지 않아요.
- **공개 범위:** 나만보기 · 일부공개(초대한 사람) · 내부공개(회사 전체) · 외부공개(인터넷). 넓힐 때는 심사가 있고, 좁히는 건 바로 돼요.
  ```bash
  axhub publish --app <슬러그> --visibility invite_only --execute   # invite_only | public | internet
  axhub access invite --app <슬러그> --user <사용자ID> --execute      # 일부공개 앱에 사람 초대
  ```

## 8. 스테이징 · 심사

- 공개된 앱은 운영에 바로 배포되지 않고 **스테이징에서 확인 → 심사 승인 → 운영 반영** 순서로 가요.
- 켜기: `axhub deploy staging enable --app <슬러그> --execute`
- 스테이징 로그: `axhub deploy logs --app <슬러그> --environment staging`

## 9. 회사 데이터 (connector)

- 관리자가 연결해 둔 회사 DB·SaaS 를 **이름으로** 읽어요: `queryConnector({ connector: '이름', sql, params })` (`lib/axhub-server.ts`).
- 사용자 입력은 반드시 `params` 로 — SQL 문자열에 이어붙이지 않아요. PostgreSQL 자리표시자는 `$1`.
- **회사 앱 주소(`{앱}.{회사}.axhub.ai`)에서만** 동작해요. 내가 쓸 수 있는 connector: `axhub connectors mine`.

## 10. 커스텀 도메인

```bash
axhub apps domains add <내도메인> --app <슬러그> --execute   # 나오는 안내대로 DNS 를 등록한 뒤
axhub apps domains verify <도메인ID> --app <슬러그>             # 확인 (도메인ID 는 add 결과에 나와요)
```

## 11. 앱에서 AI 쓰기

- 일반 앱은 AI 를 쓸 때 **키를 비밀값으로** 넣어요 (§2). axhub 가 앱 대신 AI 를 불러 주지는 않아요.
- 개인·회사 공급사 키를 그대로 넣거나, 회사가 **AXRouter** 를 켜 두었다면 회사 키를 써요. 사용량·한도는 회사 콘솔에서 관리돼요.
  ```bash
  axhub axrouter keys issue --name "내 앱"          # 키 값은 이때 한 번만 보여요
  # Anthropic SDK: ANTHROPIC_API_KEY=ax-…  ANTHROPIC_BASE_URL=https://axrouter.ai
  # OpenAI 호환:   api_key=ax-…           base_url=https://axrouter.ai/v1
  ```

## 앱 내리기 · 다시 띄우기

```bash
axhub apps suspend <슬러그> --execute   # 잠깐 내리기 (주소 접속이 막혀요)
axhub apps resume <슬러그> --execute    # 다시 띄우기
```
