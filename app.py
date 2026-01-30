import streamlit as st
from yahooquery import Ticker
import feedparser
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Stock Watch", page_icon="📈", layout="centered")
st.title("📈 Stock Watch（Yahoo）")

# ✅ 台股配色：漲紅、跌綠、平盤灰
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
    """
    t = Ticker(symbol)
    price = t.price.get(symbol, {})
    summary = t.summary_detail.get(symbol, {})

    latest = price.get("regularMarketPrice")
    prev_close = summary.get("previousClose")

    # ✅ 取資料時間（用台灣時間）
    fetched_at = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    return latest, prev_close, fetched_at

def show_price_panel(symbol: str, display_name: str):
    latest, prev_close, fetched_at = fetch_quote(symbol)

    if latest is None or prev_close is None:
        st.error(f"抓不到 {display_name} 的資料（Yahoo: {symbol}）")
        return

    diff = latest - prev_close
    diff_pct = (diff / prev_close * 100) if prev_close != 0 else 0

    st.subheader(f" {display_name}")

    # ✅ 旁邊備註抓取時間
    st.caption(f"資料抓取時間：{fetched_at}")

    price_color = "#FFFFFF"
    change_color = tw_color(diff)

    c1, c2, c3 = st.columns(3)
    with c1:
        render_tw_metric("目前股價", f"{latest:,.2f}", price_color)
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
    if not feed.entries:
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
