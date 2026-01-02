import streamlit as st
import pandas as pd
from pathlib import Path
from market_breadth import calculate_market_breadth, save_daily_result

# ================= Streamlit 基本設定 =================
st.set_page_config(page_title="台股市場寬度", layout="wide")
st.title("📊 台股市場寬度（每日紀錄 + 異常提醒）")

# ================= 路徑（非常重要：避免 data/ 不存在） =================
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "market_breadth.csv"

# ================= 股票代碼設定 =================
tickers = [
    "2330.TW", "2317.TW", "2454.TW", "2303.TW",
    "1301.TW", "1303.TW", "2881.TW", "2882.TW"
]

# ================= 抓取快取：避免 Streamlit 一直 rerun 打爆資料源 =================
@st.cache_data(ttl=15 * 60)  # 15 分鐘內重跑不重抓
def cached_market_breadth(tickers_tuple):
    return calculate_market_breadth(list(tickers_tuple))

# ================= 計算今日市場寬度並存檔（含錯誤顯示） =================
with st.spinner("抓取行情並計算市場寬度..."):
    try:
        result = cached_market_breadth(tuple(tickers))
    except Exception as e:
        st.error(f"❌ calculate_market_breadth 失敗：{e}")
        st.stop()

# 顯示本次計算結果，方便你確認「到底有沒有抓到」
with st.expander("🔎 本次計算 result（除錯用）", expanded=False):
    st.write(result)

# 存檔
try:
    save_daily_result(result)  # 你原本函式若寫死路徑，也至少確保 data/ 存在
except Exception as e:
    st.error(f"❌ save_daily_result 存檔失敗：{e}")
    st.stop()

# ================= 讀歷史資料（含檔案不存在防呆） =================
if not CSV_PATH.exists():
    st.warning(f"找不到歷史檔案：{CSV_PATH}。代表存檔沒有成功，請先看上方錯誤。")
    st.stop()

try:
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
except Exception as e:
    st.error(f"❌ 讀取 CSV 失敗：{e}")
    st.stop()

if df.empty:
    st.info("歷史資料目前是空的（可能是首次執行，或存檔內容不完整）。")
    st.stop()

# 確保數值欄位是數字，避免 line_chart 因為字串而畫不出來
for col in ["up", "down", "flat", "breadth", "ratio"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["month"] = df["date"].dt.to_period("M").astype(str)

# ================= 異常提醒（std 可能是 NaN 要處理） =================
recent = df.tail(5)
mean_breadth = recent["breadth"].mean()
std_breadth = recent["breadth"].std()

if pd.notna(std_breadth) and std_breadth > 0:
    if result["breadth"] < mean_breadth - 2 * std_breadth:
        st.warning(
            f"🔔 異常提醒：市場突然大轉弱！今天市場寬度 {result['breadth']}，"
            f"遠低於過去 5 天平均 {mean_breadth:.1f}"
        )

# ================= 每月 Tab 顯示 =================
months = sorted(df["month"].dropna().unique(), reverse=True)
tabs = st.tabs(months)

for tab, month in zip(tabs, months):
    with tab:
        mdf = df[df["month"] == month].sort_values("date")

        st.subheader(f"📅 {month} 每日市場寬度")
        st.dataframe(
            mdf[["date", "up", "down", "flat", "breadth", "ratio"]],
            use_container_width=True
        )

        st.subheader("📈 市場寬度趨勢")
        st.line_chart(mdf.set_index("date")["breadth"])

        st.subheader("📊 上漲比率趨勢")
        st.line_chart(mdf.set_index("date")["ratio"])
