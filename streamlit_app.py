import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Angel One Pro Live Terminal", layout="wide", initial_sidebar_state="collapsed")

# Precise CSS Styling for Mobile Trading
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff !important;
        color: #111827 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header, footer { visibility: hidden; }
    .block-container { padding: 0.2rem 0.4rem 5.5rem 0.4rem; }

    /* Top Watchlist Bar */
    .ticker-bar {
        display: flex;
        overflow-x: auto;
        gap: 6px;
        background: #f8fafc;
        padding: 5px 8px;
        border-bottom: 1px solid #e2e8f0;
        white-space: nowrap;
    }
    .ticker-pill {
        border: 1px solid #cbd5e1;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        background: #ffffff;
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
        padding: 6px 14px;
        font-weight: bold;
        color: #00875a;
        font-size: 14px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if 'active_order' not in st.session_state:
    st.session_state.active_order = {
        'sym': 'TEJASNET.NS',
        'display': 'TEJASNET',
        'qty': 1000,
        'buy_price': 480.00,
        'target': 505.00,
        'stop_loss': 473.50,
        'status': 'OPEN'
    }

if 'timeframe' not in st.session_state:
    st.session_state.timeframe = '15m'

order = st.session_state.active_order

# 1. Top Ticker Watchlist Bar
st.markdown("""
<div class="ticker-bar">
    <span class="ticker-pill" style="border-color:#3b82f6; color:#00875a;">TEJASNET ✕</span>
    <span class="ticker-pill" style="color:#de350b;">BLS 280.15 ✕</span>
    <span class="ticker-pill" style="color:#de350b;">INDIGO 4,282.50 ✕</span>
    <span class="ticker-pill">ITC ✕</span>
</div>
""", unsafe_allow_html=True)

# 2. Timeframe Selection Bar (Angel One Style)
col_sym, col_tf_bar = st.columns([1.2, 3.8])
with col_sym:
    stock_sym = st.selectbox("Stock", ["TEJASNET.NS", "ITC.NS", "BLS.NS", "DRREDDY.NS"], index=0, label_visibility="collapsed")
    order['sym'] = stock_sym
    order['display'] = stock_sym.replace(".NS", "")

with col_tf_bar:
    tf = st.radio("TF", ["1m", "5m", "15m", "1h", "1D", "1W", "1M"], horizontal=True, index=2, label_visibility="collapsed")
    st.session_state.timeframe = tf

# Data Fetching Map
tf_map = {
    "1m": ("1d", "1m"),
    "5m": ("5d", "5m"),
    "15m": ("1mo", "15m"),
    "1h": ("1mo", "60m"),
    "1D": ("1y", "1d"),
    "1W": ("2y", "1wk"),
    "1M": ("5y", "1mo")
}
prd, itv = tf_map[tf]

@st.cache_data(ttl=60)
def fetch_candles(sym, p, i):
    try:
        data = yf.download(sym, period=p, interval=i, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data.dropna()
    except Exception:
        return pd.DataFrame()

df = fetch_candles(order['sym'], prd, itv)

# Fallback with realistic variations if off-market / closed
if df.empty or len(df) < 15:
    np.random.seed(42)
    n_points = 50
    idx = pd.date_range(end=pd.Timestamp.now(), periods=n_points, freq='15min')
    returns = np.random.normal(0.0005, 0.008, n_points)
    price_seq = 480.0 * np.cumprod(1 + returns)
    df = pd.DataFrame({
        'Open': price_seq,
        'High': price_seq * (1 + np.abs(np.random.normal(0, 0.006, n_points))),
        'Low': price_seq * (1 - np.abs(np.random.normal(0, 0.006, n_points))),
        'Close': price_seq * (1 + np.random.normal(0, 0.004, n_points)),
        'Volume': np.random.randint(5000, 80000, n_points)
    }, index=idx)
    df['High'] = np.maximum(df['High'], np.maximum(df['Open'], df['Close']))
    df['Low'] = np.minimum(df['Low'], np.minimum(df['Open'], df['Close']))

curr_ltp = float(df['Close'].iloc[-1])

# SuperTrend (10, 3)
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

# RSI
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / (loss + 1e-9)
df['RSI'] = 100 - (100 / (1 + rs))
rsi_now = float(df['RSI'].iloc[-1])

# MACD
df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
df['Signal'] = df['MACD'].ewm(span=9).mean()
df['Hist'] = df['MACD'] - df['Signal']

# PnL Check
pnl_value = (curr_ltp - order['buy_price']) * order['qty']
pnl_pct = ((curr_ltp - order['buy_price']) / order['buy_price']) * 100
pnl_color = "#00875a" if pnl_value >= 0 else "#de350b"
pnl_sign = "+" if pnl_value >= 0 else ""

# Header Info Strip
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding: 4px 6px; font-size:12px; border-bottom:1px solid #e2e8f0; margin-bottom:2px;">
    <div><b>{order['display']}</b> <span style="color:#00875a; font-weight:bold;">₹{curr_ltp:.2f}</span></div>
    <div><b>SuperTrend:</b> <span style="color:{st_color}; font-weight:bold;">{st_text}</span></div>
    <div><b>RSI (14):</b> <span style="font-weight:bold; color:{'#de350b' if rsi_now>70 else ('#00875a' if rsi_now<30 else '#ff8b00')};">{rsi_now:.1f}</span></div>
</div>
""", unsafe_allow_html=True)

# 3-ROW SUBPLOT: Solid Bold Candlesticks + Volume + MACD
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.70, 0.15, 0.15]
)

# 1. Solid Clear Bold Candlesticks
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
    name="Candles",
    increasing_line_color='#00875a',
    increasing_fillcolor='#00875a',
    decreasing_line_color='#de350b',
    decreasing_fillcolor='#de350b',
    increasing_line_width=1.5,
    decreasing_line_width=1.5
), row=1, col=1)

# 2. SuperTrend Step Line
fig.add_trace(go.Scatter(
    x=df.index, y=df['SuperTrend'], mode='lines',
    line=dict(color=st_color, width=2.5), name="SuperTrend"
), row=1, col=1)

# SuperTrend Value Badge
fig.add_hline(
    y=current_st_val, line_color=st_color, line_width=1,
    annotation_text=f"  SuperTrend {current_st_val}  ",
    annotation_position="right",
    annotation_bgcolor=st_color,
    annotation_font=dict(color="#ffffff", size=10, family="Arial"),
    row=1, col=1
)

# Trade Lines
if order['status'] == 'OPEN':
    fig.add_hline(
        y=order['buy_price'], line_color="#00875a", line_width=1.2,
        annotation_text=f"  BUY INT | {order['qty']}  ✕  ",
        annotation_position="right", annotation_bgcolor="#ffffff",
        annotation_bordercolor="#00875a", annotation_font=dict(color="#00875a", size=10),
        row=1, col=1
    )
    fig.add_hline(
        y=curr_ltp, line_color="#00875a", line_width=1, line_dash="dot",
        annotation_text=f"  {pnl_sign}₹{pnl_value:,.2f} | {order['qty']} ⇅  ",
        annotation_position="right", annotation_bgcolor="#e6f7f2",
        annotation_bordercolor="#00875a", annotation_font=dict(color="#00875a", size=11, weight="bold"),
        row=1, col=1
    )
    fig.add_hline(
        y=order['target'], line_color="#de350b", line_width=1.2,
        annotation_text=f"  SELL TARGET | {order['qty']}  ✕  ",
        annotation_position="right", annotation_bgcolor="#ffebe6",
        annotation_bordercolor="#de350b", annotation_font=dict(color="#de350b", size=10),
        row=1, col=1
    )

# Volume Subplot (Red / Green Solid Bars)
vol_colors = ['#00875a' if c >= o else '#de350b' for c, o in zip(df['Close'], df['Open'])]
fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=vol_colors, name="Volume"), row=2, col=1)

# MACD Subplot
hist_colors = ['#00875a' if v >= 0 else '#de350b' for v in df['Hist']]
fig.add_trace(go.Bar(x=df.index, y=df['Hist'], marker_color=hist_colors, name="Hist"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#0052cc', width=1), name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='#ff8b00', width=1), name="Signal"), row=3, col=1)

fig.update_layout(
    height=460,
    margin=dict(l=5, r=105, t=10, b=10),
    xaxis_rangeslider_visible=False,
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    showlegend=False
)
fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", linecolor="#cbd5e1")
fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", linecolor="#cbd5e1", side="right")

st.plotly_chart(fig, use_container_width=True)

# 3. Bottom Positions & Action Dock
col_pos, col_act = st.columns([3, 2])
with col_pos:
    st.markdown(f"""
    <div style="padding:4px 6px;">
        <div style="font-weight:bold; font-size:13px;">{order['display']} <span style="background:#e6f7f2; color:#00875a; font-size:10px; padding:2px 4px; border-radius:3px;">BUY INT</span></div>
        <div style="color:#64748b; font-size:11px;">{order['qty']} Shares • Avg ₹{order['buy_price']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with col_act:
    st.markdown(f"""
    <div style="text-align:right; font-weight:bold; font-size:14px; color:{pnl_color};">{pnl_sign}₹{pnl_value:,.2f}</div>
    <div style="text-align:right; font-size:11px; color:{pnl_color};">({pnl_sign}{pnl_pct:.2f}%)</div>
    """, unsafe_allow_html=True)
    if st.button("⚡ ONE TAP EXIT"):
        order['status'] = 'ACHIEVED'
        st.toast("Position Exited Successfully!")
        st.rerun()

# Fixed Green Bottom Bar
st.markdown(f"""
<div class="total-green-bar">
    <div>✔ Total P&L</div>
    <div>{pnl_sign}₹{pnl_value:,.2f} ⌃</div>
</div>
""", unsafe_allow_html=True)
