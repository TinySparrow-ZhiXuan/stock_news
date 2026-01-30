import streamlit as st
import streamlit.components.v1 as components
import feedparser
import urllib.parse
import requests
from datetime import datetime
import uuid

st.set_page_config(page_title="Stock Watch", page_icon="📈", layout="centered")
st.title("📈 Stock Watch（TWSE）")

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
st.title("📈 Stock Watch")

def google_news_rss(query: str):
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

@st.cache_data(ttl=15)
def fetch_twse_quote(code: str):
    """
    走 TWSE 即時報價 (mis.twse.com.tw)
    回傳：latest, prev_close, fetched_at
    """
    fetched_at = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    # 上市：tse_2330.tw ；ETF 0050 也是 tse_0050.tw
    ex_ch = f"tse_{code}.tw"

    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    params = {"ex_ch": ex_ch, "_": str(int(datetime.now().timestamp() * 1000))}

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        arr = data.get("msgArray", [])
        if not arr:
            return None, None, fetched_at

        q = arr[0]

        # 當盤價：z（成交價），沒成交時可能是 "-"，用當日收盤/現價欄位備援
        z = q.get("z")
        latest = None
        if z and z != "-":
            latest = float(z)

        # 昨收：y
        y = q.get("y")
        prev_close = None
        if y and y != "-":
            prev_close = float(y)

        # 若最新價缺失，嘗試用「當日收盤/現價」備援（有時用這些欄位會比較有值）
        if latest is None:
            # 有時候會給 o(開) / h(高) / l(低) / z(成交) / pz(盤後?)，但最常用還是 z
            # 如果 z 沒有，就先不硬塞，避免錯誤
            pass

        return latest, prev_close, fetched_at

    except Exception:
        return None, None, fetched_at
    st.write("HTTP status:", r.status_code)
    st.write("Text head:", r.text[:200])


def show_price_panel(code: str, display_name: str):
    latest, prev_close, fetched_at = fetch_twse_quote(code)

    st.subheader(f"✅ {display_name}")
    st.caption(f"資料抓取時間：{fetched_at}")

    if latest is None or prev_close is None:
        st.warning(f"{display_name} 目前抓不到報價（TWSE: {code}），可能暫時連線不穩或非交易時段資料欄位為空，請稍後重整。")
        return

    diff = latest - prev_close
    diff_pct = (diff / prev_close * 100) if prev_close != 0 else 0

    price_color = "#111111"
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
@@ -135,14 +25,67 @@ def render_news(key_prefix: str, default_query: str):
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
    show_price_panel("2330", "台積電 2330")
    # TradingView 台股代號常用 TWSE:2330
    render_tradingview_quote("TWSE:2330", "台積電 2330", theme="light")
    render_tradingview_chart("TWSE:2330", theme="light")
    st.divider()
    render_news("t2330", "台積電 2330")

with tab2:
    show_price_panel("0050", "0050 元大台灣50")
    render_tradingview_quote("TWSE:0050", "0050 元大台灣50", theme="light")
    render_tradingview_chart("TWSE:0050", theme="light")
    st.divider()
    render_news("t0050", "0050 元大台灣50")
