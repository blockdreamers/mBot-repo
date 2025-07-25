#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys

def clear_webhook_manual():
    print("🤖 텔레그램 봇 Webhook 정리 도구")
    print("=" * 40)
    
    # Get BOT_TOKEN from user input
    print("📋 BOT_TOKEN을 입력하세요 (Render 환경변수에서 확인 가능):")
    BOT_TOKEN = input("BOT_TOKEN: ").strip()
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN이 입력되지 않았습니다!")
        return False
    
    # Get current webhook info
    print("\n🔍 현재 webhook 상태 확인 중...")
    webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_info_url)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                webhook_url = data['result'].get('url', '')
                if webhook_url:
                    print(f"📌 현재 webhook URL: {webhook_url}")
                    print(f"📊 Pending updates: {data['result'].get('pending_update_count', 0)}")
                    print(f"📅 Last error date: {data['result'].get('last_error_date', 'None')}")
                    print(f"🔧 Max connections: {data['result'].get('max_connections', 40)}")
                else:
                    print("✅ Webhook이 설정되지 않았습니다.")
                    print("🔍 하지만 다른 봇 인스턴스가 polling 모드로 실행 중일 수 있습니다.")
                    return True
            else:
                print(f"❌ Error: {data['description']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")
        return False
    
    # Delete webhook
    print("\n🗑️ Webhook 삭제 중...")
    delete_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    
    try:
        response = requests.post(delete_webhook_url)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ Webhook이 성공적으로 삭제되었습니다!")
                print("🔄 이제 Render에서 polling 모드로 봇을 실행할 수 있습니다.")
                return True
            else:
                print(f"❌ Error: {data['description']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")
        return False

def show_instructions():
    print("\n📝 추가 확인 사항:")
    print("=" * 40)
    print("1. 🖥️  로컬에서 실행 중인 봇 종료:")
    print("   - local-telegram.js 실행 중이면 Ctrl+C로 종료")
    print("   - VS Code 터미널에서 실행 중인 프로세스 확인")
    print("")
    print("2. 🌐 Netlify Functions 확인:")
    print("   - Netlify 대시보드에서 Functions 비활성화")
    print("   - 또는 webhook URL이 Netlify를 가리키고 있다면 삭제")
    print("")
    print("3. 🔄 Render 재배포:")
    print("   - Render 대시보드에서 Manual Deploy 클릭")
    print("   - 또는 GitHub에 새 커밋을 푸시")
    print("")
    print("4. 📱 봇 테스트:")
    print("   - 텔레그램에서 /start 명령어 전송")
    print("   - 응답이 오는지 확인")

if __name__ == "__main__":
    success = clear_webhook_manual()
    
    if success:
        print("\n✅ Webhook 정리 완료!")
        show_instructions()
    else:
        print("\n❌ 작업 실패!")
        print("📝 수동으로 해결하려면:")
        print("   1. 텔레그램 @BotFather에게 /mybots 명령어 전송")
        print("   2. 봇 선택 → Bot Settings → Delete webhook")
        show_instructions() 