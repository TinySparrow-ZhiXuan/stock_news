import streamlit as st
import streamlit.components.v1 as components
import feedparser
import urllib.parse
import uuid

st.set_page_config(page_title="Stock Watch", page_icon="📈", layout="centered")
st.title("📈 Stock Watch")

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

def render_tradingview_quote(symbol: str, title: str, height: int = 220, theme: str = "light"):
    """
    用 TradingView 的「Symbol Info」widget：
    會顯示：最新價、漲跌、漲跌幅（你要的都有）
    """
    wid = uuid.uuid4().hex  # 確保每次 container id 唯一，避免互相覆蓋
    html = f"""
    <div>
      <h3 style="margin: 0 0 8px 0;">{title}</h3>
      <div class="tradingview-widget-container" style="width:100%;">
        <div class="tradingview-widget-container__widget" id="tv_{wid}"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js" async>
        {{
          "symbol": "{symbol}",
          "width": "100%",
          "locale": "zh_TW",
          "colorTheme": "{theme}",
          "isTransparent": false
        }}
        </script>
      </div>
    </div>
    """
    components.html(html, height=height, scrolling=False)

def render_tradingview_chart(symbol: str, height: int = 420, theme: str = "light"):
    """
    可選：如果你想要圖，也可以用 TradingView Mini Chart
    """
    wid = uuid.uuid4().hex
    html = f"""
    <div class="tradingview-widget-container" style="width:100%;">
      <div class="tradingview-widget-container__widget" id="tv_chart_{wid}"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
      {{
        "symbol": "{symbol}",
        "width": "100%",
        "height": "{height}",
        "locale": "zh_TW",
        "dateRange": "6M",
        "colorTheme": "{theme}",
        "isTransparent": false,
        "autosize": true,
        "largeChartUrl": ""
      }}
      </script>
    </div>
    """
    components.html(html, height=height + 40, scrolling=False)

tab1, tab2 = st.tabs(["台積電 2330", "0050"])

with tab1:
    # TradingView 台股代號常用 TWSE:2330
    render_tradingview_quote("TWSE:2330", "台積電 2330", theme="light")
    render_tradingview_chart("TWSE:2330", theme="light")
    st.divider()
    render_news("t2330", "台積電 2330")

with tab2:
    render_tradingview_quote("TWSE:0050", "0050 元大台灣50", theme="light")
    render_tradingview_chart("TWSE:0050", theme="light")
    st.divider()
    render_news("t0050", "0050 元大台灣50")
