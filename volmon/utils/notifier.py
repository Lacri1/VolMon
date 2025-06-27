# volmon/utils/notifier.py

import requests
import json
from volmon.config import DISCORD_WEBHOOK_URL, TIME_WINDOW

def send_alert(symbol: str, price: float, change: float):
    if not DISCORD_WEBHOOK_URL:
        print("[Notifier Error] Discord webhook URL is not configured")
        return False

    message = {
        "content": (
            f"변동성 알림!\n"
            f"티커: {symbol.upper()}\n"
            f"가격: ${price:,.2f}\n"
            f"변동률: {change:+.2f}% ({TIME_WINDOW}초 기준)"
        )
    }
    
    try:
        print(f"[Notifier] Sending alert to Discord: {message['content']}")
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(message),
            headers=headers,
            timeout=10  # 10초 타임아웃
        )
        
        # 응답 상태 코드 확인
        response.raise_for_status()
        print(f"[Notifier] Successfully sent alert to Discord")
        return True
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            try:
                error_msg = e.response.json()
                print(f"[Notifier Error] Discord API Error ({status_code}): {error_msg}")
            except:
                print(f"[Notifier Error] Failed to send alert: HTTP {status_code} - {str(e)}")
        else:
            print(f"[Notifier Error] Failed to send alert: {str(e)}")
        return False
