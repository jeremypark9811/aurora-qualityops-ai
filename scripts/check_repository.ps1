param([switch]$SkipHistory)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Push-Location -LiteralPath $repoRoot
$ignoreProbe = $null
try {
    $problems = [System.Collections.Generic.List[string]]::new()
    # Test the committed ignore file without this checkout's .git/info/exclude.
    $ignoreProbe = Join-Path $repoRoot ('instance/ignore-check-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $ignoreProbe -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repoRoot '.gitignore') -Destination (Join-Path $ignoreProbe '.gitignore')
    git -C $ignoreProbe init --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create isolated ignore check.' }
    $mustIgnore = @(
        '.env', '.env.local', '.env.production', '.env.production.local',
        'instance/qualityops.db', 'instance/session.key', 'backup.sqlite3',
        'private.pem', 'private.key', 'credentials.json', 'token.json',
        '.claude/settings.local.json', '.codex/hooks.json', '.agents/hooks.json',
        '.codex/auth.json', '.axhub/state.json', '.venv/pyvenv.cfg',
        '__pycache__/app.pyc', '.pytest_cache/state', 'logs/server.log'
    )
    foreach ($candidate in $mustIgnore) {
        git -C $ignoreProbe -c 'core.excludesFile=' check-ignore --no-index --quiet -- $candidate
        if ($LASTEXITCODE -ne 0) { $problems.Add("Not ignored: $candidate") }
    }
    foreach ($candidate in @('.env.example','app.py','requirements.txt','templates/index.html','static/qualityops.js','.vscode/tasks.json')) {
        git -C $ignoreProbe -c 'core.excludesFile=' check-ignore --no-index --quiet -- $candidate
        if ($LASTEXITCODE -eq 0) { $problems.Add("Required source ignored: $candidate") }
    }

    $patterns = [ordered]@{
        'OpenAI key' = 'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}'
        'GitHub token' = '(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{40,})'
        'AWS access key' = '(?:AKIA|ASIA)[A-Z0-9]{16}'
        'Google API key' = 'AIza[0-9A-Za-z_-]{35}'
        'Private key' = '-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'
        'Slack token' = 'xox[baprs]-[A-Za-z0-9-]{20,}'
        'URL with credential' = 'https?://[^/\s:@]+:[^/\s@]{8,}@'
    }
    $paths = @(git -c core.quotepath=false ls-files --cached --others --exclude-standard)
    if ($LASTEXITCODE -ne 0) { throw 'Unable to list Git candidate files.' }
    $checked = 0
    foreach ($relative in ($paths | Sort-Object -Unique)) {
        $normalized = $relative.Replace('\','/')
        $denied = $normalized -match '(^|/)(instance|\.venv|node_modules|__pycache__)/' -or
            $normalized -match '(^|/)\.env($|\.)' -or
            $normalized -match '\.(db|sqlite3?|pem|key|pfx|p12)(-|$)' -or
            $normalized -match '^\.(claude/settings\.local\.json|codex/hooks\.json|agents/hooks\.json|codex/auth\.json)$'
        if ($denied -and $normalized -ne '.env.example') {
            $problems.Add("Sensitive path in Git candidates: $normalized")
        }
        $absolute = Join-Path $repoRoot $relative
        if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) { continue }
        $content = [System.IO.File]::ReadAllText($absolute)
        $checked++
        foreach ($rule in $patterns.Keys) {
            if ([regex]::IsMatch($content, $patterns[$rule])) {
                $problems.Add("Potential $rule in $normalized (value hidden)")
            }
        }
    }
    if (-not $SkipHistory) {
        # Capture history locally. Never print a matching line or a secret value.
        $historyLines = @(git log --all --format= -p --no-ext-diff)
        if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect Git history.' }
        $history = [string]::Join("`n", $historyLines)
        foreach ($rule in $patterns.Keys) {
            if ([regex]::IsMatch($history, $patterns[$rule])) {
                $problems.Add("Potential $rule in Git history (value hidden)")
            }
        }
    }
    if ($problems.Count -gt 0) {
        foreach ($problem in $problems) { Write-Output $problem }
        throw 'Repository safety check failed. Review findings before push.'
    }
    Write-Output "PASS: $checked candidate files checked; private files ignored; known secret patterns not detected."
    if (-not $SkipHistory) { Write-Output 'PASS: existing Git history checked.' }
} finally {
    if ($ignoreProbe -and (Test-Path -LiteralPath $ignoreProbe)) {
        $probeAbsolute = [System.IO.Path]::GetFullPath($ignoreProbe)
        $allowedProbeRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'instance')) + [System.IO.Path]::DirectorySeparatorChar
        if (-not $probeAbsolute.StartsWith($allowedProbeRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Refusing to remove an ignore probe outside the instance directory.'
        }
        Remove-Item -LiteralPath $probeAbsolute -Recurse -Force
    }
    Pop-Location
}
