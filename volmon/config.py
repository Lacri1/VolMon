# volmon/config.py

import os
from dotenv import load_dotenv
from typing import Dict, List

# 환경 변수 로드
load_dotenv()

# 바이낸스 API 설정
BASE_API_URL = 'https://api.binance.com'  # REST API 기본 주소
BASE_WEBSOCKET_URL = 'wss://stream.binance.com:9443/ws/'  # 웹소켓 주소

# API 키 (필수)
BINANCE_API_KEY = os.environ["BINANCE_API_KEY"]
BINANCE_API_SECRET = os.environ["BINANCE_API_SECRET"]

# 모니터링 설정
SYMBOLS = ['btcusdt', 'ethusdt']  # 모니터링할 코인 심볼
ALERT_THRESHOLD = 0.3  # 변동성 알림 임계값 (%)
TIME_WINDOW = 60  # 변동성 계산 기간 (초)
REQUEST_TIMEOUT = 10  # API 요청 제한 시간 (초)
UPDATE_INTERVAL = 5 # 화면 갱신 주기 (초)

# 보안 설정
SECURITY_TOKEN = os.environ["SECURITY_TOKEN"]
ALLOWED_WEBHOOK_IDS = [id_.strip() for id_ in os.environ["ALLOWED_WEBHOOK_IDS"].split(",") if id_.strip()]

# 디스코드 웹훅 URL (필수)
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# 바이낸스 API 엔드포인트
ENDPOINTS = {
    'ticker_price': '/api/v3/ticker/price',  # 현재가 조회
    'exchange_info': '/api/v3/exchangeInfo',  # 거래소 정보
    'klines': '/api/v3/klines'  # 캔들스틱 데이터
}

def get_full_url(endpoint: str) -> str:
    """API 엔드포인트에 베이스 URL을 결합"""
    return f"{BASE_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"

def get_headers() -> Dict[str, str]:
    """API 요청 헤더 생성"""
    return {
        'X-MBX-APIKEY': BINANCE_API_KEY,
        'Content-Type': 'application/json'
    }
