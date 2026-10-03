import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="Angel One Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Precise Angel One CSS Styling
st.markdown("""
<style>
    .stApp {
        background-color: #121722 !important;
        color: #f0f3f8 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 0.8rem; padding-bottom: 5rem; padding-left: 0.8rem; padding-right: 0.8rem; }

    .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .top-tabs { display: flex; gap: 15px; border-bottom: 1px solid #232c3d; padding-bottom: 8px; font-size: 14px; color: #788699; }
    .tab-active { color: #5379fe; font-weight: bold; border-bottom: 2px solid #5379fe; padding-bottom: 8px; }

    .angel-card {
        background-color: #1a2230;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        border: 1px solid #232c3d;
    }
    .overall-card {
        background: linear-gradient(135deg, #1b263b 0%, #151d2c 100%);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 15px;
        border: 1px solid #2d3b52;
    }

    .loss-red { color: #eb5b62 !important; font-weight: 600; }
    .gain-green { color: #00d09c !important; font-weight: 600; }
    .muted-text { color: #788699; font-size: 12px; }
    .bold-white { color: #f0f3f8; font-weight: 600; }

    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #161c28;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        border-top: 1px solid #232c3d;
        z-index: 9999;
    }
    .nav-item { text-align: center; color: #788699; font-size: 11px; text-decoration: none; }
    .nav-active { color: #5379fe !important; font-weight: bold; }
    .nav-icon { font-size: 18px; margin-bottom: 2px; }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'portfolio'
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = 'ITC'

portfolio_data = {
    'ITC': {'name': 'ITC Ltd', 'sym': 'ITC.NS', 'shares': 1850, 'atp': 308.21, 'ltp': 255.90, 'inv': 570197, 'val': 473415, 'pnl': -96773.49, 'pnl_pct': -16.97},
    'DRREDDY': {'name': "Dr. Reddy's Lab", 'sym': 'DRREDDY.NS', 'shares': 1, 'atp': 1316.81, 'ltp': 1206.20, 'inv': 1316, 'val': 1206, 'pnl': -110.61, 'pnl_pct': -8.41},
    'ITCHOTELS': {'name': 'ITC Hotels', 'sym': 'ITCHOTELS.NS', 'shares': 8, 'atp': 513.47, 'ltp': 158.51, 'inv': 4107, 'val': 1268, 'pnl': -2839.68, 'pnl_pct': -69.14},
    'SAKUMA': {'name': 'Sakuma Exports', 'sym': 'SAKUMA.NS', 'shares': 100, 'atp': 7.80, 'ltp': 5.40, 'inv': 780, 'val': 540, 'pnl': -240.00, 'pnl_pct': -30.87}
}

# ========================================================
# 1. SCREEN 1: PORTFOLIO SCREEN
# ========================================================
if st.session_state.current_view == 'portfolio':
    st.markdown("""
    <div class="top-header">
        <div style="font-size: 20px; font-weight: bold;">Holdings <span style="font-size:14px; font-weight:normal; color:#788699;">My Wealth</span></div>
        <div style="font-size: 18px; color: #788699;">👤 🔍 ⋮</div>
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
        <div style="font-size: 24px; font-weight: bold;">₹16,02,788 👁️</div>
        <div class="loss-red" style="font-size:13px; margin: 4px 0 12px 0;">↓ Overall Loss -₹3,17,701.45 (-16.54%)</div>
        <div style="display:flex; justify-content:space-between; border-top: 1px solid #232c3d; padding-top: 8px;">
            <div>
                <div class="muted-text">Invested Value</div>
                <div class="bold-white" style="font-size:14px;">₹19,20,509</div>
            </div>
            <div style="text-align: right;">
                <div class="muted-text">Today's Gain</div>
                <div class="gain-green" style="font-size:14px;">+₹0.01 (+0.00%)</div>
            </div>
        </div>
    </div>
    <div style="color:#788699; font-size:13px; margin-bottom:8px;">🔍 Search stocks by company</div>
    """, unsafe_allow_html=True)

    for key, item in portfolio_data.items():
        c_body, c_btn = st.columns([4, 1])
        with c_body:
            st.markdown(f"""
            <div class="angel-card">
                <div style="display:flex; justify-content:space-between;">
                    <div style="font-weight:bold; font-size:15px;">{key}</div>
                    <div class="{'gain-green' if item['pnl']>=0 else 'loss-red'}">₹{item['pnl']:,.2f} ({item['pnl_pct']:.2f}%)</div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:3px;">
                    <div class="muted-text">ATP ₹{item['atp']:.2f}</div>
                    <div><span class="muted-text">LTP</span> <span class="bold-white">₹{item['ltp']:.2f}</span></div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:2px;">
                    <div class="muted-text">Shares {item['shares']}</div>
                    <div class="muted-text">Current ₹{item['val']:,}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_btn:
            if st.button("View", key=f"v_{key}"):
                st.session_state.selected_stock = key
                st.session_state.current_view = 'detail'
                st.rerun()

# ========================================================
# 2. SCREEN 2: STOCK DETAIL OVERVIEW
# ========================================================
elif st.session_state.current_view == 'detail':
    stock = portfolio_data[st.session_state.selected_stock]

    top_c1, top_c2 = st.columns([1, 4])
    with top_c1:
        if st.button("← Back"):
            st.session_state.current_view = 'portfolio'
            st.rerun()
    with top_c2:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:18px; font-weight:bold;">{stock['name']}</div>
                <div class="muted-text">NSE</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:18px; font-weight:bold; color:#eb5b62;">₹{stock['ltp']:.2f} ▼</div>
                <div class="loss-red" style="font-size:12px;">-6.85 (-2.61%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    dates = pd.date_range(end=pd.Timestamp.now(), periods=30)
    prices = np.linspace(stock['atp'], stock['ltp'], 30) + np.random.normal(0, 1.5, 30)
    fig_mini = go.Figure()
    fig_mini.add_trace(go.Scatter(x=dates, y=prices, mode='lines', line=dict(color='#eb5b62', width=2), fill='tozeroy', fillcolor='rgba(235,91,98,0.08)'))
    fig_mini.update_layout(template="plotly_dark", height=130, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor="#121722", paper_bgcolor="#121722")
    st.plotly_chart(fig_mini, use_container_width=True)

    st.markdown(f"""
    <div class="angel-card">
        <div class="muted-text">Overall Loss 👁️</div>
        <div class="loss-red" style="font-size:22px;">₹{stock['pnl']:,.2f} ({stock['pnl_pct']:.2f}%)</div>
        <hr style="border-color:#232c3d; margin:10px 0;">
        <div style="display:grid; grid-template-columns: 1fr 1fr; row-gap:12px;">
            <div><span class="muted-text">Total Quantity</span><br><b>{stock['shares']}</b></div>
            <div><span class="muted-text">Avg Traded Price</span><br><b>₹{stock['atp']:.2f}</b></div>
            <div><span class="muted-text">Invested</span><br><b>₹{stock['inv']:,}</b></div>
            <div><span class="muted-text">Market Value</span><br><b>₹{stock['val']:,}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    btn_chart, btn_b, btn_s = st.columns([2, 1.5, 1.5])
    with btn_chart:
        if st.button("📊 Charts", type="secondary"):
            st.session_state.current_view = 'chart'
            st.rerun()
    with btn_b:
        if st.button("BUY", type="primary"):
            st.toast("Buy Order Placed")
    with btn_s:
        if st.button("SELL"):
            st.toast("Sell Order Placed")

# ========================================================
# 3. SCREEN 3: ADVANCED YOUTUBE STYLE CHART TERMINAL
# ========================================================
elif st.session_state.current_view == 'chart':
    stock = portfolio_data[st.session_state.selected_stock]
    sym = stock['sym']

    c_bk, c_tf = st.columns([1, 4])
    with c_bk:
        if st.button("← Details"):
            st.session_state.current_view = 'detail'
            st.rerun()
    with c_tf:
        tf_choice = st.radio("TF", ["1m", "5m", "15m", "1h", "1D", "1W"], horizontal=True, index=2, label_visibility="collapsed")

    tf_lookup = {"1m": ("1d", "1m"), "5m": ("5d", "5m"), "15m": ("1mo", "15m"), "1h": ("1mo", "60m"), "1D": ("1y", "1d"), "1W": ("2y", "1wk")}
    p, i = tf_lookup[tf_choice]

    @st.cache_data(ttl=60)
    def fetch_chart_data(s, prd, itv):
        d = yf.download(s, period=prd, interval=itv, progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        return d.dropna()

    df = fetch_chart_data(sym, p, i)
    if df.empty or len(df) < 25:
        st.warning("கேண்டில் டேட்டா ஏற்றப்படவில்லை. மீண்டும் முயற்சிக்கவும்.")
        st.stop()

    curr_ltp = float(df['Close'].iloc[-1])

    # SuperTrend Calculation (10, 3)
    df['TR'] = np.maximum((df['High'] - df['Low']), np.maximum(abs(df['High'] - df['Close'].shift(1)), abs(df['Low'] - df['Close'].shift(1))))
    df['ATR'] = df['TR'].rolling(10).mean().bfill()
    df['Basic_UB'] = (df['High'] + df['Low']) / 2 + (3 * df['ATR'])
    df['Basic_LB'] = (df['High'] + df['Low']) / 2 - (3 * df['ATR'])

    supertrend = [df['Basic_LB'].iloc[0]]
    st_dir = [True]
    for idx in range(1, len(df)):
        c = df['Close'].iloc[idx]
        prev_st = supertrend[-1]
        is_up = st_dir[-1]
        if is_up:
            st_val = max(df['Basic_LB'].iloc[idx], prev_st) if c > prev_st else df['Basic_UB'].iloc[idx]
            is_up = c > prev_st
        else:
            st_val = min(df['Basic_UB'].iloc[idx], prev_st) if c < prev_st else df['Basic_LB'].iloc[idx]
            is_up = c >= prev_st
        supertrend.append(st_val)
        st_dir.append(is_up)
    df['SuperTrend'] = supertrend
    df['ST_Dir'] = st_dir

    # RSI & Volume SMA
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    rsi_now = float(df['RSI'].iloc[-1])
    vol_sma = df['Volume'].rolling(20).mean().iloc[-1]
    vol_now = df['Volume'].iloc[-1]

    # Strength Metric (4-Color Scale)
    strength_pct = int(min(max(abs(rsi_now - 50) * 2 + (vol_now / (vol_sma + 1e-9) * 20), 10), 98))
    if strength_pct >= 75:
        str_color = "#00d09c"
        str_label = "STRONG BULLISH / BEARISH"
        trend_line_color = "#00d09c"
    elif strength_pct >= 50:
        str_color = "#ffeb3b"
        str_label = "MODERATE MOMENTUM"
        trend_line_color = "#ffeb3b"
    elif strength_pct >= 40:
        str_color = "#ff8a80"
        str_label = "WEAKENING / NEUTRAL"
        trend_line_color = "#ff8a80"
    else:
        str_color = "#d50000"
        str_label = "EXTREME RISK / EXHAUSTION"
        trend_line_color = "#d50000"

    # Pattern Recognition (Evening Star / Triangle / Channel)
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    detected_pattern = "Consolidation / Channel Range"
    if c1['Close'] > c1['Open'] and abs(c2['Close'] - c2['Open']) < (c1['High'] - c1['Low']) * 0.3 and c3['Close'] < c3['Open']:
        detected_pattern = "Evening Star Pattern (Bearish Reversal)"
    elif c1['Close'] < c1['Open'] and abs(c2['Close'] - c2['Open']) < (c1['High'] - c1['Low']) * 0.3 and c3['Close'] > c3['Open']:
        detected_pattern = "Morning Star Pattern (Bullish Reversal)"

    recent_high = float(df['High'].iloc[-20:].max())
    recent_low = float(df['Low'].iloc[-20:].min())
    is_downtrend = not df['ST_Dir'].iloc[-1]
    trend_state = "DOWNTREND" if is_downtrend else "UPTREND"

    # Target & Stop Loss Calculation
    stop_loss = round(df['SuperTrend'].iloc[-1], 2)
    risk_diff = abs(curr_ltp - stop_loss)
    target = round(curr_ltp - (risk_diff * 1.5), 2) if is_downtrend else round(curr_ltp + (risk_diff * 1.5), 2)

    # YouTube Style Achievement Check
    achieved = (curr_ltp <= target) if is_downtrend else (curr_ltp >= target)
    achieve_text = "🎉 TARGET ACHIEVED! (+1:1.5 RR)" if achieved else "⏳ RUNNING IN TARGET DIRECTION"
    achieve_bg = "#064e3b" if achieved else "#1a2230"

    # Plotly Subplot
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Candles", increasing_line_color='#00d09c', decreasing_line_color='#eb5b62'
    ), row=1, col=1)

    # 1. Parallel Channel / Flag Box (YouTube Flag Pattern)
    x_start, x_end = df.index[-20], df.index[-1]
    fig.add_shape(type="rect",
        x0=x_start, y0=recent_low, x1=x_end, y1=recent_high,
        line=dict(color=trend_line_color, width=1.5, dash="dot"),
        fillcolor=str_color, opacity=0.08,
        row=1, col=1
    )

    # 2. Risk-Reward Target Achievement Box (Green Target Zone / Red SL Zone)
    target_box_top = max(curr_ltp, target)
    target_box_bot = min(curr_ltp, target)
    sl_box_top = max(curr_ltp, stop_loss)
    sl_box_bot = min(curr_ltp, stop_loss)

    # Green Target Box
    fig.add_shape(type="rect",
        x0=df.index[-8], y0=target_box_bot, x1=df.index[-1], y1=target_box_top,
        line=dict(color="#00d09c", width=1), fillcolor="#00d09c", opacity=0.2,
        row=1, col=1
    )
    # Red Stop Loss Box
    fig.add_shape(type="rect",
        x0=df.index[-8], y0=sl_box_bot, x1=df.index[-1], y1=sl_box_top,
        line=dict(color="#eb5b62", width=1), fillcolor="#eb5b62", opacity=0.2,
        row=1, col=1
    )

    # Target & Stop Loss Lines with Badges
    fig.add_hline(y=target, line_color="#00d09c", line_dash="dash", annotation_text=f"🎯 TARGET ₹{target}", row=1, col=1)
    fig.add_hline(y=stop_loss, line_color="#eb5b62", line_dash="dash", annotation_text=f"🛑 SL ₹{stop_loss}", row=1, col=1)

    # SuperTrend Step Line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SuperTrend'], mode='lines',
        line=dict(color='#eb5b62' if is_downtrend else '#00d09c', width=2),
        name="SuperTrend"
    ), row=1, col=1)

    # Volume Subplot
    colors_vol = ['#00d09c' if c >= o else '#eb5b62' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name="Volume"), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", height=520, margin=dict(l=5, r=5, t=10, b=10),
        xaxis_rangeslider_visible=False,
        plot_bgcolor="#121722", paper_bgcolor="#121722",
        legend=dict(orientation="h", y=1.03, x=0, font=dict(size=10))
    )
    st.plotly_chart(fig, use_container_width=True)

    # YouTube Trade Achievement & Pattern Banner
    st.markdown(f"""
    <div style="background:{achieve_bg}; padding:10px 14px; border-radius:8px; border:1px solid #2d3b52; margin-bottom:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:bold; font-size:14px; color:#f0f3f8;">{achieve_text}</div>
            <div style="color:#788699; font-size:12px;">Pattern: <b style="color:#ffeb3b;">{detected_pattern}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Strength & Signal Card directly above Buy/Sell Buttons with 4-Color Scale
    st.markdown(f"""
    <div style="background:#1a2230; padding:10px 14px; border-radius:8px; margin-bottom:10px; border:1px solid #232c3d;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div><b>Trend:</b> <span style="color:{'#eb5b62' if is_downtrend else '#00d09c'}; font-weight:bold;">{trend_state}</span></div>
            <div><b>Strength:</b> <span style="color:{str_color}; font-size:15px; font-weight:bold;">{strength_pct}% ({str_label})</span></div>
            <div><b>LTP:</b> ₹{curr_ltp:.2f}</div>
        </div>
        <div style="width:100%; background:#232c3d; height:7px; border-radius:4px; margin-top:8px;">
            <div style="width:{strength_pct}%; background:{str_color}; height:7px; border-radius:4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # In-Chart Instant Buy / Sell Buttons
    c_buy, c_sell = st.columns(2)
    with c_buy:
        if st.button(f"BUY @ ₹{curr_ltp:.2f}", type="primary"):
            st.toast(f"Buy Order Executed @ ₹{curr_ltp:.2f}")
    with c_sell:
        if st.button(f"SELL @ ₹{curr_ltp:.2f}"):
            st.toast(f"Sell Order Executed @ ₹{curr_ltp:.2f}")

# ========================================================
# 4. FIXED BOTTOM NAVIGATION BAR
# ========================================================
st.markdown("""
<div class="bottom-nav">
    <div class="nav-item"><div class="nav-icon">🏠</div>HOME</div>
    <div class="nav-item"><div class="nav-icon">⭐</div>WATCHLIST</div>
    <div class="nav-item nav-active"><div class="nav-icon">📁</div>PORTFOLIO</div>
    <div class="nav-item"><div class="nav-icon">📑</div>ORDERS</div>
    <div class="nav-item"><div class="nav-icon">👤</div>ACCOUNT</div>
</div>
""", unsafe_allow_html=True)
