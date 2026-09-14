<#
.SYNOPSIS
    Quartz 5 기반 지식베이스 블로그를 이 폴더에 셋업합니다.

.DESCRIPTION
    1) Quartz 저장소를 이 폴더로 가져오고
    2) 의존성 설치 + Obsidian 템플릿으로 초기화
    3) quartz.config.yaml 을 개인화 (제목/locale/푸터/플러그인)
    4) GitHub Pages 배포 워크플로 생성
    5) 시작 노트 배치 + origin 리모트 연결

.EXAMPLE
    .\setup.ps1
    .\setup.ps1 -GitHubUser bjchoi -RepoName quartz_base -SiteTitle "범진의 지식베이스"
    .\setup.ps1 -GitHubUser bjchoi -RepoName notes -VaultPath "D:\workspace\TIL"
#>
[CmdletBinding()]
param(
    [string]$GitHubUser = "",
    [string]$RepoName = "",
    [string]$SiteTitle = "",
    [string]$VaultPath = "",
    [switch]$UserSite   # user.github.io 저장소인 경우 (baseUrl 에 /repo 를 붙이지 않음)
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Say($msg)  { Write-Host "  $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  !   $msg" -ForegroundColor Yellow }
function Die($msg)  { Write-Host "  X   $msg" -ForegroundColor Red; exit 1 }

function Invoke-Step($label, [scriptblock]$block) {
    Say $label
    # 외부 명령(npm 등)이 stderr 로 진행상황을 찍어도 중단되지 않도록
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $global:LASTEXITCODE = 0
    & $block
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { Die "$label 실패 (exit $code)" }
}

Write-Host ""
Write-Host "  Quartz 5 지식베이스 셋업" -ForegroundColor White
Write-Host "  대상 폴더: $Root" -ForegroundColor DarkGray
Write-Host ""

# ---------------------------------------------------------------- 0. 사전 점검
foreach ($cmd in @("git", "node", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Die "$cmd 가 설치되어 있지 않습니다. (node 는 22 이상 필요: https://nodejs.org)"
    }
}

$nodeMajor = [int](((node -v) -replace '^v', '') -split '\.')[0]
if ($nodeMajor -lt 22) { Die "Node 22 이상이 필요합니다. 현재: $(node -v)" }
Ok "git $(git --version | ForEach-Object { $_ -replace 'git version ','' }) / node $(node -v) / npm $(npm -v)"

if (Test-Path (Join-Path $Root "package.json")) {
    Die "이미 셋업된 폴더로 보입니다 (package.json 존재). 처음부터 다시 하려면 폴더를 비우고 실행하세요."
}

# ---------------------------------------------------------------- 1. 입력 받기
if (-not $GitHubUser) { $GitHubUser = "$(Read-Host '  GitHub 사용자명')".Trim() }
if (-not $GitHubUser) { Die "GitHub 사용자명은 필수입니다." }

if (-not $RepoName) {
    $default = Split-Path $Root -Leaf
    $answer = "$(Read-Host "  저장소 이름 [$default]")".Trim()
    $RepoName = if ($answer) { $answer } else { $default }
}

if (-not $SiteTitle) {
    $answer = "$(Read-Host "  사이트 제목 [$GitHubUser knowledge base]")".Trim()
    $SiteTitle = if ($answer) { $answer } else { "$GitHubUser knowledge base" }
}

$isUserSite = $UserSite -or ($RepoName -ieq "$GitHubUser.github.io")
$BaseUrl = if ($isUserSite) { "$GitHubUser.github.io" } else { "$GitHubUser.github.io/$RepoName" }

$strategy = "new"
if ($VaultPath) {
    if (-not (Test-Path $VaultPath -PathType Container)) { Die "vault 경로를 찾을 수 없습니다: $VaultPath" }
    $strategy = "copy"
}

Write-Host ""
Write-Host "  저장소   : https://github.com/$GitHubUser/$RepoName" -ForegroundColor DarkGray
Write-Host "  사이트   : https://$BaseUrl" -ForegroundColor DarkGray
Write-Host "  제목     : $SiteTitle" -ForegroundColor DarkGray
Write-Host "  콘텐츠   : $(if ($strategy -eq 'copy') { "$VaultPath 복사" } else { '새로 시작' })" -ForegroundColor DarkGray
Write-Host ""
if ("$(Read-Host '  진행할까요? [Y/n]')".Trim() -imatch '^n') { exit 0 }
Write-Host ""

# ------------------------------------------------------- 2. Quartz 소스 가져오기
$tmp = Join-Path $env:TEMP ("quartz-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
Invoke-Step "Quartz 5 소스 clone 중..." { git clone --branch v5 https://github.com/jackyzha0/quartz.git $tmp }

Get-ChildItem -LiteralPath $tmp -Force | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $Root -Force
}
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
Ok "소스 배치 완료"

Set-Location $Root

# ------------------------------------------------------------- 3. 의존성 설치
Invoke-Step "npm 의존성 설치 중... (몇 분 걸립니다)" { npm install --no-audit --no-fund }
Ok "의존성 설치 완료"

# ----------------------------------------------------------------- 4. 초기화
if ($strategy -eq "copy") {
    Invoke-Step "Quartz 초기화 중 (Obsidian 템플릿, vault 복사)..." {
        npx quartz create -t obsidian -X copy -s "$VaultPath" -b "$BaseUrl"
    }
} else {
    Invoke-Step "Quartz 초기화 중 (Obsidian 템플릿)..." {
        npx quartz create -t obsidian -X new -b "$BaseUrl"
    }
}
Ok "초기화 완료"

# ------------------------------------------------------------- 5. 설정 개인화
Invoke-Step "quartz.config.yaml 개인화 중..." {
    node "_setup/patch-config.mjs" --title "$SiteTitle" --github "$GitHubUser/$RepoName" --locale "ko-KR"
}

Invoke-Step "플러그인 설치 중..." { npx quartz plugin install --from-config }
Ok "설정 완료"

# --------------------------------------------------- 6. GitHub Actions 워크플로
# Quartz 저장소 자체의 CI 워크플로는 개인 저장소에서 불필요하므로 정리
Remove-Item -LiteralPath (Join-Path $Root ".github") -Recurse -Force -ErrorAction SilentlyContinue
$wf = Join-Path $Root ".github\workflows"
New-Item -ItemType Directory -Path $wf -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $Root "_setup\deploy.yml") -Destination (Join-Path $wf "deploy.yml") -Force
Ok "GitHub Pages 워크플로 생성 (.github/workflows/deploy.yml)"

# ------------------------------------------------------------- 7. 시작 노트
$content = Join-Path $Root "content"
$seed = Join-Path $Root "_setup\content"
if ($strategy -eq "new") {
    Copy-Item -Path (Join-Path $seed "*") -Destination $content -Recurse -Force
    Ok "시작 노트 배치 (index / MOC / 작성 규칙 / 사용법 / 템플릿)"
} else {
    # 기존 vault 를 덮어쓰지 않도록 없는 것만 채움
    foreach ($rel in @("MOC", "templates")) {
        $dst = Join-Path $content $rel
        if (-not (Test-Path $dst)) { Copy-Item -LiteralPath (Join-Path $seed $rel) -Destination $dst -Recurse -Force }
    }
    $howto = Join-Path $content "notes"
    New-Item -ItemType Directory -Path $howto -Force | Out-Null
    Copy-Item -Path (Join-Path $seed "notes\*") -Destination $howto -Force
    if (-not (Test-Path (Join-Path $content "index.md"))) {
        Copy-Item -LiteralPath (Join-Path $seed "index.md") -Destination $content -Force
    }
    Ok "안내 노트 추가 (기존 vault 파일은 건드리지 않음)"
}
New-Item -ItemType Directory -Path (Join-Path $content "private") -Force | Out-Null
Set-Content -LiteralPath (Join-Path $content "private\.gitkeep") -Value "" -NoNewline

# ------------------------------------------------------------- 8. git 리모트
$originUrl = "https://github.com/$GitHubUser/$RepoName.git"
git remote get-url origin *>$null
if ($LASTEXITCODE -eq 0) { git remote set-url origin $originUrl *>$null }
else { git remote add origin $originUrl *>$null }
git remote get-url upstream *>$null
if ($LASTEXITCODE -ne 0) { git remote add upstream https://github.com/jackyzha0/quartz.git *>$null }
Ok "origin -> https://github.com/$GitHubUser/$RepoName.git"

git add -A *>$null
git commit -m "chore: initialize quartz knowledge base" *>$null
Ok "초기 커밋 생성"

# ------------------------------------------------------------------ 완료
Write-Host ""
Write-Host "  셋업 완료" -ForegroundColor Green
Write-Host ""
Write-Host "  다음 순서로 진행하세요:" -ForegroundColor White
Write-Host ""
Write-Host "  1) 로컬 확인" -ForegroundColor White
Write-Host "       npx quartz build --serve      -> http://localhost:8080" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2) GitHub 에 빈 저장소 생성 (README/gitignore 체크 해제)" -ForegroundColor White
Write-Host "       https://github.com/new  이름: $RepoName" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3) push" -ForegroundColor White
Write-Host "       git push -u origin v5" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  4) 저장소 Settings > Pages > Source 를 'GitHub Actions' 로 변경" -ForegroundColor White
Write-Host "       1~2분 뒤 https://$BaseUrl 에서 확인" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  5) Obsidian 에서 content 폴더를 vault 로 열기" -ForegroundColor White
Write-Host "       $content" -ForegroundColor DarkGray
Write-Host ""
