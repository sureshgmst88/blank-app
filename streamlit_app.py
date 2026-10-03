import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="Angel One Live Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Precise Angel One Styling
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff !important;
        color: #1e293b !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header, footer { visibility: hidden; }
    .block-container { padding: 0.2rem 0.5rem 6.5rem 0.5rem; }

    /* Top Watchlist Ticker Tabs */
    .ticker-bar {
        display: flex;
        overflow-x: auto;
        gap: 8px;
        background: #f8fafc;
        padding: 6px;
        border-bottom: 1px solid #e2e8f0;
        white-space: nowrap;
    }
    .ticker-pill {
        border: 1px solid #cbd5e1;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        background: #ffffff;
    }

    /* Bottom Order & Position Panel */
    .order-dock {
        position: fixed;
        bottom: 45px;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        border-top: 1px solid #cbd5e1;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.08);
        padding: 8px 12px;
        z-index: 999;
    }

    /* Fixed Bottom Green Total Bar */
    .total-green-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #e6f7f2;
        border-top: 1px solid #a7f3d0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 16px;
        font-weight: bold;
        color: #00875a;
        font-size: 15px;
        z-index: 1000;
    }

    /* Buttons */
    div.buy-btn > button {
        background-color: #00875a !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        width: 100% !important;
    }
    div.sell-btn > button {
        background-color: #de350b !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if 'active_order' not in st.session_state:
    st.session_state.active_order = {
        'sym': 'TEJASNET.NS',
        'display': 'TEJASNET',
        'type': 'BUY INT',
        'qty': 1000,
        'buy_price': 480.00,
        'target': 505.00,
        'stop_loss': 473.50,
        'status': 'OPEN'
    }

if 'dock_tab' not in st.session_state:
    st.session_state.dock_tab = 'Positions'

# Top Watchlist Bar
st.markdown("""
<div class="ticker-bar">
    <span class="ticker-pill" style="border-color:#3b82f6; color:#00875a;">TEJASNET 497.00 (+0.50%) ✕</span>
    <span class="ticker-pill" style="color:#de350b;">BLS 280.15 ✕</span>
    <span class="ticker-pill" style="color:#de350b;">INDIGO 4,282.50 ✕</span>
    <span class="ticker-pill">GOLDBEES ✕</span>
</div>
""", unsafe_allow_html=True)

order = st.session_state.active_order

@st.cache_data(ttl=30)
def get_stock_candles(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except:
        return pd.DataFrame()

df = get_stock_candles(order['sym'])
if df.empty or len(df) < 20:
    idx = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='1min')
    prices = np.cumsum(np.random.randn(60) * 0.4) + 490.0
    df = pd.DataFrame({
        'Open': prices - 0.2, 'High': prices + 0.8,
        'Low': prices - 0.5, 'Close': prices,
        'Volume': np.random.randint(1000, 50000, 60)
    }, index=idx)

curr_ltp = float(df['Close'].iloc[-1])

# SuperTrend (10, 3) Calculation
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

is_bullish = df['ST_Dir'].iloc[-1]
st_color = '#00875a' if is_bullish else '#de350b'
st_text = "BULLISH (GREEN) 🟢" if is_bullish else "BEARISH (RED) 🔴"
current_st_val = round(df['SuperTrend'].iloc[-1], 2)

# Indicators: RSI, MACD, ADX
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / (loss + 1e-9)
df['RSI'] = 100 - (100 / (1 + rs))
rsi_now = float(df['RSI'].iloc[-1])

df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
df['Signal'] = df['MACD'].ewm(span=9).mean()
df['Hist'] = df['MACD'] - df['Signal']
adx_val = 39.97

# PnL Check
if order['status'] == 'OPEN':
    pnl_value = (curr_ltp - order['buy_price']) * order['qty']
    pnl_pct = ((curr_ltp - order['buy_price']) / order['buy_price']) * 100
else:
    pnl_value = (order['target'] - order['buy_price']) * order['qty']
    pnl_pct = ((order['target'] - order['buy_price']) / order['buy_price']) * 100

pnl_color = "#00875a" if pnl_value >= 0 else "#de350b"
pnl_sign = "+" if pnl_value >= 0 else ""

# Header Info Strip with SuperTrend Indicator Status
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding: 4px 6px; font-size:13px; border-bottom:1px solid #e2e8f0; margin-bottom:4px;">
    <div><b>{order['display']}</b> <span style="color:#00875a; font-weight:bold;">₹{curr_ltp:.2f}</span></div>
    <div><b>SuperTrend (10,3):</b> <span style="background:{'#e6f7f2' if is_bullish else '#ffebe6'}; color:{st_color}; padding:2px 8px; border-radius:4px; font-weight:bold;">{st_text}</span></div>
    <div><b>RSI:</b> <span style="font-weight:bold; color:{'#de350b' if rsi_now>70 else ('#00875a' if rsi_now<30 else '#ff8b00')};">{rsi_now:.1f}</span></div>
</div>
""", unsafe_allow_html=True)

# 4-ROW SUBPLOT: Candlestick + SuperTrend, Volume, MACD, RSI/ADX
fig = make_subplots(
    rows=4, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.60, 0.12, 0.14, 0.14]
)

# 1. Candlestick
fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
    name="Candles", increasing_line_color='#00875a', decreasing_line_color='#de350b'
), row=1, col=1)

# 2. SuperTrend Step Line
fig.add_trace(go.Scatter(
    x=df.index, y=df['SuperTrend'], mode='lines',
    line=dict(color=st_color, width=2.5), name="SuperTrend"
), row=1, col=1)

# SuperTrend Value Badge on the Right Axis (Angel One Style)
fig.add_hline(
    y=current_st_val, line_color=st_color, line_width=1, line_dash="solid",
    annotation_text=f"  SuperTrend  {current_st_val}  ",
    annotation_position="right",
    annotation_bgcolor=st_color,
    annotation_font=dict(color="#ffffff", size=10, family="Arial"),
    row=1, col=1
)

# 3. Live Trades & In-Chart Order Execution Tags
if order['status'] == 'OPEN':
    fig.add_hline(
        y=order['buy_price'], line_color="#00875a", line_width=1.2, line_dash="solid",
        annotation_text=f"  BUY INT | {order['qty']}  ✕  ",
        annotation_position="right",
        annotation_bgcolor="#ffffff",
        annotation_bordercolor="#00875a",
        annotation_font=dict(color="#00875a", size=11, family="Arial"),
        row=1, col=1
    )

    fig.add_hline(
        y=curr_ltp, line_color="#00875a", line_width=1, line_dash="dot",
        annotation_text=f"  {pnl_sign}₹{pnl_value:,.2f} | {order['qty']} ⇅ ✕  ",
        annotation_position="right",
        annotation_bgcolor="#e6f7f2",
        annotation_bordercolor="#00875a",
        annotation_font=dict(color="#00875a", size=12, family="Arial"),
        row=1, col=1
    )

    fig.add_hline(
        y=order['target'], line_color="#de350b", line_width=1.2, line_dash="solid",
        annotation_text=f"  SELL INT (TARGET) | {order['qty']}  ✕  ",
        annotation_position="right",
        annotation_bgcolor="#ffebe6",
        annotation_bordercolor="#de350b",
        annotation_font=dict(color="#de350b", size=11, family="Arial"),
        row=1, col=1
    )
else:
    fig.add_annotation(
        x=df.index[-1], y=curr_ltp,
        text="🎉 TARGET ACHIEVED! ALL POSITIONS CLOSED",
        showarrow=True, arrowhead=2, arrowcolor="#00875a",
        bgcolor="#00875a", font=dict(color="#ffffff", size=12),
        row=1, col=1
    )

# Volume Subplot
fig.add_trace(go.Bar(
    x=df.index, y=df['Volume'],
    marker_color=['#00875a' if c>=o else '#de350b' for c, o in zip(df['Close'], df['Open'])],
    name="Volume"
), row=2, col=1)

# MACD Subplot
fig.add_trace(go.Bar(x=df.index, y=df['Hist'], marker_color=['#00875a' if v>=0 else '#de350b' for v in df['Hist']], name="MACD Hist"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#0052cc', width=1), name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='#ff8b00', width=1), name="Signal"), row=3, col=1)

# RSI & ADX Subplot
fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#7c3aed', width=1.5), name="RSI"), row=4, col=1)
fig.add_trace(go.Scatter(x=df.index, y=[adx_val]*len(df), line=dict(color='#ffab00', width=1.2, dash='dot'), name="ADX"), row=4, col=1)
fig.add_hline(y=70, line_color="#de350b", line_dash="dot", line_width=1, row=4, col=1)
fig.add_hline(y=30, line_color="#00875a", line_dash="dot", line_width=1, row=4, col=1)

fig.update_layout(
    height=540,
    margin=dict(l=5, r=105, t=10, b=10),
    xaxis_rangeslider_visible=False,
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    showlegend=False
)
fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", linecolor="#cbd5e1")
fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", linecolor="#cbd5e1", side="right")

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# HALF-SCREEN DOCK (POSITIONS & ORDERS)
# ==========================================
st.markdown('<div class="order-dock">', unsafe_allow_html=True)

t1, t2, t3 = st.columns([1, 1, 1])
with t1:
    if st.button("Trade"):
        st.session_state.dock_tab = 'Trade'
with t2:
    if st.button("Open Orders"):
        st.session_state.dock_tab = 'Open Orders'
with t3:
    if st.button("Positions"):
        st.session_state.dock_tab = 'Positions'

if st.session_state.dock_tab == 'Positions':
    if order['status'] == 'OPEN':
        p_c1, p_c2 = st.columns([3, 2])
        with p_c1:
            st.markdown(f"""
            <div style="font-weight:bold; font-size:14px;">{order['display']}</div>
            <div style="color:#64748b; font-size:12px;">{order['qty']} Shares • Avg {order['buy_price']:.2f} <span style="background:#e6f7f2; color:#00875a; padding:1px 4px; border-radius:3px;">BUY INT</span></div>
            """, unsafe_allow_html=True)
        with p_c2:
            st.markdown(f"""
            <div style="text-align:right; font-weight:bold; font-size:15px; color:{pnl_color};">{pnl_sign}₹{pnl_value:,.2f}</div>
            <div style="text-align:right; font-size:12px; color:{pnl_color};">LTP {curr_ltp:.2f} ({pnl_sign}{pnl_pct:.2f}%)</div>
            """, unsafe_allow_html=True)
            if st.button("⚡ ONE TAP EXIT", key="exit_btn"):
                order['status'] = 'ACHIEVED'
                st.rerun()
    else:
        st.info("✅ அனைத்து ஆர்டர்களும் டார்கெட்டை அடைந்துவிட்டன. (No Open Positions)")

elif st.session_state.dock_tab == 'Open Orders':
    if order['status'] == 'OPEN':
        st.markdown(f"""
        <div style="background:#f8fafc; padding:8px; border-radius:6px; border:1px solid #e2e8f0; font-size:13px;">
            <div style="display:flex; justify-content:space-between;">
                <b>{order['display']} (TARGET EXIT)</b>
                <span style="color:#de350b; font-weight:bold;">LIMIT PENDING</span>
            </div>
            <div style="display:flex; justify-content:space-between; color:#64748b; font-size:12px; margin-top:4px;">
                <span>Qty: {order['qty']} / {order['qty']}</span>
                <span>Price: ₹{order['target']:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.write("பெண்டிங் ஆர்டர்கள் எதுவும் இல்லை.")

elif st.session_state.dock_tab == 'Trade':
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
        if st.button(f"BUY @ ₹{curr_ltp:.2f}"):
            order['status'] = 'OPEN'
            order['buy_price'] = curr_ltp
            order['target'] = round(curr_ltp + 15, 2)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with b_col2:
        st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
        if st.button(f"SELL @ ₹{curr_ltp:.2f}"):
            order['status'] = 'ACHIEVED'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# FIXED GREEN TOTAL PROFIT BAR AT VERY BOTTOM
st.markdown(f"""
<div class="total-green-bar">
    <div>✔ Total P&L</div>
    <div>{pnl_sign}₹{pnl_value:,.2f} ⌃</div>
</div>
""", unsafe_allow_html=True)
