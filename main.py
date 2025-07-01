# volmon/main.py

import sys
import os
import time
import logging
from pathlib import Path
import requests
import json
import threading
import websocket
from datetime import datetime
from typing import Dict

# 로깅 설정
def setup_logging():
    # 로거 생성
    logger = logging.getLogger('volmon')
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러 (로깅용)
    file_handler = logging.FileHandler('volmon.log', encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                     datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    
    # 콘솔 핸들러 (에러만 표시)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from volmon.utils.detector import VolatilityDetector
from volmon.utils.notifier import send_alert
from volmon.config import SYMBOLS, BASE_WEBSOCKET_URL, ALERT_THRESHOLD, TIME_WINDOW

class PriceDisplay:
    def __init__(self, symbols):
        self.prices = {}  # 가격 저장 딕셔너리
        self.last_update = {}  # 마지막 업데이트 시간 저장
        self.update_interval = 5  # 화면 갱신 주기(초)
        self.lock = threading.Lock()  # 스레드 안전을 위한 락
        self.last_display_time = 0  # 마지막 화면 갱신 시간
        self.initial_prices_received = False  # 초기 가격 수신 여부
        self.expected_symbols = set(symbol.upper() for symbol in symbols)  # 대소문자 구분 없이 처리

    def update_price(self, symbol: str, price: float):
        """가격을 업데이트하고 필요시 화면 갱신"""
        now = time.time()
        symbol = symbol.upper()  # 대문자로 통일
        
        with self.lock:
            # 가격 업데이트 (변경 여부와 관계없이)
            price_changed = symbol not in self.prices or self.prices[symbol] != price
            if price_changed:
                self.prices[symbol] = price
            self.last_update[symbol] = now  # 항상 타임스탬프 업데이트
            
            # 가격이 변경되지 않았고 초기 가격도 수신된 상태면 화면 갱신만 수행
            if not price_changed and self.initial_prices_received:
                if now - self.last_display_time >= self.update_interval:
                    self.last_display_time = now
                    self._update_display()
                return

            # 초기 가격이 아직 수신되지 않았을 때
            if not self.initial_prices_received:
                # 모든 심볼의 가격을 수신했는지 확인
                if all(sym in self.prices for sym in self.expected_symbols):
                    self.initial_prices_received = True
                    self.last_display_time = now
                    self._update_display()
                return
                
            # 초기 가격 이후에는 주기적으로만 업데이트
            if now - self.last_display_time >= self.update_interval:
                self.last_display_time = now
                self._update_display()



    def _update_display(self):
        # 헤더 출력
        print("=== VolMon - Cryptocurrency Volatility Monitor ===")
        print(f"Monitoring {len(self.expected_symbols)} coins - {', '.join(sorted(self.expected_symbols))}")
        print(f"Alert threshold: {ALERT_THRESHOLD}% change within {TIME_WINDOW} seconds")
        print("=" * 50 + "\n")
        
        # 가격 테이블 헤더
        print("=== Cryptocurrency Price Monitor ===")
        print(f"{'Symbol':<10} | {'Price (USDT)':>15} | Last Updated")
        print("-" * 50)
        
        # 각 심볼별 가격 출력 (알파벳 순 정렬)
        for symbol in sorted(self.expected_symbols):
            price = self.prices.get(symbol, 0)
            last_update_ts = self.last_update.get(symbol, 0)
            last_update = datetime.fromtimestamp(last_update_ts).strftime('%H:%M:%S') if last_update_ts > 0 else '--:--:--'
            price_str = f"{price:,.2f}" if price > 0 else 'Loading...'
            print(f"{symbol:<10} | {price_str:>15} | {last_update}")
        
        sys.stdout.flush()  # 출력 버퍼 비우기

class TickerMonitor:
    def __init__(self, symbol: str, display: PriceDisplay):
        self.symbol = symbol.upper()  # 거래소 심볼 (예: BTCUSDT)
        self.display = display  # 가격 표시기
        self.detector = VolatilityDetector()  # 변동성 감지기
        self.ws_url = f"{BASE_WEBSOCKET_URL}{symbol.lower()}@trade"  # 웹소켓 URL (소문자로 통일)
        self.ws = None  # 웹소켓 연결 객체
        self.thread = None  # 웹소켓 스레드
        self.last_update_time = 0  # 마지막 업데이트 시간
        self.last_price = 0  # 마지막 가격
        self.last_processed_time = 0  # 마지막 처리 시간
        self.message_queue = []  # 메시지 큐
        self.processing = False  # 메시지 처리 중 플래그

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
            logger.error(f"[{self.symbol}] REST API 오류: {str(e)[:100]}")
            return -1

    def on_message(self, ws, message):
        """웹소켓 메시지 처리"""
        try:
            current_time = time.time()
            
            # 0.1초 이내에 도착한 메시지는 무시
            if current_time - self.last_processed_time < 0.1:
                return
                
            data = json.loads(message)
            price = float(data['p'])  # 현재 가격
            
            # 가격이 변경되었는지 확인
            price_changed = abs(price - self.last_price) >= 0.01  # 부동소수점 비교를 위한 작은 값 사용
        
            # 가격이 변경되었거나, 1초 이상 지났으면 업데이트
            if price_changed or (current_time - self.last_processed_time >= 1.0):
                if price_changed:
                    self.last_price = price
                self.last_processed_time = current_time
                
                # 디스플레이 업데이트 (타임스탬프 갱신을 위해 항상 호출)
                self.display.update_price(self.symbol, self.last_price)
                
                # 1초에 한 번만 변동성 감지
                if current_time - self.last_update_time >= 1.0:
                    detected, change = self.detector.detect(price)
                    self.last_update_time = current_time
                    
                    # 변동성이 감지된 경우에만 알림 전송 및 로깅
                    if detected:
                        print(f"\n[{self.symbol}] Volatility detected! Change: {change:+.2f}% (Threshold: {ALERT_THRESHOLD}%)")
                        send_alert(
                            symbol=self.symbol,
                            price=price,
                            change=change
                        )
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)[:100]}")

    def on_error(self, ws, error):
        """웹소켓 에러 처리"""
        if hasattr(error, 'status_code') and error.status_code == 429:
            logger.warning(f"[{self.symbol}] 요청 제한 초과. 재연결 대기 중...")
            time.sleep(60)  # 1분 대기
        else:
            print(f"[{self.symbol}] 오류: {str(error)[:100]}")

    def on_close(self, ws, close_status_code, close_msg):
        """웹소켓 연결 종료 처리"""
        logger.warning(f"[{self.symbol}] 웹소켓 연결 종료. 재연결 시도 중...")
        time.sleep(5)
        self.start()  # 재연결 시도

    def on_open(self, ws):
        """웹소켓 연결 성공 시 호출"""
        # 로그 파일에만 기록 (화면에는 표시 안 함)
        logger.debug(f"[{self.symbol}] Websocket connected")

    def start(self):
        """모니터링 시작"""
        # 로그 파일에만 기록
        logger.info(f"[VolMon] Starting monitoring: {self.symbol}")

        # 초기 가격 조회
        rest_price = self.get_current_price_rest()
        if rest_price > 0:
            logger.info(f"[{self.symbol}] Initial price: {rest_price:,.2f}")
            # 화면에 즉시 반영
            self.last_price = rest_price
            self.last_processed_time = time.time()
            self.display.update_price(self.symbol, rest_price)

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
    display = PriceDisplay(SYMBOLS)  # 모든 심볼로 디스플레이 초기화
    monitors = []
    
    # 모든 모니터 초기화
    for symbol in SYMBOLS:
        monitor = TickerMonitor(symbol, display)
        monitors.append(monitor)
    
    # 모든 모니터 시작
    for monitor in monitors:
        monitor.start()
        time.sleep(0.5)  # API 요청 간 간격 유지
    
    # 초기 화면 표시
    display._update_display()

    try:
        # 메인 스레드 유지
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n예상치 못한 오류 발생: {str(e)}")
    finally:
        print("모니터링이 중지되었습니다.")

if __name__ == "__main__":
    main()