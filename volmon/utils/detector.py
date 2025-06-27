# volmon/utils/detector.py

import time
from collections import deque
from volmon.config import TIME_WINDOW, ALERT_THRESHOLD

class VolatilityDetector:
    def __init__(self):
        self.price_history = deque()  # (timestamp, price) 튜플을 저장하는 데크
        self.time_window = TIME_WINDOW  # 초 단위 시간 창

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
                print(f"[Detector] 변동성 감지! {price_change:.2f}% (임계값: {ALERT_THRESHOLD}%)")
                return True, price_change

        return False, 0