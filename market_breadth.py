# market_breadth.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import pandas as pd

import yfinance as yf


DEFAULT_CSV = Path("data") / "market_breadth.csv"


def calculate_market_breadth(tickers: list[str], flat_epsilon: float = 0.0) -> dict:
    """
    回傳格式範例：
    {
      "date": "2026-01-02",
      "up": 5, "down": 2, "flat": 1,
      "breadth": 3,
      "ratio": 0.7142857143
    }
    """
    up = down = flat = 0
    last_dates = []

    errors = []

    for t in tickers:
        try:
            df = yf.download(
                t,
                period="10d",      # 關鍵：不要只抓 1d
                interval="1d",
                progress=False,
                threads=False
            )

            if df is None or df.empty:
                raise ValueError("download 回傳空資料")

            df = df.dropna(subset=["Close"])
            if len(df) < 2:
                raise ValueError(f"交易日資料不足（rows={len(df)}）")

            last_close = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2])
            last_dt = pd.to_datetime(df.index[-1]).date()
            last_dates.append(last_dt)

            diff = last_close - prev_close
            if diff > flat_epsilon:
                up += 1
            elif diff < -flat_epsilon:
                down += 1
            else:
                flat += 1

        except Exception as e:
            # 不要讓單一股票掛掉就整個 breadth 不能算
            errors.append((t, str(e)))
            continue

    # 以「最後可用交易日」為 date（避免你硬用 today 導致 mismatch）
    date = max(last_dates).isoformat() if last_dates else datetime.now().date().isoformat()

    breadth = up - down
    denom = (up + down)
    ratio = (up / denom) if denom > 0 else None

    result = {
        "date": date,
        "up": up,
        "down": down,
        "flat": flat,
        "breadth": breadth,
        "ratio": ratio,
        "errors": errors,  # 建議保留，方便你在 UI 顯示哪幾檔失敗
    }
    return result


def save_daily_result(result: dict, csv_path: str | Path = DEFAULT_CSV) -> None:
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "date": result["date"],
        "up": result["up"],
        "down": result["down"],
        "flat": result["flat"],
        "breadth": result["breadth"],
        "ratio": result["ratio"],
    }

    if path.exists():
        df = pd.read_csv(path)
        # 若同一天已存在就覆寫（避免 Streamlit rerun 一直重複寫）
        df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
        if row["date"] in set(df["date"].tolist()):
            df.loc[df["date"] == row["date"], list(row.keys())] = list(row.values())
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(path, index=False)
