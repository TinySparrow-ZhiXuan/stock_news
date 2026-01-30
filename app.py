import streamlit as st
from yahooquery import Ticker
import feedparser
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Stock Watch", page_icon="📈", layout="centered")
st.title("📈 Stock Watch（Yahoo）")

# 台股配色：漲紅、跌綠、平盤灰
def tw_color(value: float) -> str:
    if value > 0:
        return "#d60000"  # 紅
    elif value < 0:
        return "#008000"  # 綠
    else:
        return "#666666"  # 灰

def render_tw_metric(label: str, value: str, color: str):
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(200,200,200,0.35);
            border-radius:14px;
            padding:12px 14px;
            margin:4px 0px;
            background: rgba(255,255,255,0.04);
        ">
          <div style="font-size:12px; color:#888; margin-bottom:6px;">
            {label}
          </div>
          <div style="font-size:28px; font-weight:700; color:{color};">
            {value}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def google_news_rss(query: str):
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

@st.cache_data(ttl=30)
def fetch_quote(symbol: str):
    """
    回傳：latest_price, prev_close, fetched_at_str
    yahooquery 在雲端偶爾會回 None / 結構不同，這裡做完整保護避免 App 掛掉
    """
    fetched_at = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    try:
        t = Ticker(symbol)

        # price：可能是 None / dict / 或 symbol key 不存在
        price_map = t.price or {}
        price = price_map.get(symbol) or {}
        if not isinstance(price, dict):
            price = {}

        # summary_detail：也可能是 None / dict / 或 symbol key 不存在
        summary_map = t.summary_detail or {}
        summary = summary_map.get(symbol) or {}
        if not isinstance(summary, dict):
            summary = {}

        latest = price.get("regularMarketPrice")

        # 昨收：summary_detail 沒有就用 price 的 previous close 當備援
        prev_close = summary.get("previousClose")
        if prev_close is None:
            prev_close = price.get("regularMarketPreviousClose")

        return latest, prev_close, fetched_at

    except Exception:
        return None, None, fetched_at

def show_price_panel(symbol: str, display_name: str):
    latest, prev_close, fetched_at = fetch_quote(symbol)

    st.subheader(f"✅ {display_name}")
    st.caption(f"資料抓取時間：{fetched_at}")

    # 抓不到就不要讓整頁掛掉
    if latest is None or prev_close is None:
        st.warning(f"{display_name} 目前抓不到報價（Yahoo: {symbol}），可能暫時被限制或資料延遲，稍後重整再試。")
        return

    diff = float(latest) - float(prev_close)
    diff_pct = (diff / float(prev_close) * 100) if float(prev_close) != 0 else 0

    price_color = "#111111"  # 最新價用深色
    change_color = tw_color(diff)

    c1, c2, c3 = st.columns(3)
    with c1:
        render_tw_metric("目前股價", f"{float(latest):,.2f}", price_color)
    with c2:
        render_tw_metric("漲跌", f"{diff:+.2f}", change_color)
    with c3:
        render_tw_metric("漲跌幅", f"{diff_pct:+.2f}%", change_color)

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

tab1, tab2 = st.tabs(["台積電 2330", "0050"])

with tab1:
    show_price_panel("2330.TW", "台積電 2330")
    st.divider()
    render_news("t2330", "台積電 2330")

with tab2:
    show_price_panel("0050.TW", "0050 元大台灣50")
    st.divider()
    render_news("t0050", "0050 元大台灣50")

