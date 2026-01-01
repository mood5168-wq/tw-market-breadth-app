import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import os

DATA_PATH = "data/market_breadth.csv"

# ====== 全上市股票清單 ======
# 這裡用官方證交所資料，可自行更新
# 目前示範用範例清單，可隨時從證交所 CSV 更新
TWSE_LISTED_TICKERS = [
    "2330.TW", "2317.TW", "2454.TW", "2303.TW",
    "1301.TW", "1303.TW", "2881.TW", "2882.TW",
    # ...你可以自行擴充，或用網抓的完整清單
]

# ====== 計算市場寬度 ======
def calculate_market_breadth(tickers=TWSE_LISTED_TICKERS):
    """
    tickers: 股票代碼列表
    return: dict，包含今天市場寬度相關數據
    """
    end = date.today()
    start = end - timedelta(days=7)

    data = yf.download(tickers, start=start, end=end, group_by="ticker", progress=False)

    up = down = flat = 0

    for t in tickers:
        try:
            close = data[t]["Close"].dropna()
            if len(close) < 2:
                continue

            yesterday, today = close.iloc[-2], close.iloc[-1]

            if today > yesterday:
                up += 1
            elif today < yesterday:
                down += 1
            else:
                flat += 1
        except Exception:
            continue

    breadth = up - down
    ratio = up / (up + down) if (up + down) > 0 else 0

    return {
        "date": end.isoformat(),
        "up": up,
        "down": down,
        "flat": flat,
        "breadth": breadth,
        "ratio": round(ratio, 4)
    }

# ====== 存每日結果到 CSV ======
def save_daily_result(result):
    os.makedirs("data", exist_ok=True)

    df_new = pd.DataFrame([result])

    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        if result["date"] in df["date"].values:
            return
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(DATA_PATH, index=False)
