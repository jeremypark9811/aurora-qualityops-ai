import type { ReactNode } from 'react'
import { Card, buttonVariants } from '@heroui/react'
import { AppShell } from '@/components/AppShell'
import { CodeBlock, PageHeader, StatusDot } from '@/components/ax'
import { APP_NAME, isAxhubConfigured, me } from '@/lib/axhub-server'
import { isDbConfigured } from '@/lib/db'

export default async function Home() {
  // 방문자 신원 — axhub 문이 요청마다 실어 주는 헤더를 읽어요 (허브 호출 없음).
  const visitor = await me()
  const configured = isAxhubConfigured()
  const dbReady = isDbConfigured()

  const title = visitor.authenticated ? `환영합니다, ${visitor.name || visitor.email}님 👋` : '환영합니다 👋'
  const desc = !configured
    ? '로컬에서 실행 중이에요. axhub 로 배포하면 로그인한 사용자가 여기 표시돼요.'
    : visitor.authenticated
      ? `${APP_NAME} 이 준비됐어요. 이제 화면만 만들면 돼요.`
      : '오른쪽 위에서 로그인하면 이름이 여기 표시돼요.'

  return (
    <AppShell>
      {/* 페이지 = 세로로 40px 간격(gap-10)으로 쌓아요. 바깥 여백은 셸이 이미 잡아 놨어요. */}
      <div className="flex flex-col gap-10">
        <PageHeader
          title={title}
          description={desc}
          actions={
            <a className={buttonVariants({ variant: 'outline' })} href="https://docs.axhub.ai/ko/docs" target="_blank" rel="noreferrer">
              가이드 보기
            </a>
          }
        />

        {/* 다음 할 일 — 코드를 몰라도 Claude Code 에 말로 요청해 이어서 만들 수 있게. */}
        <Card>
          <Card.Header>
            <Card.Title>Claude Code 에 이렇게 요청해 이어서 만드세요</Card.Title>
            <Card.Description>
              axhub 플러그인이 설치된 Claude Code 를 이 폴더에서 열고, 만들고 싶은 것을 말로 요청하면 돼요. 화면을
              만들고, 데이터를 붙이고, 배포까지 해 줘요.
            </Card.Description>
          </Card.Header>
          <Card.Content className="flex flex-col gap-4">
            <ul className="grid list-none grid-cols-1 gap-3 p-0 sm:grid-cols-2">
              {PROMPT_EXAMPLES.map((ex) => (
                <li key={ex.prompt} className="rounded-card border border-default p-4">
                  <p className="t-caption">{ex.label}</p>
                  <p className="t-small mt-1">“{ex.prompt}”</p>
                </li>
              ))}
            </ul>
            {/* 아직 준비가 안 된 사람은 준비 도우미로 — CLI·코딩 도구·플러그인·로그인을 한 번에 해 줘요. */}
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-card bg-muted p-4">
              <div>
                <p className="t-small font-semibold">axhub 를 아직 설치하지 않았나요?</p>
                <p className="t-caption mt-1">준비 도우미가 Claude Code · axhub 플러그인 · 로그인까지 한 번에 준비해 줘요.</p>
              </div>
              <a className={buttonVariants({ variant: 'primary', size: 'sm' })} href={ONBOARDER_URL} target="_blank" rel="noreferrer">
                준비 도우미에서 안내받기
              </a>
            </div>
          </Card.Content>
        </Card>

        {/* 신원 데모 — 실제 앱에선 지우고 원하는 내용을 넣으세요. */}
        <Card>
          <Card.Header>
            <Card.Title>내 정보</Card.Title>
            <Card.Description>
              axhub 문이 요청마다 실어 주는 <Code>X-AxHub-*</Code> 헤더를 읽은 결과예요. 허브에 다시 묻지 않아요.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            {!configured ? (
              <p className="t-small">로컬에는 문(게이트)이 없어서 값이 비어 있어요. 배포하면 채워져요.</p>
            ) : (
              <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
                <Row label="상태">
                  <StatusDot tone={visitor.authenticated ? 'active' : 'muted'}>
                    {visitor.authenticated ? '로그인함' : '로그인 안 함 (정상)'}
                  </StatusDot>
                </Row>
                <Row label="이름">{visitor.name || '—'}</Row>
                <Row label="이메일">{visitor.email || '—'}</Row>
                <Row label="워크스페이스">{visitor.tenant_slug || '—'}</Row>
                <Row label="이 앱에서의 역할">{visitor.app_role || '—'}</Row>
                <Row label="관리자">{visitor.is_admin ? '예' : '아니오'}</Row>
              </dl>
            )}
          </Card.Content>
        </Card>

        <section className="flex flex-col gap-4">
          <h2 className="t-section-title">시작 안내</h2>

          {/* 데이터베이스는 기본으로 붙지 않아요 — 필요할 때 켜는 방식이에요. */}
          <Card>
            <Card.Header>
              <Card.Title>데이터베이스 연결하기</Card.Title>
              <Card.Description>
                {dbReady ? (
                  <>
                    연결돼 있어요. <Code>lib/db.ts</Code> 로 바로 쿼리하면 돼요.
                  </>
                ) : (
                  <>
                    이 앱은 아직 데이터베이스가 없어요. 필요하면 <Code>axhub.yaml</Code> 에서 아래 두 줄의 주석을 풀고 다시
                    배포하세요. 전용 PostgreSQL 이 발급되고 접속 정보가 자동으로 들어와요.
                  </>
                )}
              </Card.Description>
            </Card.Header>
            <Card.Content className="flex flex-col gap-4">
              {dbReady ? (
                <CodeBlock language="tsx" code={DB_EXAMPLE} className="rounded-card bg-muted p-4" />
              ) : (
                <>
                  <CodeBlock language="yaml" code={'database:\n  engine: postgres'} className="rounded-card bg-muted p-4" />
                  <p className="t-small">
                    로컬에서 먼저 해 보려면 <Code>npm run db:up</Code> 으로 Postgres 를 띄우고 <Code>.env.local</Code> 의
                    DATABASE_URL 줄 주석(#)을 지워요. 순서는 <Code>AXHUB.md</Code> §3, 쓰는 법은 <Code>lib/db.ts</Code> 에
                    적혀 있어요.
                  </p>
                </>
              )}
            </Card.Content>
          </Card>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <GuideCard
              title="화면 만들기"
              code="app/page.tsx"
              desc="이 페이지를 고치거나 새 화면을 추가하세요. 사이드바 메뉴는 config/navigation.ts 에 한 줄 더하면 돼요."
            />
            <GuideCard
              title="axhub 기능 켜기"
              code="AXHUB.md"
              desc="파일 저장 · 알림/메일 · 웹훅 · 공개 범위 · 도메인 · 로그 · 되돌리기. 직접 만들기 전에 여기부터 보세요."
            />
            <GuideCard
              title="배포하기"
              code="/axhub:deploy"
              desc="Claude Code 에서 한 줄로 배포해요. 배포 전에 디자인 규칙 검사가 자동으로 돌아요."
            />
          </div>
        </section>

      </div>
    </AppShell>
  )
}

/** 준비 도우미(데스크톱 온보더) 다운로드 페이지. 회사 주소 없이 열리는 공개 화면이에요. */
const ONBOARDER_URL = 'https://axhub.ai/download'

/** 첫 화면에 보여 줄 요청 예시. axhub 플러그인이 알아듣는 말로 적어요. */
const PROMPT_EXAMPLES = [
  { label: '화면 만들기', prompt: '이 axhub 앱에 할 일 목록 화면 만들어줘' },
  { label: '데이터 저장', prompt: 'DB 켜고 입력한 내용이 저장되게 해줘' },
  { label: '회사 데이터 쓰기', prompt: '내 connector 데이터로 대시보드 만들어줘' },
  { label: '배포하기', prompt: 'axhub 에 배포하고 성공했는지 확인해줘' },
]

const DB_EXAMPLE = `import { db, ensureSchema } from "@/lib/db";

await ensureSchema();
await db()\`INSERT INTO todos (user_key, title) VALUES (\${userKey}, \${title})\`;`

/** 문장 속 파일명·명령 — 회색 바탕 고정폭 글자. */
function Code({ children }: { children: ReactNode }) {
  return <code className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-caption-01 text-secondary">{children}</code>
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-default pb-2">
      <dt className="t-caption shrink-0">{label}</dt>
      <dd className="t-small text-right">{children}</dd>
    </div>
  )
}

function GuideCard({ title, code, desc }: { title: string; code: string; desc: string }) {
  return (
    <Card>
      <Card.Header>
        <Card.Title>{title}</Card.Title>
        <Card.Description className="font-mono">{code}</Card.Description>
      </Card.Header>
      <Card.Content>
        <p className="t-small">{desc}</p>
      </Card.Content>
    </Card>
  )
}

/* ─────────────────────────────────────────────────────────────────────────────
 * 🤖 Claude Code / AI 에이전트 — 이 앱 만드는 법 (지우지 말 것)
 *
 * 【디자인】 axhub 콘솔과 같은 스택 — 자세한 규칙·예시는 AGENTS.md 「디자인」.
 *   - 컴포넌트는 @heroui/react (v3) 에서: Card · Button · TextField · Select · Checkbox · Modal · Table · Chip · toast.
 *     v2 문법(<Card><CardBody>, color="primary", onClick) 은 틀린다 — v3 는 Card.Header/Card.Content, onPress.
 *   - 콘솔 공용 조각(PageHeader · StatusDot · CodeBlock · useConfirm …)은 '@/components/ax' 에서.
 *   - 버튼 모양의 링크는 <Link className={buttonVariants({ variant: 'primary' })}>.
 *   - 아이콘은 @phosphor-icons/react ('use client' 파일) / @phosphor-icons/react/ssr (서버 파일).
 *   - 색은 의미 클래스(bg-content, text-muted, border-default, text-danger), 글자는 t-* (t-small, t-caption).
 *     #hex · text-[15px] · text-gray-500 · bg-white 금지. 다른 UI 라이브러리 설치 금지.
 *   - 페이지 = <div className="flex flex-col gap-10"> 안에 <PageHeader> + <Card> 들.
 *   - 바깥 여백·최대 폭은 셸(PageContainer)이 이미 잡았다. 페이지가 또 붙이지 않는다.
 *
 * 【레이아웃】 새 화면을 추가할 때
 *   - components/AppShell.tsx · Shell.tsx 는 건드리지 않는다. 내용만 <AppShell> 안에 넣는다.
 *   - 사이드바 메뉴는 config/navigation.ts 배열에 한 줄 추가한다.
 *
 * 【백엔드】 전부 서버에서 (Server Component / Route Handler / Server Action).
 *
 * 1) 지금 방문자가 누구인지
 *    import { me, loginUrl, logoutUrl } from "@/lib/axhub-server";
 *    const visitor = await me();
 *    // { authenticated, user_id, email, name, app_role, is_admin, tenant_slug, surface }
 *    // authenticated=false 는 오류가 아니라 "로그인 안 됨" 정상 상태 — 로그인 버튼을 보여준다.
 *    // 출처는 axhub 문이 요청마다 실어 주는 X-AxHub-* 헤더 (허브 API 를 다시 부르지 않는다 —
 *    // 퍼블릭·커스텀 도메인에선 허브 쿠키가 없어 sdk.identity.me 는 401 이다).
 *    // "/__axhub/auth/*" 는 플랫폼 예약 경로 — 앱 라우트로 쓰지 않는다.
 *
 * 2) 데이터 저장·조회 · 표준 PostgreSQL
 *    ⚠️ 기본으로는 DB 가 없다. axhub.yaml 의 `database: { engine: postgres }` 주석을 풀고
 *    다시 배포해야 발급된다. 로컬은 `npm run db:up`.
 *    import { db, ensureSchema } from "@/lib/db";
 *    await ensureSchema();                       // 첫 read/write 전에 한 번
 *    // 값은 tagged-template 으로 — 자동 바인딩되어 SQL 인젝션 안전. 문자열 이어붙이기 금지.
 *    await db()`INSERT INTO todos (user_key, title) VALUES (${userKey}, ${title})`;
 *    const rows = await db()<{ id: string; title: string }[]>`
 *      SELECT id::text, title FROM todos WHERE user_key = ${userKey} ORDER BY id DESC LIMIT 50`;
 *    // 새 테이블이 필요하면 lib/db.ts 의 ensureSchema() 에 CREATE TABLE IF NOT EXISTS 를 추가.
 *    // 사용자별로 가르려면 visitor.email(또는 user_id)을 user_key 컬럼으로 쓰고 늘 필터한다.
 *
 * 3) Gateway · 외부 DB/SaaS 조회  (connector 이름으로, parameterized SQL, audit log)
 *    ⚠️ 사용자 쿠키가 필요해 **회사 앱 주소에서만** 동작 — 퍼블릭·커스텀 도메인 앱은 미지원.
 *    import { queryConnector } from "@/lib/axhub-server";
 *    const res = await queryConnector<{ id: number; name: string }>({
 *      connector: "my-db",
 *      sql: "SELECT id, name FROM public.employees WHERE active = $1 LIMIT $2",
 *      params: [true, 10],
 *    });
 *
 * 4) 에러 처리
 *    - DB(lib/db.ts) 호출은 표준 postgres 에러를 던져요 — try/catch 로 감싸요.
 *    - SDK(gateway) 호출은 AxHubError — e.code / e.category / e.requestId 로 분기.
 * ───────────────────────────────────────────────────────────────────────────── */
