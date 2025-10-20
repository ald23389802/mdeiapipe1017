import json
import httpx
import time
import random
from datetime import datetime

# 使用 Yahoo Finance API
URL = "https://query1.finance.yahoo.com/v8/finance/chart/1101.TW"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
}

def get_taini_close(url: str = URL) -> float:
    """從 Yahoo Finance API 抓取台泥收盤價。
    
    Args:
        url: Yahoo Finance API 網址
        
    Returns:
        float: 台泥收盤價
        
    Raises:
        RuntimeError: 當找不到收盤價或 API 回應異常時
    """
    # 加入時間參數以避免快取
    params = {
        "interval": "1d",  # 日資料
        "range": "1d",     # 取得今天的資料
        "timestamp": int(time.time())  # 避免快取
    }
    
    with httpx.Client(headers=HEADERS, timeout=20, verify=False) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        try:
            # 從 API 回應中取得最新收盤價
            result = data['chart']['result'][0]
            latest_price = result['meta']['regularMarketPrice']
            return float(latest_price)
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"無法從 API 回應中取得收盤價: {str(e)}")

if __name__ == "__main__":
    try:
        price = get_taini_close()
        print(f"台泥收盤價: {price}")
        
        # 加入更多資訊
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"查詢時間: {current_time}")
    except Exception as e:
        print(f"錯誤: {e}")
        
        # 如果想看完整的 API 回應，取消註解以下程式碼
        # with httpx.Client(headers=HEADERS, timeout=20, verify=False) as client:
        #     response = client.get(URL, params={"interval": "1d", "range": "1d"})
        #     print("\nAPI 回應:", json.dumps(response.json(), indent=2, ensure_ascii=False))
