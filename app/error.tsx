'use client'

import Link from 'next/link'
import { useEffect } from 'react'
import { Button, Card, buttonVariants } from '@heroui/react'

/**
 * 화면을 그리다 오류가 나면 Next.js 기본 화면 대신 이 화면이 보여요.
 * "다시 시도" 는 같은 화면을 다시 그려요 (일시적인 DB·네트워크 오류는 대부분 이걸로 풀려요).
 *
 * 브라우저 쪽 컴포넌트라 AppShell(서버 전용)을 쓸 수 없어요 — 그래서 가운데 카드만 보여줘요.
 * 오류 내용은 사용자에게 보여주지 않고 콘솔에만 남겨요 (DB 주소·쿼리가 새지 않게).
 */
export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="grid min-h-screen place-items-center px-5">
      <Card className="w-full max-w-xl items-center text-center">
        <Card.Header className="items-center">
          <Card.Title>문제가 생겼어요</Card.Title>
          <Card.Description>잠시 뒤 다시 시도해 주세요. 계속되면 아래 번호를 관리자에게 알려 주세요.</Card.Description>
          {error.digest && <p className="t-caption mt-2 font-mono">오류 번호 {error.digest}</p>}
        </Card.Header>
        <Card.Footer className="justify-center gap-2">
          <Button onPress={reset}>다시 시도</Button>
          <Link className={buttonVariants({ variant: 'outline' })} href="/">
            홈으로
          </Link>
        </Card.Footer>
      </Card>
    </div>
  )
}
