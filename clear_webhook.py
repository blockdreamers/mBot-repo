#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from dotenv import load_dotenv

def clear_webhook():
    # Load environment variables
    load_dotenv()
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN이 .env 파일에 설정되지 않았습니다!")
        return False
    
    # Get current webhook info
    print("🔍 현재 webhook 상태 확인 중...")
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
                else:
                    print("✅ Webhook이 설정되지 않았습니다.")
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

if __name__ == "__main__":
    print("🤖 텔레그램 봇 Webhook 정리 도구")
    print("=" * 40)
    
    success = clear_webhook()
    
    if success:
        print("\n✅ 작업 완료!")
        print("📝 다음 단계:")
        print("   1. 로컬에서 실행 중인 봇이 있다면 종료하세요")
        print("   2. Render에서 봇을 다시 배포하세요")
        print("   3. 로그에서 '🤖 Telegraf 봇 로컬 실행 중 (Polling 모드)' 메시지를 확인하세요")
    else:
        print("\n❌ 작업 실패!")
        print("📝 수동으로 해결하려면:")
        print("   1. 텔레그램 @BotFather에게 /mybots 명령어 전송")
        print("   2. 봇 선택 → Bot Settings → Webhook 해제") 