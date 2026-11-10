#!/usr/bin/env bash
# 디자인 토큰 회귀 검사.
#
#   bash scripts/check-design.sh              레포 전체 (모든 템플릿)
#   bash scripts/check-design.sh <템플릿폴더>  한 템플릿만 (배포 전 ci 용)
#
# 스택: Tailwind 4 + HeroUI v3(@heroui/react) + @jocoding-ax-partners/design-system (design/axhub.css)
#
# 잡는 것
#   1) 생색  — #hex, bg-[#...], style="color:#..."
#   2) 생크기 — text-[15px] 같은 arbitrary 크기
#   3) Tailwind 기본 팔레트 — text-gray-500, bg-white 등 (토큰 대신 쓰면 색이 안 따라옴)
#   4) 다른 UI 키트 — MUI·antd·Chakra·Mantine·shadcn·Radix·lucide·HeroUI v2 경로 등.
#      컴포넌트는 @heroui/react(v3), 콘솔 조각은 @jocoding-ax-partners/react, 아이콘은 @phosphor-icons/react 만.
#
# 예외가 필요하면 같은 줄에 `design-token-allow` 주석을 다세요.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCOPE="${1:-}"
cd "$ROOT"

if [ -n "$SCOPE" ]; then
  DIRS=("$SCOPE")
elif [ -d nextjs-axhub ] && [ -d design ]; then
  # 템플릿 레포 — 모든 템플릿을 검사
  DIRS=(nextjs-axhub)
else
  # 앱 안 — 자기 소스만 검사
  DIRS=(.)
fi

# CSS 는 검사하지 않아요 (토큰 값은 design-system 패키지가 정의해요).
COMMON=(--include=*.tsx --include=*.ts --include=*.astro --include=*.jsx --include=*.js --include=*.mjs
        --exclude=check-design.sh
        --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.next --exclude-dir=prompts)

found=0

# scan 제목 패턴 안내 [허용 패턴]
#   주석 줄은 건너뛰어요 — 판정은 «파일:줄:» 바로 뒤에서만 해요(https:// 같은 문자열을 주석으로 오인하지 않게).
scan() {
  local title="$1" pattern="$2" hint="$3" allow="${4:-}"
  local hits=""
  for d in "${DIRS[@]}"; do
    [ -d "$d" ] || continue
    local out
    out=$(grep -rnE "$pattern" "${COMMON[@]}" "$d" 2>/dev/null \
          | grep -v "design-token-allow" \
          | grep -vE "^[^:]+:[0-9]+:[[:space:]]*(\*|//|\{?/\*|<!--)" || true)
    [ -n "$allow" ] && out=$(printf '%s\n' "$out" | grep -vE "$allow" || true)
    [ -n "$out" ] && hits+="$out"$'\n'
  done
  if [ -n "$hits" ]; then
    echo
    echo "✗ $title"
    echo "$hits" | sed '/^$/d' | head -30
    echo "  → $hint"
    found=1
  fi
}

scan "생색(hex) 사용" \
  "(#[0-9a-fA-F]{3,8}\b|(bg|text|border|fill|stroke)-\[#[0-9a-fA-F]+\])" \
  "var(--primary) 같은 토큰이나 text-muted / bg-content 클래스를 쓰세요."

scan "생크기 사용" \
  "(text|size|w|h|min-w|min-h|max-w|max-h|p[xytblrse]?|m[xytblrse]?|gap(-[xy])?|space-[xy]|rounded(-[a-z]+)?|leading|tracking|top|bottom|left|right|inset(-[xy])?)-\[[0-9]+(\.[0-9]+)?(px|rem)\]" \
  "t-small · text-body-03 · text-caption-01 · rounded-card · h-button-md 처럼 디자인 시스템 토큰 클래스를 쓰세요."

scan "Tailwind 기본 팔레트 사용" \
  "(text|bg|border|ring|divide)-(gray|slate|zinc|neutral|stone|blue|red|green|yellow|indigo|violet)-[0-9]{2,3}\b|(bg|text)-(white|black)\b" \
  "토큰 클래스(text-muted, bg-content, border-default, text-danger)를 쓰세요. 색이 다크 모드를 따라가야 해요."

scan "다른 UI 라이브러리 사용" \
  "(from|import)[[:space:]]*['\"](@mui/|@material-ui/|antd|@ant-design/|@chakra-ui/|@mantine/|@radix-ui/|@headlessui/|@nextui-org/|react-bootstrap|lucide-react|react-icons|@tabler/icons|@heroicons/|@/components/ui/)|(HeroUIProvider|NextUIProvider)" \
  "컴포넌트는 @heroui/react (v3), 콘솔 조각은 @/components/ax, 아이콘은 @phosphor-icons/react 에서 가져오세요. HeroUI v3 는 Provider 가 필요 없어요."

# HeroUI v2 는 기능별 패키지(@heroui/button 등)로 나뉘어 있었어요. v3 는 @heroui/react · @heroui/styles 둘뿐이에요.
scan "HeroUI v2 패키지 사용" \
  "['\"]@heroui/[a-z0-9-]+" \
  "HeroUI v3 는 @heroui/react 에서 가져와요. @heroui/button 같은 v2 패키지는 쓰지 마세요." \
  "['\"]@heroui/(react|styles)(['\"/])"

scan "브라우저 기본 대화상자 사용" \
  "(^|[^A-Za-z_.])(window\.)?(confirm|alert|prompt)\([[:space:]]*['\"\`]" \
  "확인은 @/components/ax 의 useConfirm, 알림은 @heroui/react 의 toast 를 쓰세요."

if [ "$found" -eq 0 ]; then
  echo "✓ 디자인 토큰 규칙 통과."
fi
exit "$found"
