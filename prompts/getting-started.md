# 시작용 프롬프트 모음

처음 vibe coding 할 때 그대로 복붙하거나 살짝 바꿔서 AI 한테 던져요.

## 1. 첫 화면 만들기

```
app/page.tsx 메인 화면을 [내가 만들고 싶은 서비스 한 줄 설명] 의 첫인상에 맞게 바꿔줘.
- 제목 큰 거 하나
- 설명 문단 하나
- 클릭 가능한 버튼 1개 (눌러도 아직 동작 안 해도 됨)
- HeroUI 컴포넌트와 디자인 토큰으로 깔끔하게 (AGENTS.md 「디자인」), 모바일에서도 안 깨지게
```

## 2. axhub Hub API 호출하는 페이지

```
/me 라우트 만들어줘. lib/axhub-server.ts 의 me() 를 Server Component 에서 호출해서
로그인 사용자 정보(이름·이메일·app_role)를 카드로 보여줘.
로그인 안 했으면(authenticated=false) 오류 대신 loginUrl('/') 로 가는 로그인 버튼을 보여줘.
```

## 3. 입력 폼 + 저장 (앱 데이터 = 표준 Postgres)

```
app/feedback 라우트에 피드백 입력 폼 만들어줘. Server Action 으로 lib/db.ts 의 db() 를 써서
Postgres 에 저장해줘. 먼저 lib/db.ts 의 ensureSchema() 에 feedback 테이블을
(CREATE TABLE IF NOT EXISTS feedback (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 user_key text NOT NULL, message text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()))
추가하고, insert 는 db()`INSERT INTO feedback (user_key, message) VALUES (${userKey}, ${message})`.
userKey 는 me() 의 email (익명은 'anonymous', 로컬은 'local-dev'). 저장 성공하면 "감사합니다" 표시.
```

## 3-A. Gateway query — 외부 DB 조회 페이지

```
app/employees 라우트 만들어줘. lib/axhub-server.ts 의 queryConnector() 로
const res = await queryConnector({ connector: "my-db",
sql: "SELECT id, name FROM employees WHERE active = $1 LIMIT $2", params: [true, 20] })
(placeholder 는 postgres 네이티브 $n — '?' 는 백엔드에서 500 으로 떨어져)
호출해서 res.rows 를 테이블로 렌더. connector 는 "이름" 으로 넘기면 helper 가 grant·session·UUID 를 자동 처리해.
connector / sql 은 코드 상수로 (사용자 입력은 반드시 params 로). 정책 deny 는 throw 라 try/catch 로 안내.
AxHubError 는 .code 로 분기 (PermissionDeniedError / UnauthenticatedError).
(이 앱 자체 데이터 저장은 위 3번 — lib/db.ts Postgres. gateway 는 *외부* DB 읽기 전용.)
```

## 4. 디자인 폴리싱

```
app/page.tsx 디자인을 "조코딩 AX 파트너스" 브랜드 톤에 맞게 다듬어줘.
색은 보라/파랑 계열, 폰트는 시스템 산세리프, 여백 넉넉하게, 모서리 부드럽게.
```

## 5. 배포 직전 체크리스트

```
배포 전에 점검해줘:
- console.log 남은 거 있나?
- 환경변수 미설정인 곳에서 죽는 코드 있나?
- "use client" 컴포넌트가 lib/axhub-server.ts import 하는 곳 있나? (위험 — 서버 전용)
- raw fetch 로 api.axhub.ai 를 직접 호출하는 곳 있나? (반드시 SDK 경유)
- 모듈 최상단에서 new AxHubClient() 캐싱하는 곳 있나? (사용자 자격 누설 위험)
- AxHubError.message 한국어 문자열로 분기하는 곳 있나? (.code/.category 만)
- public/ 에 안 쓰는 이미지 있나?
```
