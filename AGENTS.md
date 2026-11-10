# AI Agents Guide

이 프로젝트의 **모든 AI 에이전트 행동 규칙** 이에요. Claude Code, Codex, 다른 어떤 AI 도구든 이 파일이 source-of-truth.
한국어 vibe coder 가 좋은 결과를 얻도록 설계됐어요.

## axhub 기능은 먼저 AXHUB.md 를 봐요 (에이전트 필수)

사용자가 "파일 올리게 / 알림 보내줘 / 결제 웹훅 받아줘 / 회사 사람만 쓰게 / 도메인 연결 / 이전 버전으로" 처럼 말하면
**직접 만들기 전에 [AXHUB.md](./AXHUB.md) 의 표를 먼저 봐요.** axhub 가 이미 주는 기능(DB · 파일 저장 · 알림/메일 · 웹훅 relay ·
공개 범위·초대 · 스테이징·심사 · 커스텀 도메인 · 로그 · 되돌리기)은 **설정 + 다시 배포** 로 켜고, 새 서비스·패키지로 다시 만들지 않아요.
- `axhub.yaml` 을 바꾸거나(`database:` · `storage:`) env 를 넣는 일, `--execute` 가 붙는 명령은 **사용자에게 먼저 말하고** 해요.
- 메일·알림에 SendGrid 같은 외부 서비스를 붙이지 말고 `createAppMessagingClient()` (이미 설치된 `@ax-hub/sdk`) 를 써요.
- 파일 저장은 `storage: enabled: true` + S3 호환 (`requestChecksumCalculation/responseChecksumValidation: 'WHEN_REQUIRED'` 필수).

## 사용자
비전공자 한국인 vibe coder. 한국어로 답해요. 코드 용어는 풀어서 설명해요. 결과는 화면으로 확인.

## 디자인 — axhub 디자인 시스템 (에이전트 필수)

이 템플릿은 axhub 콘솔과 **같은 UI 스택**이에요. 화면을 만들 때 아래 규칙을 지켜야 앱들이 콘솔과 같은 모양으로 보여요.

| 층 | 패키지 (이미 설치됨) | 규칙 |
|---|---|---|
| 컴포넌트 | `@heroui/react` **v3** | 버튼·입력·선택·표·모달은 전부 여기서. 직접 `<button className=…>` 을 꾸미지 않아요 |
| 모양·토큰 | `@jocoding-ax-partners/design-system` | CSS 만. 위 컴포넌트를 콘솔처럼 칠하고 의미 토큰을 줘요. import 할 JS 없음 |
| 콘솔 조각 | `@jocoding-ax-partners/react` | 확인창(`useConfirm`)·`PageHeader`·`StatusDot`·`CodeBlock` 등. **`@/components/ax` 에서** 가져와요 |
| 아이콘 | `@phosphor-icons/react` | `'use client'` 파일은 `@phosphor-icons/react`, 서버 파일은 `@phosphor-icons/react/ssr` |
| 배치 | Tailwind 4 | `flex` `grid` `gap-4` `mt-2` 같은 배치에만 |

### ⚠️ HeroUI 는 v3 — v2 문법을 쓰지 마세요

인터넷·학습 데이터의 HeroUI/NextUI 예제는 대부분 v2 라 **틀려요.**

- ❌ `<HeroUIProvider>` · `import { Button } from "@heroui/button"` · `<Card><CardBody>` · `color="primary"` · `onClick` · `<Input label="이름" />`
- ✅ Provider 없음(이미 `components/Providers.tsx` 에 필요한 것만 있음) · `import { Button } from "@heroui/react"` · `<Card><Card.Header><Card.Title>` · `variant="primary"` · **`onPress`** · `<TextField><Label/><Input/></TextField>`
- 모르는 컴포넌트는 순서대로 확인해요: ① heroui MCP 서버(있으면) ② https://v3.heroui.com/docs/react/components/<이름> ③ `node_modules/@heroui/react/dist/components/<이름>/<이름>.d.ts` (설치된 버전 — 셋이 다르면 ③ 이 맞아요)
- design-system 이 더하는 것(`data-color` 등)은 `node_modules/@jocoding-ax-partners/design-system/llms.txt` 에 있어요. 화면 코드를 쓰기 전에 한 번 읽어요.

### 무엇을 쓰나

| 하고 싶은 것 | 쓸 것 |
|---|---|
| 버튼 | `Button` (`variant`: `primary` 기본 · `secondary` · `outline` · `ghost` · `danger` · `danger-soft`, `size`: `sm`/`md`/`lg`, 아이콘만이면 `isIconOnly` + `aria-label`) |
| 버튼 모양의 링크 | `<Link className={buttonVariants({ variant: 'outline' })} href="/x">` (`next/link` + `@heroui/react` 의 `buttonVariants`) |
| 글자 입력 | `TextField` + `Label` + `Input` (여러 줄은 `TextArea`) + `Description` + `FieldError` |
| 고르기 | `Select` (+ `ListBox`), 몇 개뿐이면 `RadioGroup` |
| 체크 · 켜고 끄기 | `Checkbox` · `Switch` |
| 날짜 | `DatePicker` (기간은 `DateRangePicker`) |
| 내용 묶기 | `Card` (`Card.Header` · `Card.Title` · `Card.Description` · `Card.Content` · `Card.Footer`) |
| 목록 표 | `Table` (`Table.ScrollContainer` > `Table.Content` > `Table.Header`/`Table.Body`) |
| 상태 표시 | 배경 있는 알약 `Chip` (`color`: `success`/`warning`/`danger`/`accent`), 점+글자 `StatusDot` (`@/components/ax`) |
| 탭 | `Tabs` |
| 대화상자 · 옆 서랍 | `Modal` · `Drawer` |
| "정말 삭제할까요?" | `useConfirm()` (`@/components/ax`) — `window.confirm` 금지 |
| 저장됐어요 알림 | `toast.success('저장했어요')` / `toast.danger(...)` (`@heroui/react`) — `alert()` 금지 |
| 빈 화면 | `EmptyState` |
| 로딩 | `Spinner` · `Skeleton` |
| 페이지 제목 줄 | `PageHeader` (`@/components/ax`) — `title` · `description` · `actions` |
| 코드·설정 예시 | `CodeBlock` (`@/components/ax`) |
| 아이콘 | `@phosphor-icons/react` (예: `Plus`, `Trash`, `PencilSimple`) — https://phosphoricons.com |

### 색·글자는 의미 토큰으로

- 색: `bg-surface`(회색 바탕) `bg-content`(흰 면) `bg-muted` · `text-default` `text-secondary` `text-muted` `text-subtle` · `border-default` · `text-primary` `bg-primary-soft` · `text-danger` `text-success` `text-warning`
- 글자: `t-page-title` `t-section-title` `t-card-title` `t-body` `t-small` `t-caption` (크기+굵기+색이 한 번에), 크기만은 `text-heading-01~05` `text-body-01~03` `text-caption-01~02`
- 모서리·높이: `rounded-card` `rounded-input` `h-button-md` …
- ❌ `#2d64fa` · `bg-[#eee]` · `text-[15px]` · `text-gray-500` · `bg-white` · `style={{ color: … }}` — 다크 모드에서 그 부분만 색이 안 따라가요.
- ❌ 부탁받지 않은 테두리·그림자·구분선을 더하지 않아요. 컴포넌트 기본 모양을 믿어요.
- ❌ 다른 UI 라이브러리(MUI · antd · Chakra · Mantine · shadcn/ui · Radix · lucide-react · react-icons · HeroUI v2 패키지)를 설치·import 하지 않아요.
- 예외가 꼭 필요하면 같은 줄에 `design-token-allow` 주석. `bash scripts/check-design.sh` 가 위반을 잡고, 배포 전에 자동으로 돌아요.

### 서버 파일 vs 브라우저 파일

- `@heroui/react` — 어디서나 import 돼요. 단 `onPress` 처럼 **함수를 넘기는 곳은 `'use client'` 파일**이어야 해요.
- `@jocoding-ax-partners/react` — **`@/components/ax`** 로 가져와요. 그 패키지는 서버 파일에서 직접 쓰면 빌드가 깨져요 — 직접 import 해도 되는 곳은 `'use client'` 파일뿐이에요(`Shell.tsx`·`Providers.tsx` 처럼). 필요한 이름이 없으면 `components/ax.ts` 에 한 줄 더해요.
- 서버 파일 아이콘은 `@phosphor-icons/react/ssr` 에서 가져오고 `size={16} weight="fill"` 을 직접 넘겨요(서버는 `IconContext` 기본값을 못 읽어요).
- 데이터 읽기는 서버(`page.tsx`), 누르기·입력 같은 상호작용은 작은 `'use client'` 컴포넌트로 나눠요. 저장은 Server Action(`'use server'`) 으로.

### 예시 1 — 입력 폼 (Server Action 으로 저장)

```tsx
'use client'
import { Button, Description, FieldError, Input, Label, TextField } from '@heroui/react'
import { Plus } from '@phosphor-icons/react'

export function TodoForm({ action }: { action: (fd: FormData) => Promise<void> }) {
  return (
    <form action={action} className="flex flex-col gap-4">
      <TextField name="title" isRequired>
        <Label>할 일</Label>
        <Input placeholder="예: 보고서 제출" />
        <Description>50자 이내로 적어요.</Description>
        <FieldError />
      </TextField>
      <Button type="submit"><Plus />추가</Button>
    </form>
  )
}
```

### 예시 2 — 버튼 + 알림

```tsx
'use client'
import { Button, toast } from '@heroui/react'

<div className="flex gap-2">
  <Button onPress={() => toast.success('저장했어요')}>저장</Button>
  <Button variant="outline">취소</Button>
</div>
```

### 예시 3 — 삭제 확인

```tsx
'use client'
import { Button, toast } from '@heroui/react'
import { useConfirm } from '@/components/ax'

export function DeleteButton({ onDelete }: { onDelete: () => Promise<void> }) {
  const confirm = useConfirm()
  return (
    <Button
      variant="outline"
      data-color="danger"
      onPress={async () => {
        const ok = await confirm({ title: '삭제할까요?', description: '지우면 되돌릴 수 없어요.', confirmLabel: '삭제', variant: 'danger' })
        if (!ok) return
        await onDelete()
        toast.success('삭제했어요')
      }}
    >
      삭제
    </Button>
  )
}
```

체크박스는 `Checkbox.Content` 안에 `Checkbox.Control` 과 `Label` 을 함께 넣어요 (밖에 두면 칸과 글자가 세로로 쪼개져요):
`<Checkbox name="done"><Checkbox.Content><Checkbox.Control><Checkbox.Indicator /></Checkbox.Control><Label>완료</Label></Checkbox.Content></Checkbox>`

### 페이지 모양

```tsx
<AppShell>                                   {/* 상단바·사이드바·바깥 여백은 셸이 이미 그려요 */}
  <div className="flex flex-col gap-10">     {/* 섹션 사이 40px */}
    <PageHeader title="할 일" description="한 줄 설명" actions={<Link className={buttonVariants()} href="/todos/new">새로 만들기</Link>} />
    <Card>
      <Card.Header><Card.Title>목록</Card.Title></Card.Header>
      <Card.Content>…</Card.Content>
    </Card>
  </div>
</AppShell>
```

- 회색 바탕 위 흰 카드(`Card`)가 axhub 의 기본 모양이에요. 카드 밖에 내용을 그냥 얹지 마세요.
- 바깥 여백·최대 폭은 셸(`PageContainer`)이 이미 잡았어요. 페이지가 `p-8`·`max-w-*`·`mx-auto` 를 또 붙이지 마세요.

### 건드리지 않는 파일

- `app/axhub.css` — 자동 생성(디자인 시스템 진입점). 고치려면 axhub-template 레포의 `design/axhub.css` 를 고치고 `node scripts/sync-design.mjs`. 이 앱만의 CSS 가 꼭 필요하면 `app/globals.css` 아래에 더해요.
- `components/AppShell.tsx` · `components/Shell.tsx` · `components/Providers.tsx` — 앱 전체 뼈대예요. 내용만 `<AppShell>` 안에 넣어요.
- 다크 모드는 `<html data-theme="dark">` 하나로 바뀌어요 (`app/layout.tsx` 가 시스템 설정을 따라 붙여요). 색을 직접 바꾸지 마세요.

### 화면·메뉴 추가

- 새 화면은 셸 안에 내용만 넣어요.
- 사이드바 메뉴는 `config/navigation.ts` 배열에 한 줄 추가해요 (아이콘은 phosphor 컴포넌트).
- 관리자 화면 메뉴는 `adminOnly: true` 를 붙이면 관리자(`me().is_admin` — 앱 소유자·회사 관리자)가 아닌 사람에게 안 보여요. 메뉴만 숨기는 것이라 그 화면도 서버에서 권한을 따로 확인해요.
- 상단바·사이드바는 이미 제자리에 고정돼 있고(`sticky`) 페이지 전체가 스크롤돼요. 화면 안에 `h-screen`·`overflow-auto` 로 스크롤 상자를 따로 만들지 마세요 — 스크롤이 두 겹이 돼요.
- 좁은 화면 메뉴(서랍)는 `components/Shell.tsx` 가 같은 `config/navigation.ts` 로 그려요.
- 없는 주소는 `app/not-found.tsx`, 화면 오류는 `app/error.tsx` 가 보여줘요. 데이터가 없을 때는 `notFound()` 를 불러요.

### 업무 앱 완성도 — 시제품처럼 보이지 않게

사용자는 이미 잘 만든 SaaS 를 써 봤어요. 아래를 지키면 "만들어 본 앱"이 아니라 "회사에서 쓰는 앱"으로 보여요.

- **앱 얼굴** — `config/navigation.ts` 의 `APP_ICON` 을 앱이 하는 일에 맞는 아이콘으로 바꾸고, 메뉴마다 다른 아이콘을 줘요. 앱 이름은 사람이 읽는 이름(예: "거래처 관리")이에요. `axhub apps create --name` 으로 정하면 배포 때 `APP_NAME` 으로 들어와 셸에 그대로 보여요 — 화면에 이름을 따로 박거나 슬러그(`my-crm`)를 쓰지 않아요.
- **첫 화면은 요약** — 맨 위에 `StatCard`(`@/components/ax`) 3~4개를 `grid grid-cols-2 gap-4 lg:grid-cols-4` 로 놓고(숫자 + 비교 한 줄, 누르면 그 조건의 목록으로 — `StatCard` 는 링크 속성이 없어서 `<Link>` 로 감싸요), 그 아래 "내가 처리할 일"(승인 대기·기한 임박 — 항목마다 바로 처리 버튼)과 최근 활동을 둬요. 비중·추세는 `ProgressBar`·`Meter` 나 너비 %인 막대로 그려요(차트 패키지 설치 금지).
- **목록** — `Table` 위에 상태 `Tabs`(전체·대기·완료처럼, 탭마다 건수) + `SearchField` + `Select` 필터. 행을 누르면 오른쪽 `Drawer` 에서 상세를 보고 바로 처리해요. 금액·수량 열은 오른쪽 정렬 + `tabular-nums`, 상태는 색 있는 `Chip`.
- **사람** — 이름만 쓰지 말고 `Avatar`(이름 첫 글자) + 이름 + 부서로 보여줘요. 사람 고르기는 `ComboBox` 로 이름 검색, 후보와 저장은 회사 구성원 목록 `sdk.tenants.membersDirectory`(가입한 활성 멤버, `userId`)로 해요. 부서 이름은 멤버의 `groupId` 로 `orgDirectory` 에서 찾고, 조직도가 비어 있으면(조직도 연동 없는 회사) 부서를 빼요 — `orgDirectory` 의 `scimUserId` 는 사용자 ID 가 아니라 저장·알림에 못 써요. 저장은 사용자 ID + 그때 이름을 함께(이름이 바뀌거나 퇴사해도 기록이 읽혀요).
- **입력** — 브라우저 기본 `<select>` · `<input type="date">` 대신 `Select` · `DatePicker`. 칸이 많으면 `Card` 로 묶음을 나누고, 저장 버튼은 폼 끝 오른쪽에 둬요.
- **예시 데이터는 진짜처럼** — 사람 6~8명(흔한 한국 이름, 부서 3~4개), 목록마다 12~25건, 최근 90일에 퍼진 날짜, 오늘·이번 주 할 일과 기한 지난 건, 상태가 골고루 섞이게. 예시 사람은 가상 이름으로 저장하되 일부 담당자는 지금 로그인한 사람으로 넣어 "내가 처리할 일"이 비지 않게 하고, 예시 데이터로 알림·메일을 보내지 않아요. 행에 `is_sample` 열을 두고, "예시" 꼬리표를 행마다 붙이지 않아요. 안내와 "예시 데이터 지우기"는 첫 화면 위 작은 `Alert` 한 줄에만 둬요.
- **화면 말투** — 영어 상태값(`pending`)·`ID`·`null`·개발 용어를 화면에 보이지 않아요. 상태와 버튼은 한국어 동사로("승인", "반려", "처리 완료").

```tsx
// 첫 화면 요약 줄 (서버 page.tsx 에서 그대로 써도 돼요)
import Link from 'next/link'
import { StatCard } from '@/components/ax'

<div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
  <Link href="/approvals?status=pending">
    <StatCard label="승인 대기" value="5건" sub="가장 오래된 건 3일 전" />
  </Link>
  <StatCard label="이번 달 사용" value="42일" sub="지난달보다 6일 많아요" />
  <StatCard label="오늘 휴가" value="3명" sub="영업팀 2 · 인사팀 1" />
  <StatCard label="남은 연차 평균" value="9.5일" />
</div>
```

## Stack
Next.js 16 (App Router · RSC · Server Actions) · React 19 · TypeScript strict · Tailwind 4 · HeroUI v3 + axhub design-system · Node 20+ ·
**데이터는 표준 PostgreSQL** (`lib/db.ts`, `DATABASE_URL`) · **인증/식별 · 외부 connector 는 `@ax-hub/sdk 6.x`** (`lib/axhub-server.ts`).

## 5가지 Vibe Coder 프로토콜 (모든 작업에 적용)

1. **Plan first** — 다단계 작업 시작 전, 한국어로 한 줄 plan 보여줘요.
   예: "1. `lib/db.ts` 에 테이블 추가 → 2. `app/page.tsx` 에서 조회·표시 → 3. 결과 확인". 사용자 OK 후 코드.
2. **Verify-then-claim** — UI 변경 후 "되긴 해요" / "should work" 만으로 끝 금지.
   정확히 어디 접속해서 무엇이 보여야 하는지 알려줘요.
   예: "http://localhost:3000 새로고침 → '내 할 일' 카드에 방금 추가한 항목이 보여야 해요. 안 보이면 알려주세요."
   사용자 확인 전엔 "완료" 표시 금지.
3. **No unprompted refactor** — X 요청에 Y / Z 같이 "개선" 금지. 변경한 모든 line 이 X 와 직접 관련.
4. **Honest failure** — 못 만들면 plainly 말해요. "아직 안 풀렸어요. 시도: A, B. 모름: C." 가짜 성공 보고 금지.
5. **Ask before install** — 작은 utility 라도 npm install 전에 "X 추가해도 될까요? 이유: Y" 한 번 물어봐요.
   (단, `@ax-hub/sdk` · `postgres` · `@heroui/react` · `@jocoding-ax-partners/*` · `@phosphor-icons/react` 는 이미 설치돼 있으니 다시 설치 금지. UI 라이브러리는 더 설치하지 않아요.)

## 데이터 = 표준 PostgreSQL (`lib/db.ts`)

> 사용자는 "대화 저장되게 / 주문 목록 보여줘" 처럼 **결과만** 말해요. 이 앱의 데이터는 이 앱 전용
> **PostgreSQL** 에 저장해요 — `lib/db.ts` 가 단일 진입점이에요. 평범한 SQL 을 쓰면 돼요(특별한 API 없음).

### D1. read/write 는 `lib/db.ts` 의 `db()` 로 — 평범한 SQL
```ts
import { db, ensureSchema } from '@/lib/db'
await ensureSchema()                                  // 첫 read/write 전에 한 번 (테이블 정의는 lib/db.ts 에)
// 값은 tagged-template 으로 — 자동 바인딩되어 SQL injection 안전. 문자열 이어붙이기 금지.
await db()`INSERT INTO todos (user_key, title) VALUES (${userKey}, ${title})`
const rows = await db()<{ id: string; title: string }[]>`
  SELECT id::text, title FROM todos WHERE user_key = ${userKey} ORDER BY id DESC LIMIT 50`
```

### D2. 테이블은 `ensureSchema()` 에 `CREATE TABLE IF NOT EXISTS` 로
- 새 테이블/컬럼이 필요하면 `lib/db.ts` 의 `ensureSchema()` 안에 `CREATE TABLE IF NOT EXISTS ...`
  (또는 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) 한 줄을 추가. 별도 마이그레이션 도구 불필요.
- `id`/`created_at` 같은 컬럼도 직접 SQL 로 선언 (자동 추가 같은 마법 없음 — 평범한 Postgres).

### D3. 사용자별 데이터 → `user_key` 컬럼 + 로그인 사용자
- **자동 격리는 없어요.** 자기 데이터만 보이게 하려면 테이블에 `user_key text` 컬럼을 두고,
  모든 쿼리를 `WHERE user_key = ${userKey}` 로 직접 필터해요.
- 로그인 사용자는 `const visitor = await me()` (`@/lib/axhub-server`, 문이 넘긴 `X-AxHub-*` 헤더) → `visitor.email`(또는 `user_id`)을 `user_key` 로. `visitor.authenticated=false` 는 오류가 아니라 익명(정상) — 로그인 버튼(`await loginUrl('/')`)을 보여줘요. `sdk.identity.me()` 로 방문자를 알아내지 마세요 — 퍼블릭·커스텀 도메인에선 401.
  배포 시엔 실제 로그인 사용자, 로컬 단독 실행 땐 `'local-dev'` 로 폴백 (예: `app/page.tsx` 의 `currentUserKey()`).

### D4. 로컬은 docker, 배포는 axhub 가 주입
- **로컬**: `npm run db:up` 으로 Postgres 를 띄우고 `.env.local` 의 `DATABASE_URL` 사용.
  DB 조작은 npm 스크립트 우선 — `db:up` / `db:down`(데이터 유지) / `db:reset`(초기화) / `db:psql`(콘솔).
  최초 세팅은 `npm run setup` (`.env.local` 없으면 예시 복사 + DB 기동).
- **배포**: `axhub.yaml` 의 `database: { engine: postgres }` 선언으로 axhub 가 이 앱 전용 DB 를 발급하고
  `DATABASE_URL` / `DIRECT_DATABASE_URL` 을 자동 주입해요. `isDbConfigured()` 가 false 면 아직 로컬 DB 미설정.

### D5. 코드가 secret(API 키 등)을 쓰면 → axhub env 에 등록 (배포 필수)
`.env.local` 만 채우면 **로컬만** 돌아가요. 배포 환경엔 그 값이 없어 런타임에 `env: <KEY> not found` 로 깨져요.
1. `axhub.yaml` 의 `env` 에 **이름과 scope 만** 선언 (값은 적지 않음). `scope` 는 `build`/`runtime`/`both`:
   ```yaml
   env:
     required:
       - { name: OPENAI_API_KEY, scope: runtime }
   ```
2. 값은 CLI 로 등록 (값은 stdin 으로만 — 명령행 노출 방지):
   ```bash
   printf %s "$OPENAI_API_KEY" | axhub env set OPENAI_API_KEY --app <APP_SLUG> --secret --from-stdin --stage runtime --json
   ```
- `DATABASE_URL` / `DIRECT_DATABASE_URL` 은 DB 를 켜고 배포하면 axhub 가 **자동 주입** — 직접 등록 불필요.
- `APPHUB_*` 는 axhub 가 앱을 만들 때(bootstrap) 코드의 `{{...}}` 자리에 미리 채워요. 템플릿을 직접 내려받아 올린 앱만 `axhub env set` 으로 넣어요.
- 값을 넣거나 바꾼 뒤엔 **다시 배포해야** 적용돼요. `NEXT_PUBLIC_` 로 시작하는 값은 브라우저에 보이니 비밀값에 쓰지 않아요.

## SDK 사용 프로토콜 (인증/식별 · 외부 connector)

> 이 템플릿에서 `@ax-hub/sdk 6.x` 는 **인증/식별**과 **외부 connector(gateway)** 호출에 써요. (앱 데이터는 위 PostgreSQL.)
> 방문자 신원은 `lib/axhub-server.ts` 의 `me()` (문이 넘긴 헤더). 허브 SDK 가 필요한 gateway 는 `makeAxhub()` factory 가 사용자 자격을 처리하되 **회사 앱 주소에서만** 동작해요. raw `fetch()` 로 `api.axhub.ai` 직접 호출 금지.

### S1. 진입점은 factory 만 — 모듈 레벨 클라이언트 금지
- ✅ 매 호출마다 `const sdk = await makeAxhub()`.
- ❌ 파일 최상단에 `const sdk = new AxHubClient({...})` 캐싱 — 사용자 자격이 다음 요청에 누설돼요.
- 이유: 들어온 요청의 `_hub_access` 쿠키마다 다른 사용자. SDK 인스턴스는 그 요청 안에서만 유효.

### S2. 슬러그 하드코딩 금지 — helper / 상수 사용
- ✅ tenant 만 필요하면 `const t = await makeTenant()` → `t.apps.list()`.
- ❌ `sdk.tenant('my-tenant')` 처럼 슬러그 문자열 박지 마요 — `lib/axhub-server.ts` 의 `TENANT`/`APP_SLUG` 상수가 환경별로 달라요.
- ❌ flat 호출 (`sdk.apps.create(...)` 같이 tenant 스코프 없이) 금지 — `TenantSlugRequiredError`. (단, `sdk.identity.*` 는 tenant 불필요 — 예외.)

### S3. 서버 전용 — 클라이언트 컴포넌트에서 import 금지
- ✅ `app/page.tsx`, `app/api/.../route.ts`, Server Action 안에서만 `lib/axhub-server.ts` / `lib/db.ts` import.
- ❌ `"use client"` 컴포넌트에서 `me` / `makeAxhub` / `db` import — `next/headers` · DB 드라이버는 server-only 라 빌드 깨져요.
- 클라이언트에서 백엔드가 필요하면 Route Handler (`app/api/.../route.ts`) 또는 Server Action 거치게.

### S4. 에러는 `error.code` / `instanceof` 로 분기 — 메시지 문자열 매칭 금지
- ✅ `if (err instanceof AxHubError && err.code === 'slug_taken')`.
- ❌ `if (err.message.includes('이미 존재'))` — 백엔드 메시지는 변경 가능, machine-readable 한 건 `code`/`category` 뿐.
- 자주 쓰는 클래스: `ValidationError`, `UnauthenticatedError`, `PermissionDeniedError`, `NotFoundError`, `ConflictError`, `AxHubError`(catch-all).
- DB(`lib/db.ts`) 호출은 표준 postgres 에러를 던져요 — try/catch 로 감싸요.

### S5. Gateway query — 외부 DB/SaaS 조회는 `queryConnector()` 로
> **이 기능은 핵심.** 외부 시스템(자체 PostgreSQL/MySQL/SaaS connector) 데이터를 안전하게 읽어요.
> 모든 호출은 audit log 에 기록되고 connector 권한 정책으로 게이트돼요. 직접 DB 접속 금지.
> (이 앱 자체의 데이터 저장과는 별개 — 그건 위 `lib/db.ts` PostgreSQL.)

> ⚠️ **gateway 는 tenant 경로에 UUID 를 요구해요 (slug 거부 → 400 invalid_format).** slug 기반 `makeTenant()` 로는 안 돼요.
> `lib/axhub-server.ts` 의 `makeGateway()` (me() 로 tenant UUID 자동 스코프) / `queryConnector()` 를 쓰세요.

#### 기본 사용 — connector "이름" 으로 (UUID 자동 resolve)
```ts
import { queryConnector } from '@/lib/axhub-server'
const res = await queryConnector<{ id: number; name: string }>({
  connector: 'my-db',          // connector 이름 (gateway.me.connectors() 의 .name) — UUID 아님, helper 가 resolve
  sql: 'SELECT id, name FROM public.employees WHERE active = $1 LIMIT $2',  // postgres 네이티브 $n placeholder — '?' 는 백엔드에서 500(internal_error)
  params: [true, 10],          // ✅ 항상 parameterized · $1,$2 순서대로 — SQL injection 방지
})
// res.rows: 컬럼명으로 매핑된 객체 배열 · res.rowCount · res.columns
// 정책 deny 는 in-band 플래그가 아니라 throw — try/catch 로 PermissionDeniedError 분기.
```

> **SDK 6.x gateway 모델:** connector 에 **활성 grant** 가 있어야 **session** 을 열고, SQL 은 그 session 으로 실행해요.
> `queryConnector()` 가 (grant 보유 connector resolve → session open → query → session close) 를 한 번에 감싸요.

#### 저수준 — 직접 session 을 다룰 때
```ts
import { makeGateway } from '@/lib/axhub-server'
const gw = await makeGateway()                       // tenant UUID 로 스코프된 gateway (makeTenant 아님!)
const connectors = await gw.me.connectors()          // 배열 — 내가 grant 가진 connector 만. .find(c => c.name === 'my-db')
const session = await gw.sessions.create({ connectorId: connectors[0].id })  // grant 없으면 NotFoundError
try {
  const res = await gw.query.run({ sessionId: session.id, sql: 'SELECT 1' })
} finally {
  await gw.sessions.end(session.id)                  // 끝나면 반드시 닫기
}
```
- `gw.me.connectors()` / `gw.me.connectorResources(id)` / `gw.me.grants()` 는 **배열** 반환 (member-scoped — 내 grant 기준).
- REST connector 는 `gw.invoke({ sessionId, method, path })` 로 프록시 (SQL 아님).
- connector 등록·관리(create/update/delete)는 콘솔 관리자 작업 — SDK gateway 표면에 없어요.

#### 절대 규칙 (Gateway)
- ✅ **PostgreSQL SQL 테이블명은 스키마 포함 필수** — `FROM schema.table`. `FROM table` 만 쓰면 `AxHubError(internal_error)` 발생.
- ✅ `queryConnector()` 우선 — connector 이름만 넘기면 grant resolve·session 생명주기를 helper 가 처리.
- ✅ **항상 parameterized SQL** — placeholder + `params: [...]`. 사용자 입력을 SQL 문자열에 직접 박지 마요.
- ✅ `connector` / `sql` 은 코드 상수 — 사용자 값은 `params` 로만 (권한 우회·injection 방지).
- ✅ 결과 cap 은 SQL `LIMIT` 로 — gateway 가 무한 결과를 막지 않아요.
- ✅ **정책 deny 는 throw** — `try/catch` 로 `PermissionDeniedError` / `UnauthenticatedError`(session 만료) / `NotFoundError`(grant 없음) 분기.
- ❌ `makeTenant()` (slug) 로 gateway 호출 — **400 invalid_format**. `makeGateway()` / `queryConnector()` 만.
- ❌ connector UUID 하드코딩 — connector 이름으로 넘기면 자동 resolve.
- ❌ session 을 안 닫고 방치 — 저수준 사용 시 `finally` 로 `sessions.end()`. (`queryConnector()` 는 자동.)
- ❌ 모듈-레벨에 gateway 결과·session 캐싱 — 자격·데이터가 사용자별로 달라요.

## Framework-Specific Rules (Next.js)

- `lib/db.ts` · `lib/axhub-server.ts` 는 **Server-side 전용**. `"use client"` 컴포넌트에서 import 금지.
- 새 백엔드/DB 호출은 항상 Server Component · Route Handler (`app/api/.../route.ts`) · Server Action 경유.
- Tailwind class 는 길어도 분리하지 말고 인라인 유지 (vibe coder 가 한 곳에서 다 보는 게 편함).
- 변경 보고: `file:line` 형식.

## 절대 규칙 (negative-phrased)

- DO NOT `lib/db.ts` · `lib/axhub-server.ts`(server 전용)를 `"use client"` 컴포넌트에서 import.
- DO NOT DB 쿼리에 사용자 입력을 문자열로 이어붙이기 — 항상 tagged-template `db()\`... ${value} ...\`` 로 바인딩.
- DO NOT raw `fetch()` 로 `api.axhub.ai` 직접 호출 — 신원은 `me()`, gateway 는 `queryConnector()` 경유.
- DO NOT `/__axhub/auth/*` 경로를 앱 라우트로 사용 — 플랫폼 예약.
- DO NOT 모듈 레벨에 `AxHubClient` 인스턴스를 캐싱 (사용자 자격 누설).
- DO NOT slug/tenant 를 코드에 하드코딩 — `TENANT` / `APP_SLUG` 상수 또는 helper 사용.
- DO NOT `AxHubError.message` 한국어 문자열로 분기 — `code` / `category` / `instanceof` 만.
- DO NOT Gateway `query.run({ sql })` 에 사용자 입력을 그대로 박기 — 항상 `params: [...]` (parameterized SQL).
- DO NOT 사용자 세션 쿠키(`_hub_access`)/토큰을 응답 본문·로그에 노출.
- DO NOT `.env.local` 커밋 (`.gitignore` 막혀있지만 force-add 도 금지).
- DO NOT 사용자 동의 없이 destructive git (`reset --hard`, `push --force`, `branch -D`).
- DO NOT 새 npm 패키지 사용자 확인 없이 설치 (`@ax-hub/sdk` · `postgres` · UI 패키지는 이미 들어가 있어 재설치 금지). 다른 UI 키트·아이콘 팩은 묻지도 말고 쓰지 않아요.
- DO NOT HeroUI v2 문법(`@heroui/<컴포넌트>` 패키지, `HeroUIProvider`, `CardBody`, `onClick`) — 이 앱은 v3 (`@heroui/react`).
- DO NOT 생색(#hex)·생크기(`text-[15px]`)·Tailwind 기본 팔레트(`text-gray-500`, `bg-white`) — 의미 토큰만.
- DO NOT `npm run build`·배포를 사용자가 묻기 전에 실행 (느리고 결과물이 바뀌어요). 고친 뒤 확인용 `npx tsc --noEmit` · `npm run check:design` 은 스스로 돌려도 돼요 — Verify-then-claim 의 일부예요.

## 신뢰 모델 (1-line)

- **데이터**: `lib/db.ts` 의 `db()` / `ensureSchema()` — `DATABASE_URL`(런타임, prepare:false) · `DIRECT_DATABASE_URL`(마이그레이션). 로컬은 docker compose, 배포는 axhub 주입.
- **인증/식별**: `lib/axhub-server.ts` 의 `me()` / `loginUrl()` / `logoutUrl()` — axhub 문이 요청마다 실어 주는 `X-AxHub-*` 헤더를 `headers()` 로 읽어요. 허브에 다시 묻지 않아요. **gateway**: 같은 파일의 `makeAxhub` / `makeTenant` / `makeGateway` / `queryConnector` — 들어온 요청의 `_hub_access` 쿠키를 SDK JWT 로 박아요 (**회사 앱 주소에서만** 동작).

## 빠른 레퍼런스

```ts
// ── 데이터 (표준 PostgreSQL) — Server Component / Route Handler / Server Action 안에서 ──
import { db, ensureSchema } from '@/lib/db'
await ensureSchema()
await db()`INSERT INTO todos (user_key, title) VALUES (${userKey}, ${title})`
const rows = await db()<{ id: string; title: string; done: boolean }[]>`
  SELECT id::text, title, done FROM todos WHERE user_key = ${userKey} ORDER BY id DESC LIMIT 50`

// ── 방문자 신원 (사용자별 데이터의 user_key) ──
import { me, loginUrl, logoutUrl } from '@/lib/axhub-server'
const visitor = await me()            // { authenticated, user_id, email, name, app_role, is_admin, tenant_slug, surface }
// visitor.authenticated=false → 익명(정상): <a href={await loginUrl('/')}>로그인</a>
// 로그아웃: await logoutUrl('/') — 회사 앱이면 null(콘솔 로그아웃 안내)

// ── 조직 구성원 조회 (tenant_member 권한이면 가능, sdk 6.1+) ──
// ⚠️ 사용자 쿠키가 필요해 회사 앱 주소에서만 동작 (gateway 와 같음). 슬러그는 TENANT 상수를 그대로 넘겨요.
import { makeAxhub, TENANT } from '@/lib/axhub-server'
const sdk = await makeAxhub()                         // 요청마다 새로 (모듈 레벨 캐싱 금지)
const org = await sdk.tenants.orgDirectory(TENANT)    // { departments: [{ name, members }], unassigned } — SCIM 조직도, 미가입자는 joined:false
const dir = await sdk.tenants.membersDirectory(TENANT) // { items: [{ userId, name, role, groupId? }], total } — 가입한 활성 멤버 (email 없음)

// ── Gateway · 외부 DB/SaaS connector 조회 (connector 이름으로; helper 가 grant·session·UUID 처리) ──
import { queryConnector } from '@/lib/axhub-server'
const employees = await queryConnector<{ id: number; name: string }>({
  connector: 'my-db',     // connector 이름 (UUID 아님) — 활성 grant 가 있어야 보여요
  sql: 'SELECT id, name FROM public.employees WHERE active = $1 LIMIT $2',  // ⚠️ PostgreSQL: 스키마 포함 + 네이티브 $n placeholder('?' 는 500)
  params: [true, 10],
})
// 정책 deny 는 throw — try/catch 로 PermissionDeniedError 분기 (in-band allowed 플래그 없음)

// ── 에러 처리 ──
import { AxHubError } from '@ax-hub/sdk'
try {
  /* DB 또는 SDK 호출 */
} catch (err) {
  if (err instanceof AxHubError) console.error(err.code, err.category, err.requestId) // SDK(identity/gateway)
  else console.error(err)                                                             // 표준 postgres 에러
}
```

## 배포

`/axhub:deploy` (Claude Code) 또는 `axhub deploy create --app <slug> --execute` (`--execute` 없으면 미리보기). 사용자 명시 요청 후에만. 앱 슬러그는 `axhub apps list`.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
