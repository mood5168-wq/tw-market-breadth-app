import streamlit as st
import pandas as pd
from market_breadth import calculate_market_breadth, save_daily_result

st.set_page_config(page_title="台股市場寬度", layout="wide")
st.title("📊 台股市場寬度（每日紀錄 + 異常提醒）")

tickers = [
    "2330.TW", "2317.TW", "2454.TW", "2303.TW",
    "1301.TW", "1303.TW", "2881.TW", "2882.TW"
]

# 計算並存檔
result = calculate_market_breadth(tickers)
save_daily_result(result)

# 讀歷史資料
df = pd.read_csv("data/market_breadth.csv", parse_dates=["date"])
df["month"] = df["date"].dt.to_period("M").astype(str)

# === 異常提醒邏輯 ===
# 最近 5 天市場寬度平均與標準差
recent = df.tail(5)
mean_breadth = recent["breadth"].mean()
std_breadth = recent["breadth"].std()

if result["breadth"] < mean_breadth - 2 * std_breadth:
    st.warning(f"🔔 異常提醒：市場突然大轉弱！今天市場寬度 {result['breadth']}，遠低於過去 5 天平均 {mean_breadth:.1f}")

