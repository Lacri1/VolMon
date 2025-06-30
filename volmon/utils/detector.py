# volmon/utils/detector.py

import time
from collections import deque
from volmon.config import TIME_WINDOW, ALERT_THRESHOLD

class VolatilityDetector:
    def __init__(self):
        self.price_history = deque()  # (timestamp, price) 튜플을 저장하는 데크
        self.time_window = TIME_WINDOW  # 초 단위 시간 창
        self.last_log_time = 0  # 마지막 로그 출력 시간
        self.log_interval = 300  # 로그 출력 최소 간격 (초)
        self.last_detected_change = 0  # 마지막 감지된 변동률
        self.last_direction = 0  # 마지막 변동 방향 (1: 상승, -1: 하락, 0: 초기값)

    def detect(self, current_price: float):
        now = time.time()
        
        # 현재 시간 기준으로 time_window(초) 이전의 타임스탬프 계산
        time_threshold = now - self.time_window

        # 오래된 데이터 제거 (time_window 이전의 데이터)
        while self.price_history and self.price_history[0][0] < time_threshold:
            self.price_history.popleft()

        # 현재 가격과 시간 추가
        self.price_history.append((now, current_price))
        
        # 최소 2개 이상의 데이터가 있어야 변동성 계산 가능
        if len(self.price_history) >= 2:
            # time_window 내의 첫 번째 가격과 현재 가격 비교
            _, oldest_price = self.price_history[0]
            price_change = ((current_price - oldest_price) / oldest_price) * 100
            
            if abs(price_change) >= ALERT_THRESHOLD:
                current_time = time.time()
                current_direction = 1 if price_change >= 0 else -1
                
                # 방향이 바뀌었거나, 로그 출력 간격이 지났거나, 변동률이 크게 증가한 경우에만 로그 출력
                should_log = (
                    current_time - self.last_log_time >= self.log_interval or
                    current_direction != self.last_direction or
                    abs(price_change) >= abs(self.last_detected_change) * 1.3
                )
                
                if should_log:
                    print(
                        f"[Detector] 변동성 감지! {price_change:+.2f}% "
                        f"(임계값: {ALERT_THRESHOLD}%, 이전: {self.last_detected_change:+.2f}%)"
                    )
                    self.last_log_time = current_time
                
                # 상태 업데이트
                self.last_detected_change = price_change
                self.last_direction = current_direction
                
                return True, price_change

        return False, 0