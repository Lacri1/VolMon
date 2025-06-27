"""바이낸스 API를 통한 암호화폐 가격 조회 모듈"""
import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from volmon.config import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    REQUEST_TIMEOUT,
    get_full_url,
    get_headers,
    ENDPOINTS
)

class BinanceClient:
    """바이낸스 API 클라이언트"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or BINANCE_API_KEY
        self.api_secret = api_secret or BINANCE_API_SECRET
        self.session = self._init_session()
    
    def _init_session(self) -> requests.Session:
        """요청 세션 초기화"""
        session = requests.Session()
        session.headers.update(get_headers())
        return session
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """API 서명 생성 (비공개 엔드포인트용)"""
        if not self.api_secret:
            return ""
        query_string = urlencode(data)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, signed: bool = False, **kwargs) -> Dict:
        """API 요청 실행"""
        uri = get_full_url(endpoint)
        
        if signed:  # 비공개 API 호출 시 서명 추가
            kwargs['params'] = kwargs.get('params', {})
            kwargs['params']['timestamp'] = int(time.time() * 1000)
            kwargs['params']['signature'] = self._generate_signature(kwargs['params'])
        
        try:
            response = self.session.request(
                method=method,
                url=uri,
                timeout=REQUEST_TIMEOUT,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"API 요청 실패: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)
    
    def get_ticker_price(self, symbol: str) -> Dict[str, str]:
        """특정 코인의 현재 가격 조회"""
        params = {'symbol': symbol.upper()}
        return self._request('GET', ENDPOINTS['ticker_price'], params=params)
    
    def get_all_prices(self) -> List[Dict[str, str]]:
        """모든 코인의 현재 가격 조회"""
        return self._request('GET', ENDPOINTS['ticker_price'])
    
    def get_klines(
        self,
        symbol: str,
        interval: str = '1m',  # 1분봉
        limit: int = 100,      # 조회 건수
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[list]:
        """캔들스틱 데이터 조회"""
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000)  # 최대 1000건
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        return self._request('GET', ENDPOINTS['klines'], params=params)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """거래소 지원 코인 및 거래쌍 정보 조회"""
        return self._request('GET', ENDPOINTS['exchange_info'])


# 전역 인스턴스 생성
binance_client = BinanceClient()

def get_price(symbol: str) -> float:
    """코인 가격을 float 타입으로 반환"""
    result = binance_client.get_ticker_price(symbol)
    return float(result['price'])

def get_prices(symbols: List[str] = None) -> Dict[str, float]:
    """여러 코인의 현재가를 딕셔너리로 반환"""
    if symbols:
        return {symbol: get_price(symbol) for symbol in symbols}
    
    all_prices = binance_client.get_all_prices()
    return {item['symbol']: float(item['price']) for item in all_prices}
