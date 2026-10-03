import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import json

st.set_page_config(page_title="Angel One AI Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Precise Angel One CSS Styling
st.markdown("""
<style>
    .stApp {
        background-color: #121722 !important;
        color: #f0f3f8 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header, footer { visibility: hidden; }
    .block-container { padding: 0.2rem 0.5rem 5.5rem 0.5rem; }

    /* Top Navigation Tabs */
    .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .top-tabs { display: flex; gap: 15px; border-bottom: 1px solid #232c3d; padding-bottom: 8px; font-size: 13px; color: #788699; }
    .tab-active { color: #5379fe; font-weight: bold; border-bottom: 2px solid #5379fe; padding-bottom: 8px; }

    /* Cards */
    .angel-card {
        background-color: #1a2230;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        border: 1px solid #232c3d;
    }
    .overall-card {
        background: linear-gradient(135deg, #1b263b 0%, #151d2c 100%);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid #2d3b52;
    }

    /* Colors */
    .loss-red { color: #eb5b62 !important; font-weight: 600; }
    .gain-green { color: #00d09c !important; font-weight: 600; }
    .muted-text { color: #788699; font-size: 12px; }
    .bold-white { color: #f0f3f8; font-weight: 600; }

    /* Fixed Bottom Action Dock */
    .order-dock {
        position: fixed;
        bottom: 34px;
        left: 0;
        width: 100%;
        background-color: #161c28;
        border-top: 1px solid #232c3d;
        padding: 6px 12px;
        z-index: 998;
    }
    .total-green-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #064e3b;
        border-top: 1px solid #00d09c;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 14px;
        font-weight: bold;
        color: #ffffff;
        font-size: 13px;
        z-index: 999;
    }

    /* Bottom Navigation Bar */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #161c28;
        display: flex;
        justify-content: space-around;
        padding: 6px 0;
        border-top: 1px solid #232c3d;
        z-index: 999;
    }
    .nav-item { text-align: center; color: #788699; font-size: 10px; }
    .nav-active { color: #5379fe !important; font-weight: bold; }
    .nav-icon { font-size: 16px; margin-bottom: 2px; }

    /* Custom Buttons */
    div.buy-btn > button {
        background-color: #00d09c !important;
        color: #121722 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        width: 100% !important;
        border: none !important;
    }
    div.sell-btn > button {
        background-color: #eb5b62 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        width: 100% !important;
        border: none !important;
    }
    div.neutral-btn > button {
        background-color: #232c3d !important;
        color: #f0f3f8 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        width: 100% !important;
        border: 1px solid #374151 !important;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'portfolio'
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = 'ITC'
if 'dock_tab' not in st.session_state:
    st.session_state.dock_tab = 'Positions'

# Holdings / Stock Data
portfolio_data = {
    'ITC': {'name': 'ITC Ltd', 'sym': 'ITC.NS', 'shares': 1850, 'atp': 308.21, 'ltp': 255.90, 'inv': 570197, 'val': 473415, 'pnl': -96773.49, 'pnl_pct': -16.97, 'today_pnl': -12.50, 'today_pnl_pct': -0.01, 'status': 'OPEN', 'target': 262.00, 'sl': 253.50},
    'FIVESTAR': {'name': 'Five-Star Business', 'sym': 'FIVESTAR.NS', 'shares': 50, 'atp': 516.85, 'ltp': 506.25, 'inv': 25842, 'val': 25312, 'pnl': -530.00, 'pnl_pct': -2.05, 'today_pnl': -10.60, 'today_pnl_pct': -2.05, 'status': 'OPEN', 'target': 520.00, 'sl': 498.00},
    'TEJASNET': {'name': 'Tejas Networks', 'sym': 'TEJASNET.NS', 'shares': 1000, 'atp': 480.00, 'ltp': 497.00, 'inv': 480000, 'val': 497000, 'pnl': 17000.00, 'pnl_pct': 3.54, 'today_pnl': 24.50, 'today_pnl_pct': 0.50, 'status': 'OPEN', 'target': 508.00, 'sl': 474.00},
    'BLS': {'name': 'BLS International', 'sym': 'BLS.NS', 'shares': 100, 'atp': 282.00, 'ltp': 280.15, 'inv': 28200, 'val': 28015, 'pnl': -185.00, 'pnl_pct': -0.65, 'today_pnl': -1.85, 'today_pnl_pct': -0.65, 'status': 'OPEN', 'target': 290.00, 'sl': 275.00}
}

# ========================================================
# SCREEN 1: PORTFOLIO SCREEN
# ========================================================
if st.session_state.current_view == 'portfolio':
    st.markdown("""
    <div class="top-header">
        <div style="font-size: 18px; font-weight: bold;">Holdings <span style="font-size:13px; font-weight:normal; color:#788699;">My Wealth</span></div>
        <div style="font-size: 16px; color: #788699;">👤 🔍 ⋮</div>
    </div>
    <div class="top-tabs">
        <div>Overview</div>
        <div class="tab-active">Equity</div>
        <div>Mutual Funds</div>
        <div>Investment Picks</div>
    </div>
    <br>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="overall-card">
        <div style="font-size: 22px; font-weight: bold;">₹16,02,788 👁️</div>
        <div class="loss-red" style="font-size:12px; margin: 3px 0 10px 0;">↓ Overall Loss -₹3,17,701.45 (-16.54%)</div>
        <div style="display:flex; justify-content:space-between; border-top: 1px solid #232c3d; padding-top: 6px;">
            <div>
                <div class="muted-text">Invested Value</div>
                <div class="bold-white" style="font-size:13px;">₹19,20,509</div>
            </div>
            <div style="text-align: right;">
                <div class="muted-text">Today's Gain</div>
                <div class="gain-green" style="font-size:13px;">+₹0.01 (+0.00%)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for key, item in portfolio_data.items():
        c_body, c_btn = st.columns([4, 1])
        t_cls = 'gain-green' if item['today_pnl'] >= 0 else 'loss-red'
        t_sgn = '+' if item['today_pnl'] >= 0 else ''
        o_cls = 'gain-green' if item['pnl'] >= 0 else 'loss-red'
        o_sgn = '+' if item['pnl'] >= 0 else ''

        with c_body:
            st.markdown(f"""
            <div class="angel-card">
                <div style="display:flex; justify-content:space-between;">
                    <div><b>{key}</b> <span class="muted-text">({item['shares']} shares)</span></div>
                    <div class="{o_cls}">{o_sgn}₹{item['pnl']:,.2f} ({o_sgn}{item['pnl_pct']:.2f}%)</div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:4px;">
                    <div class="muted-text">ATP: ₹{item['atp']:.2f} | Inv: ₹{item['inv']:,}</div>
                    <div><span class="muted-text">LTP:</span> <b class="bold-white">₹{item['ltp']:.2f}</b></div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:4px; border-top:1px dashed #232c3d; padding-top:4px;">
                    <div class="muted-text">Current: ₹{item['val']:,}</div>
                    <div><span class="muted-text">Today's P&L:</span> <span class="{t_cls}">{t_sgn}₹{item['today_pnl']:,.2f} ({t_sgn}{item['today_pnl_pct']:.2f}%)</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_btn:
            st.markdown('<div class="neutral-btn">', unsafe_allow_html=True)
            if st.button("View", key=f"btn_v_{key}"):
                st.session_state.selected_stock = key
                st.session_state.current_view = 'detail'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="bottom-nav">
        <div class="nav-item"><div class="nav-icon">🏠</div>HOME</div>
        <div class="nav-item"><div class="nav-icon">⭐</div>WATCHLIST</div>
        <div class="nav-item nav-active"><div class="nav-icon">📁</div>PORTFOLIO</div>
        <div class="nav-item"><div class="nav-icon">📑</div>ORDERS</div>
        <div class="nav-item"><div class="nav-icon">👤</div>ACCOUNT</div>
    </div>
    """, unsafe_allow_html=True)

# ========================================================
# SCREEN 2: STOCK DETAIL OVERVIEW
# ========================================================
elif st.session_state.current_view == 'detail':
    stock = portfolio_data[st.session_state.selected_stock]
    t_cls = 'gain-green' if stock['today_pnl'] >= 0 else 'loss-red'
    t_sgn = '+' if stock['today_pnl'] >= 0 else ''

    top_c1, top_c2 = st.columns([1, 4])
    with top_c1:
        st.markdown('<div class="neutral-btn">', unsafe_allow_html=True)
        if st.button("← Back"):
            st.session_state.current_view = 'portfolio'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with top_c2:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div><b style="font-size:16px;">{stock['name']}</b> <span class="muted-text">NSE</span></div>
            <div style="text-align:right;"><b style="font-size:16px; color:#00d09c;">₹{stock['ltp']:.2f}</b><br><span class="{t_cls}" style="font-size:11px;">{t_sgn}₹{stock['today_pnl']:.2f} ({t_sgn}{stock['today_pnl_pct']:.2f}%)</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="angel-card" style="margin-top:10px;">
        <div class="muted-text">Overall P&L 👁</div>
        <div class="{'gain-green' if stock['pnl']>=0 else 'loss-red'}" style="font-size:20px;">₹{stock['pnl']:,.2f} ({stock['pnl_pct']:.2f}%)</div>
        <hr style="border-color:#232c3d; margin:8px 0;">
        <div style="display:grid; grid-template-columns: 1fr 1fr; row-gap:10px;">
            <div><span class="muted-text">Total Quantity</span><br><b>{stock['shares']}</b></div>
            <div><span class="muted-text">Avg Traded Price</span><br><b>₹{stock['atp']:.2f}</b></div>
            <div><span class="muted-text">Invested</span><br><b>₹{stock['inv']:,}</b></div>
            <div><span class="muted-text">Market Value</span><br><b>₹{stock['val']:,}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    btn_chart, btn_b, btn_s = st.columns([1.5, 1.5, 1.5])
    with btn_chart:
        st.markdown('<div class="neutral-btn">', unsafe_allow_html=True)
        if st.button("📊 Open Chart"):
            st.session_state.current_view = 'chart'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_b:
        st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
        if st.button("BUY"): st.toast("Buy Order Placed")
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_s:
        st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
        if st.button("SELL"): st.toast("Sell Order Placed")
        st.markdown('</div>', unsafe_allow_html=True)

# ========================================================
# SCREEN 3: ALL-IN-ONE PRO TRADINGVIEW TERMINAL
# ========================================================
elif st.session_state.current_view == 'chart':
    stock = portfolio_data[st.session_state.selected_stock]

    # Header with Back to Holdings Button & Timeframes
    c_back, c_tf = st.columns([1, 4])
    with c_back:
        st.markdown('<div class="neutral-btn">', unsafe_allow_html=True)
        if st.button("← Back", help="Return to Portfolio"):
            st.session_state.current_view = 'portfolio'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c_tf:
        tf = st.radio("TF", ["1m", "5m", "15m", "1h", "1D"], horizontal=True, index=2, label_visibility="collapsed")

    tf_map = {"1m": ("1d", "1m"), "5m": ("5d", "5m"), "15m": ("1mo", "15m"), "1h": ("1mo", "60m"), "1D": ("1y", "1d")}
    prd, itv = tf_map[tf]

    @st.cache_data(ttl=60)
    def fetch_terminal_data(s, p, i):
        try:
            d = yf.download(s, period=p, interval=i, progress=False)
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
            d = d.dropna().reset_index()
            t_col = d.columns[0]
            d['time'] = (d[t_col].astype('int64') // 10**9)
            return d
        except:
            return pd.DataFrame()

    df = fetch_terminal_data(stock['sym'], prd, itv)
    if df.empty or len(df) < 15:
        idx = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='15min')
        prices = np.cumsum(np.random.randn(50) * 0.3) + stock['ltp']
        df = pd.DataFrame({
            'time': (idx.astype('int64') // 10**9),
            'Open': prices - 0.2, 'High': prices + 0.5, 'Low': prices - 0.4, 'Close': prices,
            'Volume': np.random.randint(5000, 50000, 50)
        })

    curr_ltp = round(float(df['Close'].iloc[-1]), 2)
    high_val = round(float(df['High'].max()), 2)
    low_val = round(float(df['Low'].min()), 2)
    open_val = round(float(df['Open'].iloc[0]), 2)
    pdc_val = round(open_val - 0.45, 2)

    # SuperTrend (10, 3)
    df['TR'] = (df['High'] - df['Low'])
    df['ATR'] = df['TR'].rolling(10).mean().bfill()
    df['ST'] = (df['High'] + df['Low']) / 2
    st_val = round(float(df['ST'].iloc[-1]), 2)
    is_bullish = curr_ltp > st_val
    st_color = "#00d09c" if is_bullish else "#eb5b62"

    # Indicators: RSI & Strength Score
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi_now = float((100 - (100 / (1 + rs))).iloc[-1])
    strength_pct = int(min(max(abs(rsi_now - 50) * 2 + 30, 10), 96))

    # 4-Color Scale
    if strength_pct >= 75:
        str_color = "#00d09c"
        str_label = "HIGH STRENGTH (GREEN)"
    elif strength_pct >= 50:
        str_color = "#ffeb3b"
        str_label = "MODERATE (YELLOW)"
    elif strength_pct >= 40:
        str_color = "#ff8a80"
        str_label = "WEAKENING (LIGHT PINK/RED)"
    else:
        str_color = "#d50000"
        str_label = "EXTREME RISK (RED)"

    # Fake Breakout Check
    fake_msg = "✅ NORMAL ACTION"
    fake_bg = "#1f2937"
    if curr_ltp >= high_val and rsi_now > 72:
        fake_msg = "⚠️ FAKE BULLISH BREAKOUT (TRAP)"
        fake_bg = "#7f1d1d"
    elif curr_ltp <= low_val and rsi_now < 28:
        fake_msg = "⚠️ FAKE BEARISH BREAKDOWN (TRAP)"
        fake_bg = "#7f1d1d"

    # PnL Check
    if stock['status'] == 'OPEN':
        pnl_val = (curr_ltp - stock['atp']) * stock['shares']
        pnl_pct = ((curr_ltp - stock['atp']) / stock['atp']) * 100
    else:
        pnl_val = (stock['target'] - stock['atp']) * stock['shares']
        pnl_pct = ((stock['target'] - stock['atp']) / stock['atp']) * 100
    pnl_col = "#00d09c" if pnl_val >= 0 else "#eb5b62"
    pnl_sgn = "+" if pnl_val >= 0 else ""

    candle_json = json.dumps([{
        "time": int(r['time']), "open": float(r['Open']),
        "high": float(r['High']), "low": float(r['Low']), "close": float(r['Close'])
    } for _, r in df.iterrows()])

    st_json = json.dumps([{
        "time": int(r['time']), "value": float(r['ST'])
    } for _, r in df.iterrows()])

    # Top Status Bar (Fake Breakout & 4-Color Scale)
    st.markdown(f"""
    <div style="background:{fake_bg}; padding:6px 10px; border-radius:6px; font-size:11px; font-weight:bold; text-align:center; margin-bottom:4px; border:1px solid #374151;">
        {fake_msg} • Strength: <span style="color:{str_color};">{strength_pct}% ({str_label})</span>
    </div>
    """, unsafe_allow_html=True)

    # Native TradingView Chart with All Scales, Reset Button, High/Low/PDC/Tags
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #121722; overflow: hidden; }}
            #tv_chart {{ width: 100vw; height: 440px; position: relative; }}
            #reset_btn {{
                position: absolute; bottom: 25px; right: 75px; width: 32px; height: 32px;
                background: #1c2432; border: 1px solid #2d3b52; border-radius: 50%;
                display: flex; align-items: center; justify-content: center; cursor: pointer;
                z-index: 100; color: #788699; font-size: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.5);
            }}
            #reset_btn:active {{ background: #2a3649; transform: scale(0.92); }}
        </style>
    </head>
    <body>
        <div id="tv_chart">
            <div id="reset_btn" title="Scroll to Realtime">🔄</div>
        </div>
        <script>
            const chart = LightweightCharts.createChart(document.getElementById('tv_chart'), {{
                width: window.innerWidth,
                height: 440,
                layout: {{ backgroundColor: '#121722', textColor: '#788699' }},
                grid: {{ vertLines: {{ color: '#1a2230' }}, horzLines: {{ color: '#1a2230' }} }},
                crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                rightPriceScale: {{ borderColor: '#232c3d', autoScale: true }},
                timeScale: {{ borderColor: '#232c3d', timeVisible: true, secondsVisible: false }},
                handleScroll: {{ vertTouchDrag: true }},
                handleScale: {{ axisPressedMouseMove: {{ time: true, price: true }} }}
            }});

            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#00d09c', downColor: '#eb5b62',
                borderUpColor: '#00d09c', borderDownColor: '#eb5b62',
                wickUpColor: '#00d09c', wickDownColor: '#eb5b62'
            }});
            candleSeries.setData({candle_json});

            const stSeries = chart.addLineSeries({{ color: '{st_color}', lineWidth: 2, title: 'SuperTrend' }});
            stSeries.setData({st_json});

            // 1. High Line
            candleSeries.createPriceLine({{ price: {high_val}, color: '#00d09c', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: 'High' }});

            // 2. Low Line
            candleSeries.createPriceLine({{ price: {low_val}, color: '#eb5b62', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: 'Low' }});

            // 3. SuperTrend Label
            stSeries.createPriceLine({{ price: {st_val}, color: '{st_color}', lineWidth: 1, axisLabelVisible: true, title: 'SuperTrend' }});

            // 4. Previous Day Close
            candleSeries.createPriceLine({{ price: {pdc_val}, color: '#788699', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: 'PDC' }});

            // 5. In-Chart Order Execution & PnL Boxes
            {'candleSeries.createPriceLine({ price: ' + str(stock['atp']) + ', color: "#00d09c", lineWidth: 1.5, axisLabelVisible: true, title: "BUY INT | ' + str(stock['shares']) + ' ✕" });' if stock['status'] == 'OPEN' else ''}
            {'candleSeries.createPriceLine({ price: ' + str(curr_ltp) + ', color: "#00d09c", lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: "' + pnl_sgn + '₹' + f"{pnl_val:,.2f}" + ' | ' + str(stock['shares']) + ' ⇅" });' if stock['status'] == 'OPEN' else ''}
            {'candleSeries.createPriceLine({ price: ' + str(stock['target']) + ', color: "#eb5b62", lineWidth: 1.5, axisLabelVisible: true, title: "TARGET EXIT | ' + str(stock['shares']) + ' ✕" });' if stock['status'] == 'OPEN' else ''}

            // Realtime Reset Button
            document.getElementById('reset_btn').addEventListener('click', () => {{
                chart.timeScale().scrollToRealTime();
                chart.priceScale('right').applyOptions({{ autoScale: true }});
            }});
            chart.timeScale().scrollToRealTime();

            window.addEventListener('resize', () => {{
                chart.applyOptions({{ width: window.innerWidth }});
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=450)

    # Bottom Half-Screen Dock (Trade | Open Orders | Positions)
    st.markdown('<div class="order-dock">', unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns([1, 1.2, 1.2, 1])
    with d1:
        if st.button("Trade"): st.session_state.dock_tab = 'Trade'
    with d2:
        if st.button("Open Orders"): st.session_state.dock_tab = 'Orders'
    with d3:
        if st.button("Positions"): st.session_state.dock_tab = 'Positions'
    with d4:
        if st.button("Option Chain"): st.session_state.dock_tab = 'Option'

    if st.session_state.dock_tab == 'Positions':
        if stock['status'] == 'OPEN':
            p1, p2 = st.columns([3, 2])
            with p1:
                st.markdown(f"""
                <div style="font-size:13px; font-weight:bold;">{stock['name']} <span style="background:#064e3b; color:#00d09c; font-size:10px; padding:1px 4px; border-radius:3px;">BUY INT</span></div>
                <div class="muted-text">{stock['shares']} Shares • Avg ₹{stock['atp']:.2f}</div>
                """, unsafe_allow_html=True)
            with p2:
                st.markdown(f"""
                <div style="text-align:right; font-weight:bold; font-size:13px; color:{pnl_col};">{pnl_sgn}₹{pnl_val:,.2f}</div>
                <div style="text-align:right; font-size:11px; color:{pnl_col};">LTP {curr_ltp:.2f} ({pnl_sgn}{pnl_pct:.2f}%)</div>
                """, unsafe_allow_html=True)
                if st.button("⚡ ONE TAP EXIT"):
                    stock['status'] = 'ACHIEVED'
                    st.toast("Target Achieved & Exited!")
                    st.rerun()
        else:
            st.info("✅ அனைத்து நிலைகளும் டார்கெட்டை அடைந்துவிட்டன.")

    elif st.session_state.dock_tab == 'Orders':
        if stock['status'] == 'OPEN':
            st.markdown(f"""
            <div style="background:#1a2230; padding:6px 10px; border-radius:6px; font-size:12px; display:flex; justify-content:space-between;">
                <div><b>{stock['name']} (TARGET)</b><br><span class="muted-text">Limit Pending • Qty: {stock['shares']}</span></div>
                <div style="color:#eb5b62; font-weight:bold;">₹{stock['target']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write("பெண்டிங் ஆர்டர்கள் இல்லை.")

    elif st.session_state.dock_tab == 'Trade':
        b1, b2 = st.columns(2)
        with b1:
            st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
            if st.button(f"BUY @ ₹{curr_ltp:.2f}"):
                stock['status'] = 'OPEN'
                st.toast("Buy Order Placed")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with b2:
            st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
            if st.button(f"SELL @ ₹{curr_ltp:.2f}"):
                stock['status'] = 'ACHIEVED'
                st.toast("Sell Order Placed")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Fixed Bottom Green Total Bar
    st.markdown(f"""
    <div class="total-green-bar">
        <div>✔ Total P&L</div>
        <div>{pnl_sgn}₹{pnl_val:,.2f} ⌃</div>
    </div>
    """, unsafe_allow_html=True)
