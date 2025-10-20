"""\
Goodinfo 現股當沖（日統計）抓取腳本
目標頁: https://goodinfo.tw/tw/DayTrading.asp?CHT_CAT=DATE&STOCK_ID=6706
做法: requests+headers+Referer -> pandas.read_html 解析表格 -> 分頁合併 -> 清洗欄位
使用: python goodinfo_daytrading_scraper.py  # 會輸出 daytrading_6706.csv
依站方規範控制請求頻率。此程式僅供教學。
"""

import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://goodinfo.tw/tw/DayTrading.asp"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def get_page(session: requests.Session, stock_id: str, page: int | None = None) -> str:
    params = {"STOCK_ID": stock_id, "CHT_CAT": "DATE"}
    if page and page > 1:
        params["PAGE"] = page  # 多數列表頁支援 PAGE，若無效會忽略
    # 多數頁面需要 Referer，提升成功率
    session.headers.update({"Referer": f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"})
    r = session.get(BASE, params=params, timeout=15)
    r.raise_for_status()
    return r.text


def _choose_df(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    # 盡量挑出含有「日期」與「當沖」等欄位的表
    best = []
    for d in dfs:
        cols = "".join(map(str, list(d.columns)))
        if ("日期" in cols) and ("當沖" in cols or "買進" in cols or "賣出" in cols):
            best.append(d)
    if best:
        return best[0].copy()
    # 後備策略: 取列數最多者
    return max(dfs, key=lambda x: x.shape[0]).copy()


def parse_table(html: str) -> pd.DataFrame:
    dfs = pd.read_html(html)  # 以表格為主，穩定度高
    if not dfs:
        return pd.DataFrame()
    df = _choose_df(dfs)

    # 去除重複標題欄、Unnamed 欄
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]
    # 標準化第一欄為 日期
    df.rename(columns={df.columns[0]: "日期"}, inplace=True)

    # 僅保留日期格式的資料列
    date_mask = df["日期"].astype(str).str.match(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}")
    df = df[date_mask].copy()

    # 數值清洗: 去千分位與百分比，無法轉換者為 NaN
    def to_num(x):
        return pd.to_numeric(str(x).replace(",", "").replace("%", ""), errors="coerce")

    for c in df.columns:
        if c != "日期":
            df[c] = df[c].map(to_num)

    df["日期"] = (
        df["日期"].astype(str).str.replace("/", "-")
    )
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期", ascending=False).reset_index(drop=True)
    return df


def has_next_page(html: str) -> bool:
    # 簡單偵測，若無「下一頁」連結或無 PAGE 連結則視為無
    if "下一頁" in html:
        return True
    if re.search(r"DayTrading\.asp[^\"]+PAGE=", html):
        return True
    return False


def crawl_daytrading(stock_id: str = "6706", max_pages: int = 20, delay: float = 1.5) -> pd.DataFrame:
    s = requests.Session()
    s.headers.update(HEADERS)

    frames: list[pd.DataFrame] = []
    for p in range(1, max_pages + 1):
        html = get_page(s, stock_id, page=p if p > 1 else None)
        df = parse_table(html)
        if df.empty:
            break
        frames.append(df)
        if not has_next_page(html):
            break
        time.sleep(delay)

    if not frames:
        return pd.DataFrame()

    out = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["日期"])  # 交叉頁重複
        .sort_values("日期")
        .reset_index(drop=True)
    )
    return out


if __name__ == "__main__":
    stock = "6706"
    df = crawl_daytrading(stock, max_pages=20, delay=1.2)
    print(df.head(10))
    df.to_csv(f"daytrading_{stock}.csv", index=False, encoding="utf-8-sig")
    print(f"saved to daytrading_{stock}.csv")
