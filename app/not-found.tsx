import Link from 'next/link'
import { Card, buttonVariants } from '@heroui/react'
import { AppShell } from '@/components/AppShell'

/**
 * 없는 주소로 들어왔을 때 보이는 화면. 코드에서 notFound() 를 불러도 여기로 와요.
 *   import { notFound } from 'next/navigation'
 *   if (!row) notFound()
 */
export default function NotFound() {
  return (
    <AppShell>
      <Card className="mx-auto w-full max-w-xl items-center text-center">
        <Card.Header className="items-center">
          <p className="t-caption">404</p>
          <Card.Title>페이지를 찾을 수 없어요</Card.Title>
          <Card.Description>주소가 바뀌었거나 지워진 페이지예요. 왼쪽 메뉴에서 다시 찾아보세요.</Card.Description>
        </Card.Header>
        <Card.Footer>
          <Link className={buttonVariants({ variant: 'primary' })} href="/">
            홈으로
          </Link>
        </Card.Footer>
      </Card>
    </AppShell>
  )
}
