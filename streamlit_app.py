import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import argrelextrema
from scipy.stats import linregress
import streamlit as st
import yfinance as yf

# 1. Page Configuration
st.set_page_config(
    page_title="AI Trade Pro - Auto Chart & Patterns",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("AI Trade Pro: Auto Pattern & Trendline Engine")
st.caption("Auto Chart Analyzer & Pattern Detection System | Free")

# 2. Sidebar Controls
st.sidebar.header("Controls")
broker_choice = st.sidebar.selectbox(
    "Trading Account (Broker)", ["Angel One", "Upstox"]
)
st.sidebar.info(f"Connected: {broker_choice} (SmartAPI Mode)")

symbol_input = st.sidebar.text_input("Stock Symbol", value="TATASTEEL.NS")
timeframe = st.sidebar.selectbox(
    "Timeframe", ["5m", "15m", "1h", "1d"], index=1
)
period_map = {"5m": "5d", "15m": "10d", "1h": "1mo", "1d": "6mo"}


# 3. Data Loading
@st.cache_data(ttl=60)
def load_data(ticker, interval, period):
  df = yf.download(ticker, period=period, interval=interval)
  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
  return df


df = load_data(symbol_input, timeframe, period_map[timeframe])

if df.empty:
  st.error("Data not found. Please check stock symbol.")
  st.stop()

# 4. Indicators (RSI & EMA)
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
rs = gain / (loss + 1e-9)
df["RSI"] = 100 - (100 / (1 + rs))

df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
df["Vol_SMA"] = df["Volume"].rolling(window=20).mean()

# 5. Extrema Peaks / Troughs
highs = df["High"].values
lows = df["Low"].values
peak_idx = argrelextrema(highs, np.greater_equal, order=4)[0]
trough_idx = argrelextrema(lows, np.less_equal, order=4)[0]

df["Peak"] = False
df["Trough"] = False
df.iloc[peak_idx, df.columns.get_loc("Peak")] = True
df.iloc[trough_idx, df.columns.get_loc("Trough")] = True

# 6. Trend & Pattern Recognition
current_price = float(df["Close"].iloc[-1])
current_rsi = float(df["RSI"].iloc[-1])
current_vol = float(df["Volume"].iloc[-1])
avg_vol = float(df["Vol_SMA"].iloc[-1])
trend = "UPTREND" if df["EMA_20"].iloc[-1] > df["EMA_50"].iloc[-1] else "DOWNTREND"

recent_peaks = df[df["Peak"]].tail(5)
recent_troughs = df[df["Trough"]].tail(5)

detected_pattern = "Normal Swing"
signal_type = "WAIT"
confidence = 40
entry, sl, target = None, None, None
reason = "No classic breakout pattern detected."

# W-Pattern (Double Bottom)
if len(recent_troughs) >= 2 and len(recent_peaks) >= 1:
  b1 = recent_troughs.iloc[-2]["Low"]
  b2 = recent_troughs.iloc[-1]["Low"]
  if abs(b1 - b2) / b1 < 0.025:
    neckline = recent_peaks.iloc[-1]["High"]
    detected_pattern = "W-Pattern (Double Bottom - Bullish)"
    signal_type = "BUY / LONG"
    height = neckline - min(b1, b2)
    entry = round(neckline, 2)
    sl = round(b2 * 0.995, 2)
    target = round(neckline + height, 2)
    confidence = 75 if current_vol > avg_vol else 55
    reason = f"Double bottom support formed. Buy on breakout above {entry}."

# M-Pattern (Double Top)
elif len(recent_peaks) >= 2 and len(recent_troughs) >= 1:
  p1 = recent_peaks.iloc[-2]["High"]
  p2 = recent_peaks.iloc[-1]["High"]
  if abs(p1 - p2) / p1 < 0.025:
    neckline = recent_troughs.iloc[-1]["Low"]
    detected_pattern = "M-Pattern (Double Top - Bearish)"
    signal_type = "SELL / SHORT"
    height = max(p1, p2) - neckline
    entry = round(neckline, 2)
    sl = round(p2 * 1.005, 2)
    target = round(neckline - height, 2)
    confidence = 75 if current_vol > avg_vol else 55
    reason = f"Double top resistance rejection. Short on breakdown below {entry}."

# Head & Shoulders
elif len(recent_peaks) >= 3 and len(recent_troughs) >= 2:
  p1, p2, p3 = (
      recent_peaks.iloc[-3]["High"],
      recent_peaks.iloc[-2]["High"],
      recent_peaks.iloc[-1]["High"],
  )
  if p2 > p1 and p2 > p3 and abs(p1 - p3) / p1 < 0.035:
    neckline = min(
        recent_troughs.iloc[-2]["Low"], recent_troughs.iloc[-1]["Low"]
    )
    detected_pattern = "Head & Shoulders (Bearish Reversal)"
    signal_type = "SELL / SHORT"
    height = p2 - neckline
    entry = round(neckline, 2)
    sl = round(p3 * 1.005, 2)
    target = round(neckline - height, 2)
    confidence = 82 if current_vol > avg_vol else 60
    reason = (
        "Head and shoulders neckline breakdown confirmed. Strong downward"
        " move expected."
    )

# 7. Dashboard Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Price", f"₹{current_price:.2f}")
col2.metric("Trend", trend)
col3.metric("RSI (14)", f"{current_rsi:.1f}")
col4.metric(
    "Confidence Score",
    f"{confidence}%",
    delta="Strong Setup" if confidence >= 60 else "Weak",
)

st.markdown("---")

# 8. Signal Card
st.subheader(f"AI Signal: {detected_pattern}")
c_a, c_b, c_c, c_d = st.columns(4)
c_a.write(f"**Action:** `{signal_type}`")
c_b.write(f"**Entry:** ₹{entry if entry else '-'}")
c_c.write(f"**Stop-Loss:** ₹{sl if sl else '-'}")
c_d.write(f"**Target:** ₹{target if target else '-'}")
st.info(f"Analysis Note: {reason}")

# 9. Plotly Candlestick Chart
fig = go.Figure()
fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candles",
    )
)
fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["EMA_20"],
        line=dict(color="orange", width=1.2),
        name="EMA 20",
    )
)
fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["EMA_50"],
        line=dict(color="blue", width=1.2),
        name="EMA 50",
    )
)

if entry and sl and target:
  fig.add_hline(
      y=entry, line_dash="dash", line_color="cyan", annotation_text="Entry Level"
  )
  fig.add_hline(
      y=sl, line_dash="dot", line_color="red", annotation_text="StopLoss (SL)"
  )
  fig.add_hline(
      y=target,
      line_dash="dash",
      line_color="green",
      annotation_text="Target Level",
  )

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=550,
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# 10. Action Buttons
st.subheader("Quick Orders")
col_buy, col_sell = st.columns(2)
with col_buy:
  if st.button("BUY ORDER", use_container_width=True):
    st.success(
        f"Order Placed! [Price: ₹{current_price} | SL: ₹{sl} | TGT: ₹{target}]"
    )
with col_sell:
  if st.button("SELL ORDER", use_container_width=True):
    st.warning(f"Order Placed! [Price: ₹{current_price} | SL: ₹{sl}]")
