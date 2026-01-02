# market_breadth.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf

CSV_PATH = Path("data") / "market_breadth.csv"


def calculate_market_breadth(tickers: list[str], lookback: str = "10d") -> dict:
    up = down = flat = 0
    processed = 0
    errors: list[dict] = []
    last_dates = []

    for t in tickers:
        try:
            df = yf.download(
                t,
                period=lookback,   # 重要：不要只抓 1d
                interval="1d",
                progress=False,
                threads=False,
            )

            if df is None or df.empty:
                raise ValueError("下載結果為空（可能被限流/無法連線/代碼無資料）")

            df = df.dropna(subset=["Close"])
            if len(df) < 2:
                raise ValueError(f"交易日資料不足（rows={len(df)}，請加長 lookback）")

            prev_close = float(df["Close"].iloc[-2])
            last_close = float(df["Close"].iloc[-1])

            last_dt = pd.to_datetime(df.index[-1]).date()
            last_dates.append(last_dt)

            diff = last_close - prev_close
            if diff > 0:
                up += 1
            elif diff < 0:
                down += 1
            else:
                flat += 1

            processed += 1

        except Exception as e:
            errors.append({"ticker": t, "error": str(e)})

    # 如果一檔都沒成功，直接丟錯，不要寫 0 假資料
    if processed == 0:
        raise RuntimeError(f"所有 ticker 都抓不到資料。errors={errors}")

    date = max(last_dates).isoformat() if last_dates else datetime.now().date().isoformat()
    breadth = up - down
    denom = up + down
    ratio = (up / denom) if denom > 0 else None

    return {
        "date": date,
        "up": up,
        "down": down,
        "flat": flat,
        "breadth": breadth,
        "ratio": ratio,
        "processed": processed,
        "errors": errors,   # 保留：讓你在前端看到哪幾檔失敗
    }


def save_daily_result(result: dict, csv_path: Path = CSV_PATH) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # 強制欄位存在，避免你截圖那種 up 空白
    row = {
        "date": result["date"],
        "up": int(result.get("up", 0) or 0),
        "down": int(result.get("down", 0) or 0),
        "flat": int(result.get("flat", 0) or 0),
        "breadth": int(result.get("breadth", 0) or 0),
        "ratio": (float(result["ratio"]) if result.get("ratio") is not None else None),
    }

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)

        # 同一天就覆寫，避免 Streamlit rerun 重複寫同日多筆
        if row["date"] in set(df["date"].tolist()):
            df.loc[df["date"] == row["date"], list(row.keys())] = list(row.values())
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(csv_path, index=False)
