// axhub 서버 전용 헬퍼 (Next.js Server Component / Route Handler / Server Action).
// 클라이언트 컴포넌트에서 import 금지 — next/headers 는 server-only.
//
// ① 사용자 신원 — 허브에 다시 묻지 않아요.
//    axhub 문(ingress 게이트)이 이 앱으로 통과시킨 요청마다 사용자 정보를 X-AxHub-* 헤더로 실어 줘요.
//    me() 는 headers() 에서 그걸 읽기만 해요 — 회사·퍼블릭(axhub.app)·커스텀 도메인 어디서든 똑같아요.
//    (허브 SDK identity.me 를 사용자 쿠키로 부르던 옛 방식은 허브 쿠키가 안 실리는 퍼블릭·커스텀 도메인에서
//    구조적으로 안 돼서 폐기했어요.)
//    loginUrl()/logoutUrl() 은 플랫폼이 정한 주소를 조립만 해요.
//
// ② 외부 connector(gateway) 조회 — 사용자 자격으로 허브 API 를 불러야 해요.
//    ⚠️ gateway 는 사용자별 grant 를 따지므로 앱 토큰으로 대신할 수 없고, 사용자 쿠키(_hub_access)가 필요해요.
//    브라우저는 그 쿠키를 회사 앱 주소({앱}.{회사}.axhub.ai)에만 보내요 → queryConnector 는 **회사 앱에서만** 동작해요.
//    퍼블릭·커스텀 도메인 앱은 connector 조회가 안 돼요 (신원 확인은 ①로 되고요).
//
// 이 파일은 신원·connector 만 담당해요. 앱 자체 데이터 저장은 표준 PostgreSQL — lib/db.ts 를 쓰세요 (DATABASE_URL).
//
// 사용:
//   const me = await me()                                   // { authenticated, user_id, email, name, ... }
//   const { rows } = await queryConnector({ connector: 'my-db', sql: 'SELECT ... LIMIT $1', params: [100] })
//
// 설정값은 axhub bootstrap 이 배포 시 {{...}} placeholder 를 치환해 박아요.
// 로컬에서 직접 돌릴 땐 .env 의 APPHUB_* 가 우선해요.
import { cookies, headers } from 'next/headers'
import { AxHubClient, type TenantScopedClient, type TenantGatewayClient, type GatewayQueryResult } from '@ax-hub/sdk'

const API_BASE = process.env.APPHUB_API_URL || 'https://api.axhub.ai'
export const APP_SLUG = process.env.APPHUB_APP_SLUG || 'ax-talent-war-jeremy'
export const TENANT = process.env.APPHUB_TENANT || 'lounge'
const APP_NAME_RAW = process.env.APPHUB_APP_NAME || 'ax-talent-war-jeremy'

const isSet = (v: string): boolean => Boolean(v) && !v.includes('{{')

// 환경값 + tenant/app slug 가 모두 placeholder 치환됐는지 확인.
// false 면 SDK 호출 직전에 명시적 에러로 끊고 사용자에게 axhub 배포 / .env 안내.
/** 상단바에 보여줄 앱 이름. 배포 시 실제 이름으로 치환돼요. */
export const APP_NAME = APP_NAME_RAW.includes('{{') ? '내 앱' : APP_NAME_RAW

export function isAxhubConfigured(): boolean {
  return isSet(API_BASE) && isSet(APP_SLUG) && isSet(TENANT)
}

// ── ① 사용자 신원 ─────────────────────────────────────────────────────────────

// 문이 넘기는 헤더를 그대로 옮긴 모양. authenticated=false 는 "로그인 안 됨" 정상 상태예요 (오류 아님).
export type AxhubMe = {
  authenticated: boolean
  user_id: string
  email: string
  name: string
  // owner / platform_admin / tenant_admin / app_member / tenant_member / guest (모르는 값은 최소 권한으로 취급)
  app_role: string
  is_admin: boolean
  // 앱을 소유한 워크스페이스 슬러그
  tenant_slug: string
  // tenant(회사·퍼블릭·커스텀 도메인 모두) / admin / public
  surface: string
}

export const ANONYMOUS: AxhubMe = {
  authenticated: false,
  user_id: '',
  email: '',
  name: '',
  app_role: '',
  is_admin: false,
  tenant_slug: '',
  surface: '',
}

// email/name 은 UTF-8 → base64 로 실려요.
function decodeBase64Utf8(v: string | null): string {
  if (!v) return ''
  try {
    return Buffer.from(v, 'base64').toString('utf8')
  } catch {
    return ''
  }
}

// 현재 방문자. 요청 스코프 밖(빌드 등)이거나 로컬 dev(문이 없음)면 익명이에요.
// 값은 문이 매 요청 덮어쓰므로 클라이언트가 위조할 수 없어요.
export async function me(): Promise<AxhubMe> {
  let h: Awaited<ReturnType<typeof headers>>
  try {
    h = await headers()
  } catch {
    return ANONYMOUS
  }
  const user_id = h.get('x-axhub-user-id') ?? ''
  return {
    authenticated: user_id !== '',
    user_id,
    email: decodeBase64Utf8(h.get('x-axhub-user-email')),
    name: decodeBase64Utf8(h.get('x-axhub-user-name')),
    app_role: h.get('x-axhub-app-role') ?? '',
    is_admin: h.get('x-axhub-is-admin') === 'true',
    tenant_slug: h.get('x-axhub-tenant-slug') ?? '',
    surface: h.get('x-axhub-surface') ?? '',
  }
}

// 이 요청이 들어온 앱 origin (https://{host}). 프록시 뒤라 x-forwarded-* 를 우선 봐요.
async function requestOrigin(): Promise<string> {
  try {
    const h = await headers()
    const host = h.get('x-forwarded-host') ?? h.get('host') ?? ''
    const proto = h.get('x-forwarded-proto') ?? 'https'
    return host ? `${proto}://${host}` : ''
  } catch {
    return ''
  }
}

// 로그인 버튼 href. 시작점이 회사·퍼블릭·커스텀 주소를 알아서 판정하고 로그인 뒤 target 으로 돌려보내요.
// returnTo 는 이 앱 안의 경로 — 로그인 후 돌아올 화면 (서버 컴포넌트는 자기 경로를 모르니 페이지가 넘겨 줘요).
export async function loginUrl(returnTo: string = '/'): Promise<string> {
  const target = `${await requestOrigin()}${returnTo.startsWith('/') ? returnTo : `/${returnTo}`}`
  return `${API_BASE.replace(/\/+$/, '')}/custom-domain-auth/start?target=${encodeURIComponent(target)}`
}

// 허브의 등록 도메인 (api.axhub.ai → axhub.ai). 회사 앱 주소({앱}.{회사}.axhub.ai)는 이 계열이에요.
function hubBaseDomain(): string {
  try {
    return new URL(API_BASE).hostname.split('.').slice(-2).join('.')
  } catch {
    return ''
  }
}

// 회사 앱(허브 도메인 계열)인지. 회사 앱은 허브 세션을 그대로 쓰므로 끊을 앱 세션이 없어요.
export async function isTenantHostApp(): Promise<boolean> {
  const base = hubBaseDomain()
  if (!base) return false
  let hostname = ''
  try {
    hostname = new URL(await requestOrigin()).hostname
  } catch {
    return false
  }
  return hostname === base || hostname.endsWith(`.${base}`)
}

// 로그아웃 링크. 이 앱 주소의 세션만 끊고 콘솔 로그인은 유지돼요 — "들어올 때 로그인 요구" 가 켜진 앱이면
// 콘솔에 로그인된 사용자는 다시 자동으로 들어와요(정상). 회사 앱은 null — 버튼을 숨기고 콘솔 로그아웃을 안내하세요.
// returnTo 는 이 앱 안의 상대 경로만 받아요.
export async function logoutUrl(returnTo: string = '/'): Promise<string | null> {
  if (await isTenantHostApp()) return null
  return `/__axhub/auth/logout?return_to=${encodeURIComponent(returnTo)}`
}

// ── ② 허브 SDK (connector/gateway · 회사 앱 전용) ──────────────────────────────

// 들어온 요청의 _hub_access 쿠키 → JWT. 요청 스코프 밖(빌드 등)에서는 빈 문자열.
async function readHubAccessToken(): Promise<string> {
  try {
    return (await cookies()).get('_hub_access')?.value ?? ''
  } catch {
    return ''
  }
}

// per-user 응답이 Next.js fetch cache 에 묻혀 다른 요청과 섞이지 않도록 모든 호출을 no-store 로.
const noStoreFetch: typeof fetch = (input, init) =>
  fetch(input, { ...(init ?? {}), cache: 'no-store' })

// 요청별 SDK 인스턴스. 절대 모듈 레벨에 캐싱 금지 (사용자 자격 혼선).
// 방문자 신원은 여기가 아니라 me() 예요 — identity.me 를 이걸로 부르지 마세요 (퍼블릭·커스텀 도메인에선 401).
export async function makeAxhub(): Promise<AxHubClient> {
  if (!isAxhubConfigured()) {
    throw new Error(
      'axhub SDK 가 설정되지 않았어요. axhub 로 앱을 만들면(bootstrap) 자동으로 채워져요. 직접 올린 앱이라면 axhub env set 으로 넣어요. ' +
        '로컬에서 직접 실행 중이라면 .env.local 의 APPHUB_API_URL / APPHUB_APP_SLUG / APPHUB_TENANT 를 채워 주세요.',
    )
  }
  const token = await readHubAccessToken()
  return new AxHubClient({
    baseUrl: API_BASE,
    // 토큰이 없으면 NoAuth 로 떨어져 401 이 자연스럽게 surface 돼요.
    ...(token ? { token, tokenType: 'jwt' as const } : {}),
    defaultTenantSlug: TENANT,
    fetch: noStoreFetch,
  })
}

// tenant 만 잡힌 클라이언트가 필요할 때 (apps.list, tenants.* 등).
export async function makeTenant(): Promise<TenantScopedClient> {
  const sdk = await makeAxhub()
  return sdk.tenant(TENANT)
}

// Gateway 전용 스코프. ⚠️ gateway 엔드포인트는 tenant 경로에 *UUID* 를 요구해요 (slug 거부 → 400 invalid_format).
// slug 기반인 makeTenant() 로는 gateway 가 안 돼요. 사용자 자격의 identity.me 로 tenant UUID 를 받아 스코프해요
// (이 호출은 tenant UUID 를 얻기 위한 것 — 회사 앱 주소에서만 사용자 쿠키가 있어 성공해요).
export async function makeGateway(): Promise<TenantGatewayClient> {
  const sdk = await makeAxhub()
  const me = await sdk.identity.me()
  const tenant = me.tenants?.find((t) => t.tenantSlug === TENANT)
  if (!tenant) {
    throw new Error(
      `현재 로그인 사용자가 tenant '${TENANT}' 의 멤버가 아니에요. ` +
        'gateway 는 이 tenant 의 UUID 가 필요해요 — APPHUB_TENANT 설정과 로그인 계정을 확인해 주세요. ' +
        '(퍼블릭·커스텀 도메인 앱에선 사용자 쿠키가 없어 connector 조회가 안 돼요 — 회사 앱 주소에서만 지원)',
    )
  }
  return sdk.tenant(tenant.tenantId).gateway
}

// 외부 DB/SaaS connector 조회 — connector "이름" 으로 호출하면 UUID 를 자동 resolve 해요 (UUID 하드코딩 불필요).
// gateway 함정(tenant UUID 스코프 · grant 기반 session · connector UUID · parameterized SQL)을 전부 감싼 편의 helper.
//
// SDK 3.x gateway 모델: connector 에 활성 grant 가 있어야 session 을 열 수 있고, SQL 은 그 session 으로 실행해요.
// 이 helper 가 (grant 보유 connector resolve → session open → query → session close) 를 한 번에 처리해요.
//
//   const { rows } = await queryConnector<{ id: number; name: string }>({
//     connector: 'my-db',          // connector 이름 (gateway.me.connectors() 의 .name) — UUID 아님
//     sql: 'SELECT id, name FROM public.employees WHERE active = $1 LIMIT $2',  // ⚠️ PostgreSQL: 스키마 포함 + 네이티브 $n placeholder('?' 는 백엔드에서 500)
//     params: [true, 100],         // ✅ 항상 parameterized · $1,$2 순서대로 — 사용자 입력을 sql 문자열에 직접 박지 마요
//   })
//   // rows: 컬럼명으로 매핑된 객체 배열 · rowCount · columns 메타
//   // 정책 deny 는 in-band 플래그가 아니라 throw — PermissionDeniedError(403) / 세션 만료는 UnauthenticatedError(401) 로 분기.
export async function queryConnector<Row extends Record<string, unknown> = Record<string, unknown>>(input: {
  connector: string
  sql: string
  params?: unknown[]
}): Promise<GatewayQueryResult<Row>> {
  const gw = await makeGateway()
  // me.connectors() 는 현재 사용자가 활성 grant 를 가진 connector 만 반환해요 (grant 없으면 목록에 안 보여요).
  const connectors = await gw.me.connectors()
  const connector = connectors.find((c) => c.name === input.connector)
  if (!connector) {
    const names = connectors.map((c) => c.name).join(', ') || '(없음 — 이 사용자가 활성 grant 를 가진 connector 가 없어요)'
    throw new Error(`connector '${input.connector}' 를 찾지 못했어요. 사용 가능: ${names}`)
  }
  // grant 기반 session 을 열고, 끝나면 반드시 닫아요 (finally).
  const session = await gw.sessions.create({ connectorId: connector.id })
  try {
    return await gw.query.run<Row>({
      sessionId: session.id,
      sql: input.sql,
      params: input.params ?? [],
    })
  } finally {
    // best-effort close — 이미 만료/종료된 session 의 close 실패는 조회 결과에 영향 없어요.
    await gw.sessions.end(session.id).catch(() => {})
  }
}
