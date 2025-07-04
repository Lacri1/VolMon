# volmon/utils/notifier.py

import requests
import json
import re
import time
from typing import Optional, Dict, Any, Tuple
from volmon.config import DISCORD_WEBHOOK_URL, TIME_WINDOW

# 보안 설정 가져오기
from volmon.config import SECURITY_TOKEN, ALLOWED_WEBHOOK_IDS

# 알림 상태 추적을 위한 전역 변수
class NotificationState:
    _instance = None
    
    # 알림을 보낼 변동률 임계값 목록 (단위: %)
    THRESHOLDS = [0.3, 0.5, 1.0, 2.0, 3.0, 5.0]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationState, cls).__new__(cls)
            cls._instance._state = {}
        return cls._instance
    
    def _get_threshold_index(self, change: float) -> int:
        """변화율에 해당하는 임계값 인덱스를 반환합니다."""
        abs_change = abs(change)
        for i, threshold in enumerate(self.THRESHOLDS):
            if abs_change < threshold:
                return i - 1
        return len(self.THRESHOLDS) - 1
    
    def should_notify(self, symbol: str, change: float) -> Tuple[bool, float]:
        """
        알림을 보내야 하는지 확인합니다.
        
        Args:
            symbol: 코인 심볼
            change: 현재 변동률
            
        Returns:
            tuple: (알림_전송_여부, 마지막_알림_이후_경과_시간(초))
        """
        current_time = time.time()
        state = self._state.get(symbol, {
            "last_notified": 0, 
            "last_change": 0,
            "last_threshold_index": -1,
            "last_direction": 0
        })
        
        # 현재 방향 (1: 상승, -1: 하락, 0: 변화 없음)
        current_direction = 1 if change > 0 else (-1 if change < 0 else 0)
        
        # 방향이 바뀌었는지 확인
        direction_changed = (state["last_direction"] * current_direction) < 0
        
        # 현재 변동률의 임계값 인덱스
        current_threshold_index = self._get_threshold_index(change)
        
        # 알림 조건:
        # 1. 방향이 바뀌었거나
        # 2. 현재 변동률이 새로운 임계값에 도달했거나
        # 3. 변동률이 0.3% 이상이고, 마지막 알림으로부터 1분(60초)이 지났을 때
        should_notify = (
            direction_changed or
            current_threshold_index > state["last_threshold_index"] or
            (abs(change) >= 0.3 and current_time - state["last_notified"] >= 60)
        )
        
        # 변동률이 0.3% 미만이면 임계값 인덱스 초기화
        if abs(change) < 0.3:
            state["last_threshold_index"] = -1
        
        if should_notify:
            state.update({
                "last_notified": current_time,
                "last_change": change,
                "last_threshold_index": current_threshold_index,
                "last_direction": current_direction
            })
            self._state[symbol] = state
            
        return should_notify, current_time - state["last_notified"]

# 전역 상태 관리자
notification_state = NotificationState()

class WebhookSecurityError(Exception):
    """웹훅 보안 관련 예외"""
    pass

def validate_webhook_url(url: str) -> bool:
    """웹훅 URL이 허용된 형식인지 검증"""
    # 웹훅 URL 패턴: https://discord.com/api/webhooks/{webhook_id}/{webhook_token}
    pattern = r'https://(?:ptb\.|canary\.)?discord\.com/api/webhooks/\d+/[\w-]+'
    if not re.fullmatch(pattern, url):
        return False
    
    # 허용된 웹훅 ID인지 확인
    webhook_id = url.split('/')[-2]
    return webhook_id in ALLOWED_WEBHOOK_IDS

def sanitize_mentions(text: str) -> str:
    """@everyone, @here 등의 멘션을 방지하기 위한 문자열 처리"""
    return text.replace("@everyone", "@​everyone").replace("@here", "@​here")

def create_alert_message(symbol: str, price: float, change: float, **kwargs) -> Dict[str, Any]:
    """알림 메시지 생성"""
    # 기본 메시지 생성
    message = sanitize_mentions(
        f"변동성 알림!\n"
        f"티커: {symbol.upper()}\n"
        f"가격: ${price:,.2f}\n"
        f"변동률: {change:+.2f}% ({TIME_WINDOW}초 기준)\n"
        f"시간: {kwargs.get('timestamp', '')}"
    )
    
    return {
        "content": message,
        # 모든 멘션 비활성화
        "allowed_mentions": {
            "parse": [],  # 모든 자동 멘션 비활성화
            "users": [],  # 유저 멘션 비활성화
            "roles": [],  # 역할 멘션 비활성화
            "replied_user": False  # 답장 시 유저 멘션 비활성화
        }
    }

def send_alert(
    symbol: str, 
    price: float, 
    change: float, 
    security_token: Optional[str] = None,
    **kwargs
) -> bool:
    """
    디스코드로 알림을 전송합니다.
    
    Args:
        symbol: 코인 심볼 (예: 'BTCUSDT')
        price: 현재 가격
        change: 가격 변동률 (%)
        security_token: 외부 요청 검증용 토큰
        **kwargs: 추가 파라미터 (timestamp 등)
        
    Returns:
        bool: 알림 전송 성공 여부
    """
    # 알림을 보내야 하는지 확인
    should_notify, time_since_last = notification_state.should_notify(symbol, change)
    
    # 알림 조건을 충족하지 않으면 전송하지 않음
    if not should_notify:
        print(f"[Notifier] 알림 건너뜀: {symbol} (마지막 알림 후 {int(time_since_last)}초 경과, 현재 변동: {change:.2f}%)")
        return False
    # 웹훅 URL 검증
    if not DISCORD_WEBHOOK_URL:
        print("[Notifier Error] Discord webhook URL is not configured")
        return False
        
    if not validate_webhook_url(DISCORD_WEBHOOK_URL):
        print("[Notifier Error] Invalid webhook URL")
        return False
    
    # 외부 요청인 경우 토큰 검증
    if security_token and security_token != SECURITY_TOKEN:
        print("[Notifier Error] Invalid security token")
        return False
    
    try:
        # 메시지 생성
        message = create_alert_message(symbol, price, change, **kwargs)
        
        print(f"[Notifier] Sending alert to Discord: {message['content']}")
        
        # 요청 헤더 설정
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'VolMon/1.0',
            'X-Security-Token': SECURITY_TOKEN
        }
        
        # 요청 전송
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(message),
            headers=headers,
            timeout=10  # 10초 타임아웃
        )
        
        # 응답 상태 코드 확인
        response.raise_for_status()
        print("[Notifier] Successfully sent alert to Discord")
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
    except Exception as e:
        print(f"[Notifier Error] Unexpected error: {str(e)}")
        return False
