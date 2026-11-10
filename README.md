# nextjs-axhub

axhub 위에서 바로 굴러가는 **Next.js 16 + React 19 + Tailwind 4 + HeroUI v3** 템플릿이에요. 화면은 axhub 콘솔과 같은 디자인 시스템(`@jocoding-ax-partners/design-system`)으로 그려져요.
**Claude Code** 로 바이브코딩하면서 axhub 에 한 줄 명령으로 배포할 수 있게 미리 세팅돼 있어요.

> **axhub 로 할 수 있는 것** — DB · 파일 저장 · 알림/메일 · 웹훅 · 권한·공개 · 스테이징 · 도메인 · 로그·되돌리기 를 켜는 법은 [AXHUB.md](./AXHUB.md) 한 곳에 모아 뒀어요. 기능을 직접 만들기 전에 먼저 보세요.

## 0. 누가 쓰면 좋아요

비전공자, 비개발자, 기획자, 사무직, 디자이너 — 코드를 직접 한 줄도 안 짜더라도 AI 한테
"이런 화면 만들어줘" 만 부탁하면 알아서 굴러가도록 디자인됐어요.

## 1. 5분 안에 시작

```bash
# 1) 이 템플릿만 내 컴퓨터로 가져오기 (npm 깔려 있어야 함, Node 20+ 권장)
npx degit jocoding-ax-partners/axhub-template/nextjs-axhub my-app
cd my-app

# 2) 의존성 설치
npm install

# 3) 환경변수 파일 만들기 (처음 한 번)
npm run setup                 # .env.example → .env.local 복사. DB 는 기본으로 꺼져 있어요 (Docker 필요 없음)
# DB·파일 저장·알림 같은 axhub 기능은 필요할 때 켜요 → AXHUB.md

# 4) 로컬 서버 띄우기
npm run dev
# http://localhost:3000 에 접속
```

## 2. 바이브코딩 흐름

1. Claude Code 를 열어요.
2. "메인 페이지에 입력 폼이랑 결과 카드 넣어줘" 같은 자연어 요청을 던져요.
3. AI 가 `app/page.tsx` 같은 파일을 고쳐요.
4. 저장하면 브라우저가 자동 새로고침 — 결과 확인.
5. 마음에 들면 다음 기능, 안 들면 다시 부탁.

## 3. 개발(dev) 환경

로컬에서 `npm run dev` 로 도는 환경 이야기예요. 배포(프로덕션)와 뭐가 다른지도 여기서 정리해요.

### 3-1. 핫리로드 (Fast Refresh)

`npm run dev` 는 Turbopack dev 서버예요. 파일을 저장하면 **재시작 없이 즉시** 브라우저에 반영돼요
(React 컴포넌트 상태도 대부분 유지). 별도 설정 필요 없어요.

- 반영이 안 되거나 화면이 이상하게 꼬이면: dev 서버 끄고 `.next` 폴더 삭제 후 `npm run dev` 재시작.
  (Mac/Linux: `rm -rf .next` · Windows PowerShell: `Remove-Item -Recurse -Force .next`)
- `lib/db.ts` 의 DB 커넥션 풀은 핫리로드를 견디도록 dev 에서 재사용돼요 — 오래 개발해도 커넥션이 안 새요.

### 3-2. 로컬 DB 다루기

전부 npm 스크립트로 준비돼 있어요 (내부는 docker compose):

| 명령 | 하는 일 |
|------|---------|
| `npm run setup` | `.env.local` 없으면 예시 복사 + Postgres 기동 (최초 1회용) |
| `npm run db:up` | 로컬 Postgres 기동 (localhost:5432) |
| `npm run db:down` | 정지 — **데이터는 유지**돼요 |
| `npm run db:reset` | 정지 + **데이터 전부 삭제** 후 재기동 (초기화) |
| `npm run db:psql` | 실행 중인 DB 에 psql 콘솔로 접속 |

테이블은 `lib/db.ts` 의 `ensureSchema()` 가 자동 생성해요 (`CREATE TABLE IF NOT EXISTS`) —
마이그레이션 파일이나 별도 명령 없이, 스키마를 고치고 저장하면 다음 요청 때 반영돼요.
테이블 구조를 크게 바꿔서 꼬였다면 `npm run db:reset` 이 제일 빨라요.

### 3-3. dev vs 프로덕션

| | 로컬 dev (`npm run dev`) | 배포 (axhub) |
|---|---|---|
| 실행 방식 | Turbopack 즉석 컴파일 + 핫리로드 | `next build` standalone → `node server.js` |
| `NODE_ENV` | `development` | `production` (Dockerfile 이 고정) |
| DB | docker compose Postgres (`.env.local`) | axhub 발급 전용 DB (`DATABASE_URL` 자동 주입) |
| 로그인 사용자 | 없음(문이 없음) → `'local-dev'` 폴백 | 문이 넘긴 헤더 → `me()` (`visitor.email`) |
| gateway (`queryConnector`) | ❌ 세션 쿠키가 없어 미동작 | ✅ **회사 앱 주소에서만** (퍼블릭·커스텀 도메인 ❌) |

- 로컬엔 axhub 문이 없어 방문자가 항상 익명이에요 — 사용자 키가 `'local-dev'` 로 폴백되고, 실제 로그인은 배포 후 확인하세요.
- gateway(connector 조회)는 사용자 세션 쿠키가 필요해서 로컬에선 안 되고, 배포해도 **회사 앱 주소에서만** 동작해요 (§4-B).
- 배포 전에 프로덕션 모드로 미리 검증하고 싶으면: `npm run build && npm start`.

## 4. 데이터 저장 (표준 PostgreSQL)

이 앱의 데이터는 **이 앱 전용 PostgreSQL** 에 저장해요. `lib/db.ts` 가 단일 진입점이고, 평범한 SQL 을 쓰면 돼요.
**DB 는 기본으로 꺼져 있어요.** 켜는 순서(로컬·배포)는 [AXHUB.md §3 DB 켜기](./AXHUB.md#3-db-켜기) 를 따라요. 로컬은 `npm run db:up` + `.env.local` 의 `DATABASE_URL` 주석 해제, 배포는 `axhub.yaml` 의 `database:` 주석 해제 후 다시 배포 → axhub 가 `DATABASE_URL` 을 자동으로 넣어 줘요.

```ts
// 예: Server Action / Route Handler 안에서
import { db, ensureSchema } from "@/lib/db";

await ensureSchema();                                  // 테이블 정의는 lib/db.ts 에 (CREATE TABLE IF NOT EXISTS)
// 값은 tagged-template 으로 — 자동 바인딩되어 SQL injection 안전.
await db()`INSERT INTO todos (user_key, title) VALUES (${userKey}, ${title})`;
const rows = await db()<{ id: string; title: string }[]>`
  SELECT id::text, title FROM todos WHERE user_key = ${userKey} ORDER BY id DESC LIMIT 50`;
```

사용자별로 데이터를 가르려면 테이블에 `user_key` 컬럼을 두고 로그인 사용자로 필터해요 (아래 §4-A).

> ⚠️ `lib/db.ts` · `lib/axhub-server.ts` 는 **Server-side 전용**이에요. `"use client"` 컴포넌트에서 import 하면 빌드가 깨져요.

### 4-A. 로그인 사용자 알기 (axhub 신원 계약)

axhub 에 배포된 앱은 **허브에 "이 사람 누구야?" 라고 다시 묻지 않아요.** 앱 앞의 문(ingress 게이트)이 통과시킨 요청마다 사용자 정보를 헤더로 실어 주고, 앱은 그걸 **읽기만** 해요. 회사 앱(`{앱}.{회사}.axhub.ai`) · 퍼블릭 앱(`{앱}.axhub.app`) · 커스텀 도메인 모두 같은 계약이에요.

> 왜 허브에 묻지 않나요? 허브 로그인 쿠키는 `axhub.ai` 계열 주소에만 실려요. 퍼블릭·커스텀 도메인은 다른 주소라 브라우저가 쿠키를 안 보내니, 허브 `/api/v1/me` 나 `sdk.identity.me` 로 방문자를 알아내는 방식은 **구조적으로 안 돼요.** 문이 넘기는 헤더는 주소 종류와 무관해요.

### ① 문이 넘기는 헤더 (앱이 사용자를 아는 계약)

| 헤더 | 값 |
|---|---|
| `X-AxHub-User-ID` | 사용자 UUID. **빈 문자열 = 익명 = 정상 상태** |
| `X-AxHub-User-Email` | 이메일 — **base64(UTF-8)**, 디코드해서 써요 |
| `X-AxHub-User-Name` | 이름 — **base64(UTF-8)**, 디코드해서 써요 |
| `X-AxHub-App-Role` | `owner` / `platform_admin` / `tenant_admin` / `app_member` / `tenant_member` / `guest` (모르는 값은 최소 권한으로) |
| `X-AxHub-Is-Admin` | `true` / `false` |
| `X-AxHub-Tenant-Slug` | 앱을 소유한 워크스페이스 슬러그 |
| `X-AxHub-Surface` | `tenant`(회사·퍼블릭·커스텀 모두) / `admin` / `public` |

값은 문이 **매 요청 덮어써요** — 클라이언트가 헤더를 흉내 내도 지워져요. 그래서 앱은 검증 없이 믿고 읽으면 돼요.

### 이 템플릿에서는

서버는 요청 헤더를 직접 볼 수 있어요. `lib/axhub-server.ts` 의 `me()` 가 `next/headers` 의 `headers()` 에서 위 헤더를 읽어 객체로 돌려줘요. 허브 호출도, SDK 도 필요 없어요.

```tsx
// app/page.tsx (Server Component) 또는 Route Handler / Server Action
import { me, loginUrl, logoutUrl } from "@/lib/axhub-server";

export default async function Page() {
  const visitor = await me();   // { authenticated, user_id, email, name, app_role, is_admin, tenant_slug, surface }
  if (!visitor.authenticated) return <a href={await loginUrl("/")}>axhub 로 로그인</a>;   // 익명 = 정상 상태
  const logout = await logoutUrl("/");                                                      // 회사 앱이면 null
  return <p>환영합니다, {visitor.name || visitor.email}님 {logout ? <a href={logout}>로그아웃</a> : "(콘솔에서 로그아웃)"}</p>;
}
```

> `visitor.email`(또는 `user_id`)을 데이터 테이블의 `user_key` 로 쓰면 사용자별 격리가 돼요.
> `lib/axhub-server.ts` 는 server-only — `"use client"` 컴포넌트에서 import 하면 빌드가 깨져요.

### ② 로그인 버튼은 시작점으로

로그인 버튼 href 는 `{API_BASE}/custom-domain-auth/start?target=<현재 주소 전체>` 예요 (헬퍼 `loginUrl()`). 시작점이 주소가 회사·퍼블릭·커스텀 중 어느 것인지 알아서 판정하고, 로그인이 끝나면 `target` 으로 돌려보내요. 앱은 주소 종류를 몰라도 돼요.

### ③ 앱 로그아웃은 이 앱 주소의 세션만 끊어요

로그아웃 href 는 앱 주소의 `/__axhub/auth/logout?return_to=/` 예요 (헬퍼 `logoutUrl()`). **이 앱 주소의 세션만** 끊고 axhub 콘솔 로그인은 유지돼요. 그래서 "들어올 때 axhub 로그인 요구" 가 켜진 앱은 콘솔에 로그인된 사용자가 다시 자동으로 들어와요 — 정상이에요. 회사 앱에는 끊을 앱 세션이 없어서 헬퍼가 `null` 을 돌려줘요 → 버튼을 숨기고 "콘솔에서 로그아웃하세요" 로 안내해요.

### ④ 콘솔 로그아웃은 앱 세션을 즉시 끊지 않아요

콘솔에서 로그아웃해도 이미 열린 앱 주소의 세션은 최대 12시간 남아 있을 수 있어요. 반면 **접근 권한**(앱 비활성화·계정 정지·공개 범위 변경)은 문이 매 요청 판정하므로 즉시 반영돼요.

### ⑤ 익명은 오류가 아니에요

"들어올 때 로그인 요구" 가 꺼진 앱은 로그인 안 한 방문자도 들어와요. 그때 헤더는 전부 빈 값이고 헬퍼는 `authenticated: false` 를 돌려줘요. 이건 **"로그인 안 됨" 이라는 정상 상태**예요 — 오류 문구 대신 로그인 버튼을 보여주세요.

### ⑥ 예약 경로

`/__axhub/auth/*` 는 플랫폼이 가로채는 예약 경로예요 (콜백·로그아웃). **앱 라우트로 쓸 수 없어요.**

### 4-B. Gateway query — 외부 DB / SaaS 조회

> ⚠️ gateway 는 **사용자별 grant** 를 따지므로 사용자 세션 쿠키(`_hub_access`)로 허브를 불러야 해요. 브라우저는 그 쿠키를 회사 앱 주소(`{앱}.{회사}.axhub.ai`)에만 보내요 → **회사 앱에서만 동작**하고 퍼블릭(`axhub.app`)·커스텀 도메인 앱에선 안 돼요. 방문자 신원(§4-A)과는 별개예요.

axhub Gateway 는 자체 PostgreSQL / MySQL / SaaS connector 를 안전하게 조회시켜 줘요. 모든 호출이 audit log 에
기록되고, connector 권한 정책으로 게이트돼요. **직접 DB 접속 금지** — 항상 SDK 의 `gateway.query` 만.

```ts
// 예: app/api/employees/route.ts
import { queryConnector } from "@/lib/axhub-server";

export async function GET() {
  // connector "이름" 으로 호출 — grant·session·UUID 스코프는 queryConnector 가 알아서 처리해요.
  const res = await queryConnector<{ id: number; name: string }>({
    connector: "my-db",          // connector 이름 (gateway.me.connectors() 의 .name) — 활성 grant 필요
    sql: "SELECT id, name FROM employees WHERE active = $1 LIMIT $2",  // postgres 네이티브 $n placeholder — '?' 는 백엔드에서 500(internal_error)
    params: [true, 10],          // ✅ 항상 parameterized · $1,$2 순서대로 (injection 방지)
  });
  return Response.json({ rows: res.rows, rowCount: res.rowCount });
}
```

- `connector` 는 connector "이름" — `queryConnector` 가 `gateway.me.connectors()` 로 UUID 를 resolve 해요 (활성 grant 가 있는 connector 만 보여요). ⚠️ gateway 는 tenant 경로에 UUID 가 필요해 slug 기반 `makeTenant()` 로는 안 돼요 (helper 가 `me()` 로 tenant UUID 를 잡아줘요).
- `connector` / `sql` 은 코드 상수 — 사용자 입력은 반드시 `params` 로 분리 (권한 우회·injection 방지). 결과 cap 은 SQL `LIMIT`.
- **정책 deny 는 throw** — `try/catch` 로 `PermissionDeniedError` (정책 거부) / `UnauthenticatedError` (session 만료) / `NotFoundError` (grant 없음) 분기. in-band `res.allowed` 플래그는 더 이상 없어요. (SDK 6.x: grant 기반 session 모델.)

## 5. axhub 에 배포

### A. Claude Code 사용자

```
/axhub:deploy
```

배포 미리보기 카드 → 동의 → 끝. 빌드 진행 상황 자동으로 한국어로 안내해줘요.

### B. CLI 직접

```bash
# 한 번만: axhub 콘솔에서 앱 등록 후 슬러그 복사
axhub apps list                                   # 내 앱 목록 · 슬러그 확인
axhub deploy create --app my-app-slug --execute   # --execute 가 없으면 미리보기만 해요
axhub deploy status --app my-app-slug --watch     # 진행 상황
axhub deploy logs --app my-app-slug --follow      # 앱 로그 (안 뜰 때 원인 찾기)
```

`axhub.yaml` 을 새로 쓰거나 고칠 때는 `axhub.yaml.example` 에 axhub.yaml 에서 쓸 수 있는 필드와 제약을 모두 적어뒀으니 먼저 참고하세요.

빌드는 repo 의 `Dockerfile`(`output:"standalone"` → `node server.js`)로 떠요. `package-lock.json` 이 있으면 `npm ci` 로 잠긴 버전 그대로 설치하니, 패키지를 추가하거나 바꿨다면 바뀐 `package-lock.json` 도 함께 커밋하세요. 잠금 파일과 `package.json` 이 어긋나면 빌드가 실패해요.

## 6. 환경변수 / 설정

| 변수 | 용도 |
|------|------|
| `DATABASE_URL` | 앱 데이터 PostgreSQL (런타임). 로컬은 docker compose, 배포는 axhub 주입 |
| `DIRECT_DATABASE_URL` | 스키마 초기화/마이그레이션용 (직결). 로컬은 비우면 `DATABASE_URL` 로 폴백 |
| `APPHUB_API_URL` | Hub API origin (`https://api.axhub.ai`) — 로그인/gateway |
| `APPHUB_APP_SLUG` | 내 앱 슬러그 (`ax-talent-war-jeremy`) |
| `APPHUB_TENANT` | 내 테넌트 슬러그 (`lounge`) |

`DATABASE_URL`/`DIRECT_DATABASE_URL` 은 DB 를 켜고 배포하면 axhub 가 **자동으로 넣어 줘요.** `APPHUB_*` 값은 axhub 로 앱을 만들 때(bootstrap) 코드의 `{{...}}` 자리에 **미리 채워져요** — 템플릿을 직접 내려받아 올렸다면 `axhub env set` 으로 넣어요. 로컬은 비워 두면 "로컬 실행 중" 으로 동작해요. axhub 연결에는 API key 가 없어요 — 인증은 들어온 요청의 세션 쿠키 포워딩으로.

## 7. 자주 막히는 곳

| 증상 | 해결 |
|------|------|
| `npm install` 실패 | Node 버전 20+ 인지 `node -v` 확인 |
| DB 연결 실패 (`ECONNREFUSED ... 5432`) | Docker Desktop 실행 확인 후 `npm run db:up` |
| `db:up` 이 `port is already allocated` | 5432 를 다른 Postgres 가 쓰는 중 — `docker-compose.dev.yml` 의 ports 를 `"5433:5432"` 로 바꾸고 `.env.local` 의 DATABASE_URL 포트도 5433 으로 |
| 테이블/데이터가 꼬임 | `npm run db:reset` — ⚠️ 로컬 데이터 전부 삭제돼요 |
| 저장해도 화면에 반영이 안 됨 | dev 서버 끄고 `.next` 폴더 삭제 후 `npm run dev` 재시작 (§3-1) |
| `axhub deploy` 가 "앱을 못 찾아요" | `axhub apps` 로 슬러그 다시 확인 |
| 빌드 통과한 것 같은데 페이지가 빈 화면 | Server Component 에서 `isAxhubConfigured()` 출력해서 설정 확인 |
| `next/headers` import 에러 | `"use client"` 컴포넌트에서 `lib/axhub-server` 를 import 했는지 확인 — server 전용 |
| `TenantSlugRequiredError` 떨어짐 | `sdk.apps.*` 처럼 flat 호출 말고 `makeTenant()` 거치세요 — tenant 슬러그 자동 주입 |
| `AxHubClient requires tokenType` 에러 | 직접 `new AxHubClient({ token })` 만들 때 발생. 그냥 `makeAxhub()` 쓰세요 — tokenType 자동 |
| 배포했는데 항상 "로그인하지 않았어요" | 정상일 수 있어요(§4-A ⑤). 로그인 버튼으로 시작점에 가 보세요. 로그인 뒤에도 그대로면 `/api/...` 가 아닌 페이지 요청에서 `headers()` 로 `x-axhub-user-id` 가 오는지 확인 |
| `queryConnector` 가 401 / "멤버가 아니에요" | 퍼블릭·커스텀 도메인 앱에선 사용자 쿠키가 없어 미지원 — 회사 앱 주소에서 확인 |
| Tailwind class 가 안 먹음 | Tailwind 4 는 설정 파일 없이 프로젝트 폴더를 알아서 훑어요. `node_modules` 안 패키지 클래스만 `app/axhub.css` 의 `@source` 로 추가돼 있어요 — 값이 없는 클래스(`text-gray-500` 대신 `text-muted`)인지 먼저 확인 |

## 8. 관련 자료

- [axhub 가이드](https://github.com/jocoding-ax-partners/axhub)
- [Next.js 16 docs](https://nextjs.org/docs)
- [Tailwind 4 docs](https://tailwindcss.com/docs)
- [HeroUI v3 컴포넌트](https://v3.heroui.com/docs/react/components) — v2 문서와 섞지 마세요

## 신뢰 모델 (이 템플릿)

이 (Next.js) 템플릿은 **server-side**.

- **데이터**: `lib/db.ts` 의 `db()` / `ensureSchema()` 가 표준 PostgreSQL 에 붙어요. `DATABASE_URL`(런타임, `prepare:false`) ·
  `DIRECT_DATABASE_URL`(마이그레이션). 로컬은 docker compose, 배포는 axhub 가 전용 DB 발급 + 주입.
- **인증/식별**: `lib/axhub-server.ts` 의 `me()` / `loginUrl()` / `logoutUrl()` — axhub 문이 요청마다 실어 주는 `X-AxHub-*`
  헤더를 `next/headers` 의 `headers()` 로 읽어요 (§4-A). 허브 API 에 다시 묻지 않아요. 정적 API key 안 써요.
- **gateway(connector)**: 같은 파일의 `makeAxhub` / `makeTenant` / `makeGateway` / `queryConnector` — 들어온 요청의 `_hub_access` 쿠키를
  `@ax-hub/sdk 6.x` JWT 로 박아 *그 사용자 자격*으로 호출해요. 사용자 쿠키가 실리는 **회사 앱 주소에서만** 동작(§4-B).
  모듈-레벨 client 캐시 금지 — 매 요청마다 factory.

## 9. 라이선스

MIT — 마음껏 쓰세요.
