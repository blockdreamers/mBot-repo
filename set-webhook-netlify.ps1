# set-webhook.ps1
Clear-Host

Write-Host "📦 Telegram Webhook 설정 도구" -ForegroundColor Cyan

# ✅ .env에서 변수 읽기
$envPath = ".\.env"
$dotenv = Get-Content $envPath | Where-Object { $_ -match '=' } | ForEach-Object {
    $parts = $_ -split '=', 2
    @{ Key = $parts[0].Trim(); Value = $parts[1].Trim() }
}

function Get-EnvVar($key) {
    return ($dotenv | Where-Object { $_.Key -eq $key }).Value
}

$BOT_TOKEN = Get-EnvVar "TELEGRAM_TOKEN"
$NGROK_URL = Get-EnvVar "NGROK_KEY"
$NETLIFY_URL = Get-EnvVar "NETLIFY_URL"

# 🔘 옵션 선택
Write-Host "`n🌐 어떤 환경으로 Webhook을 설정할까요?"
Write-Host "[1] 로컬 개발용 (ngrok)"
Write-Host "[2] Netlify 배포용"
$choice = Read-Host "선택 (1 또는 2 입력)"

switch ($choice) {
    '1' {
        $WEBHOOK_URL = "$NGROK_URL/.netlify/functions/telegram"
        $mode = "로컬"
    }
    '2' {
        $WEBHOOK_URL = "https://$NETLIFY_URL/.netlify/functions/telegram"
        $mode = "Netlify"
    }
    default {
        Write-Host "❌ 잘못된 선택입니다. 스크립트를 다시 실행해주세요." -ForegroundColor Red
        exit 1
    }
}

# 🚀 Webhook 설정 요청
Write-Host "`n🚀 설정 중... [$mode]"
Write-Host "📡 Webhook URL → $WEBHOOK_URL"

$response = curl -Method POST `
  -Uri "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" `
  -Body @{ url = $WEBHOOK_URL }

Write-Host "`n🎉 완료! 응답:"
$response
