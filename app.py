import json
from pathlib import Path
import streamlit as st
import feedparser
import urllib.parse

st.set_page_config(page_title="Stock Watch", page_icon="📈", layout="centered")
st.title("📈 Stock Watch（GitHub Cache）")

def tw_color(value: float) -> str:
    if value > 0:
        return "#d60000"
    elif value < 0:
        return "#008000"
    return "#666666"

def render_tw_metric(label: str, value: str, color: str):
    st.markdown(
        f"""
        <div style="border:1px solid rgba(200,200,200,0.35); border-radius:14px;
                    padding:12px 14px; margin:4px 0px; background: rgba(255,255,255,0.04);">
          <div style="font-size:12px; color:#888; margin-bottom:6px;">{label}</div>
          <div style="font-size:28px; font-weight:700; color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def read_quotes():
    p = Path("data/quotes.json")
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def google_news_rss(query: str):
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

def render_news(key_prefix: str, default_query: str):
    st.subheader("📰 今日新聞")
    query = st.text_input("新聞關鍵字", value=default_query, key=f"{key_prefix}_news").strip()
    if not query:
        return
    feed = feedparser.parse(google_news_rss(query))
    if not getattr(feed, "entries", None):
        st.info("目前抓不到新聞，可能 RSS 暫時無資料或網路限制。")
        return
    for e in feed.entries[:10]:
        st.markdown(f"- [{e.get('title','（無標題）')}]({e.get('link','')})")

data = read_quotes()
if not data:
    st.warning("還沒有 quotes.json（請等 GitHub Actions 跑一次，或到 Actions 手動 Run）")
    st.stop()

st.caption(f"資料抓取時間：{data.get('fetched_at','-')}（由 GitHub Actions 定時更新）")

items = data.get("items", {})

tab1, tab2 = st.tabs(["台積電 2330", "0050"])

def show(sym: str):
    it = items.get(sym, {})
    latest = it.get("latest")
    prev = it.get("prev_close")
    name = it.get("name", sym)

    st.subheader(f"✅ {name}")

    if latest is None or prev is None:
        st.warning("目前資料缺失（等下一次 Actions 更新）")
        return

    diff = float(latest) - float(prev)
    diff_pct = (diff / float(prev) * 100) if float(prev) != 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        render_tw_metric("目前股價", f"{float(latest):,.2f}", "#111111")
    with c2:
        render_tw_metric("漲跌", f"{diff:+.2f}", tw_color(diff))
    with c3:
        render_tw_metric("漲跌幅", f"{diff_pct:+.2f}%", tw_color(diff))

with tab1:
    show("2330.TW")
    st.divider()
    render_news("t2330", "台積電 2330")

with tab2:
    show("0050.TW")
    st.divider()
    render_news("t0050", "0050 元大台灣50")
