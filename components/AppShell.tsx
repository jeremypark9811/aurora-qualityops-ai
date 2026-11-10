import type { ReactNode } from 'react'
import { buttonVariants } from '@heroui/react'
import { APP_NAME, isAxhubConfigured, loginUrl, logoutUrl, me } from '@/lib/axhub-server'
import { Shell } from './Shell'

/**
 * 앱 전체 뼈대 — 상단바 + 사이드바 + 본문. axhub 콘솔과 같은 골격이에요 (그리는 건 components/Shell.tsx).
 * 이 파일은 서버에서 방문자 정보를 읽어 상단바 오른쪽(좁은 화면은 서랍 아래) 로그인 영역을 만들어요.
 *
 * 화면을 추가할 땐 이 파일이 아니라 <AppShell> 안에 내용을 넣으세요.
 * 메뉴를 늘리려면 config/navigation.ts 를 고치세요.
 */
export async function AppShell({ children }: { children: ReactNode }) {
  // 방문자 신원 — axhub 문이 요청마다 실어 주는 헤더를 읽어요 (허브 호출 없음).
  const visitor = await me()
  const configured = isAxhubConfigured()
  const loginHref = configured ? await loginUrl('/') : ''
  // 회사 앱은 끊을 앱 세션이 없어 null 이에요. 그땐 콘솔 로그아웃을 안내해요.
  const logoutHref = configured ? await logoutUrl('/') : null

  const account = !configured ? (
    <span className="t-caption">로컬 실행 중</span>
  ) : visitor.authenticated ? (
    <>
      {/* 회사 앱은 logoutHref 가 null — 버튼처럼 보이는 문구 대신 이름에 설명만 붙여요. */}
      <span className="t-small" title={logoutHref ? undefined : '이 앱은 axhub 콘솔 로그인을 그대로 써요. 로그아웃은 콘솔에서 하세요.'}>
        {visitor.name || visitor.email}
      </span>
      {logoutHref && (
        <a className={buttonVariants({ variant: 'outline', size: 'sm' })} href={logoutHref}>
          로그아웃
        </a>
      )}
    </>
  ) : (
    // 로그인은 플랫폼 경로(/__axhub/auth/*)로 페이지째 이동해야 해서 <a> 에 버튼 모양만 입혀요.
    <a className={buttonVariants({ variant: 'primary', size: 'sm' })} href={loginHref}>
      axhub 로 로그인
    </a>
  )

  return (
    <Shell appName={APP_NAME} account={account} isAdmin={visitor.is_admin}>
      {children}
    </Shell>
  )
}
