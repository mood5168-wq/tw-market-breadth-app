import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import os

# 存資料的路徑
DATA_PATH = "data/market_breadth.csv"

# ====== 計算市場寬度的核心函數 ======
def calculate_market_breadth(tickers):
    """
    tickers: 股票代碼列表，例如 ["2330.TW", "2317.TW"]
    return: dict，包含今天市場寬度相關數據
    """
    end = date.today()
    start = end - timedelta(days=7)  # 抓最近 7 天資料，確保有前一天比較

    # 抓股票歷史資料
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
    """
    result: dict，calculate_market_breadth 回傳的字典
    功能: 將結果 append 到 CSV，如果 CSV 不存在就創建
    """
    os.makedirs("data", exist_ok=True)

    df_new = pd.DataFrame([result])

    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        # 避免同一天重複寫入
        if result["date"] in df["date"].values:
            return
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(DATA_PATH, index=False)

