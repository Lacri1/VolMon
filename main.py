# volmon/main.py

import sys
import os
import time
from pathlib import Path
import requests
import json
import threading
import websocket
from datetime import datetime
from typing import Dict

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from volmon.utils.detector import VolatilityDetector
from volmon.utils.notifier import send_alert
from volmon.config import SYMBOLS, BASE_WEBSOCKET_URL, ALERT_THRESHOLD, TIME_WINDOW

class PriceDisplay:
    def __init__(self):
        self.prices = {}  # 심볼별 가격 저장
        self.last_update = {}  # 마지막 업데이트 시간 저장
        self.update_interval = 5  # 화면 갱신 주기(초)
        self.lock = threading.Lock()  # 스레드 안전을 위한 락
        self.last_display_time = 0  # 마지막 화면 갱신 시간

    def update_price(self, symbol: str, price: float):
        """가격을 업데이트하고 필요시 화면 갱신"""
        now = time.time()
        with self.lock:
            self.prices[symbol] = price
            self.last_update[symbol] = now

            # 지정된 간격마다 화면 갱신
            if now - self.last_display_time >= self.update_interval:
                self._update_display()
                self.last_display_time = now



    def _update_display(self):
        print("\n" * 3)  # 이전 출력과 구분을 위해 빈 줄 3개 추가

        # 헤더 출력
        print("=== 암호화폐 가격 모니터 ===")
        print(f"{'심볼':<10} | {'가격 (USDT)':>15} | 마지막 업데이트")
        print("-" * 50)

        # 각 심볼별 가격 출력
        for symbol in sorted(self.prices.keys()):
            price = self.prices[symbol]
            last_update = datetime.fromtimestamp(self.last_update[symbol]).strftime('%H:%M:%S')
            price_str = f"{price:,.2f}"  # 천 단위 구분자 추가
            print(f"{symbol:<10} | {price_str:>15} | {last_update}")

        sys.stdout.flush()  # 출력 버퍼 비우기

class TickerMonitor:
    def __init__(self, symbol: str, display: PriceDisplay):
        self.symbol = symbol.upper()  # 거래소 심볼 (예: BTCUSDT)
        self.display = display  # 가격 표시기
        self.detector = VolatilityDetector()  # 변동성 감지기
        self.ws_url = f"{BASE_WEBSOCKET_URL}{symbol}@trade"  # 웹소켓 URL
        self.ws = None  # 웹소켓 연결 객체
        self.thread = None  # 웹소켓 스레드
        self.last_update_time = 0  # 마지막 업데이트 시간

    def get_current_price_rest(self) -> float:
        """REST API를 사용해 현재 가격 조회"""
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {"symbol": self.symbol}
        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()  # HTTP 에러 확인
            data = res.json()
            price = float(data["price"])
            self.display.update_price(self.symbol, price)
            return price
        except Exception as e:
            print(f"[{self.symbol}] REST API 오류: {str(e)[:100]}")
            return -1

    def on_message(self, ws, message):
        """웹소켓 메시지 처리"""
        try:
            data = json.loads(message)
            price = float(data['p'])  # 현재 가격
            current_time = time.time()

            # 1초에 한 번만 가격 업데이트
            if current_time - self.last_update_time >= 1.0:
                self.display.update_price(self.symbol, price)
                self.last_update_time = current_time

            # 변동성 감지
            detected, change = self.detector.detect(price)
            
            # 변동성이 감지된 경우에만 알림 전송 및 로깅
            if detected:
                print(f"[{self.symbol}] 변동성 감지! 변동폭: {change:+.2f}% (임계값: {ALERT_THRESHOLD}%)")
                send_alert(
                    symbol=self.symbol,
                    price=price,
                    change=change
                )

        except Exception as e:
            print(f"[{self.symbol}] 메시지 처리 오류: {str(e)[:100]}")

    def on_error(self, ws, error):
        """웹소켓 에러 처리"""
        if hasattr(error, 'status_code') and error.status_code == 429:
            print(f"[{self.symbol}] 요청 제한 초과. 재연결 대기 중...")
            time.sleep(60)  # 1분 대기
        else:
            print(f"[{self.symbol}] 오류: {str(error)[:100]}")

    def on_close(self, ws, close_status_code, close_msg):
        """웹소켓 연결 종료 처리"""
        print(f"[{self.symbol}] 웹소켓 연결 종료. 재연결 시도 중...")
        time.sleep(5)
        self.start()  # 재연결 시도

    def on_open(self, ws):
        """웹소켓 연결 성공 시 호출"""
        print(f"[{self.symbol}] 웹소켓 연결 성공")

    def start(self):
        """모니터링 시작"""
        print(f"[VolMon] 모니터링 시작: {self.symbol}")

        # 초기 가격 조회
        rest_price = self.get_current_price_rest()
        if rest_price > 0:
            print(f"[{self.symbol}] 초기 가격: {rest_price:,.2f}")

        # 웹소켓 연결 시작
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

        # 웹소켓을 별도 스레드에서 실행
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True  # 메인 스레드 종료 시 함께 종료
        self.thread.start()

def main():
    # 초기 메시지 출력
    print("=== VolMon - 암호화폐 변동성 모니터 ===")
    print(f"모니터링 중인 코인: {len(SYMBOLS)}개 - {', '.join(s.upper() for s in SYMBOLS)}")
    print(f"알림 기준: {TIME_WINDOW}초 내 {ALERT_THRESHOLD}% 이상 변동 시")
    print("=" * 50 + "\n")

    # 가격 표시기 생성
    display = PriceDisplay()

    # 각 심볼별 모니터 생성 및 시작
    monitors = [TickerMonitor(symbol, display) for symbol in SYMBOLS]
    for monitor in monitors:
        monitor.start()

    # 메인 스레드 유지
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n모니터링을 종료합니다...")
    except Exception as e:
        print(f"\n예상치 못한 오류 발생: {str(e)}")
    finally:
        print("모니터링이 중지되었습니다.")

if __name__ == "__main__":
    main()