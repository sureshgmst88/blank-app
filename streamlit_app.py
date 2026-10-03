import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import json

st.set_page_config(page_title="Angel One Pro TradingView", layout="wide", initial_sidebar_state="collapsed")

# Precise Angel One Mobile Layout CSS
st.markdown("""
<style>
    .stApp {
        background-color: #121722 !important;
        color: #f0f3f8 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header, footer { visibility: hidden; }
    .block-container { padding: 0.2rem 0.4rem 4.5rem 0.4rem; }

    /* Top Watchlist Ticker Tabs */
    .ticker-bar {
        display: flex;
        overflow-x: auto;
        gap: 8px;
        background: #161c28;
        padding: 6px 10px;
        border-bottom: 1px solid #232c3d;
        white-space: nowrap;
    }
    .ticker-pill {
        border: 1px solid #2d3b52;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        background: #1a2230;
    }

    /* Fixed Bottom Action Dock */
    .action-dock {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #161c28;
        border-top: 1px solid #232c3d;
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 1000;
    }
    .btn-buy {
        background-color: #00d09c;
        color: #121722;
        font-weight: bold;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
        width: 48%;
        border: none;
    }
    .btn-sell {
        background-color: #eb5b62;
        color: #ffffff;
        font-weight: bold;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
        width: 48%;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# 1. Top Ticker Watchlist Bar
st.markdown("""
<div class="ticker-bar">
    <span class="ticker-pill" style="border-color:#5379fe; color:#00d09c;">ITC 255.90 (-2.61%) ✕</span>
    <span class="ticker-pill" style="color:#eb5b62;">FIVESTAR 506.25 ✕</span>
    <span class="ticker-pill" style="color:#00d09c;">TEJASNET 497.00 ✕</span>
    <span class="ticker-pill">BLS 280.15 ✕</span>
</div>
""", unsafe_allow_html=True)

# 2. Controls: Stock & Timeframe Selection
col1, col2 = st.columns([1.5, 3.5])
with col1:
    sym = st.selectbox("Stock", ["ITC.NS", "TEJASNET.NS", "BLS.NS", "DRREDDY.NS"], index=0, label_visibility="collapsed")
with col2:
    tf = st.radio("TF", ["1m", "5m", "15m", "1h", "1D"], horizontal=True, index=2, label_visibility="collapsed")

tf_map = {
    "1m": ("1d", "1m"),
    "5m": ("5d", "5m"),
    "15m": ("1mo", "15m"),
    "1h": ("1mo", "60m"),
    "1D": ("1y", "1d")
}
prd, itv = tf_map[tf]

# 3. Data Fetching & Technical Indicators
@st.cache_data(ttl=60)
def get_chart_data(symbol, period, interval):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna().reset_index()
    time_col = df.columns[0]
    df['time'] = (df[time_col].astype('int64') // 10**9)
    return df

df = get_chart_data(sym, prd, itv)

# Candlestick Array
candle_data = []
for _, row in df.iterrows():
    candle_data.append({
        "time": int(row['time']),
        "open": float(row['Open']),
        "high": float(row['High']),
        "low": float(row['Low']),
        "close": float(row['Close'])
    })

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
st_data = []
for _, row in df.iterrows():
    st_data.append({
        "time": int(row['time']),
        "value": float(row['SuperTrend'])
    })

candles_json = json.dumps(candle_data)
st_json = json.dumps(st_data)

curr_ltp = candle_data[-1]['close'] if candle_data else 255.90
buy_price = round(curr_ltp * 0.99, 2)
target_price = round(curr_ltp * 1.02, 2)
st_last_val = round(float(df['SuperTrend'].iloc[-1]), 2)
is_bullish = st_dir[-1]
st_color = "#00d09c" if is_bullish else "#eb5b62"

# 4. Embedded TradingView Lightweight Chart with Native Real-time Jump (🔄)
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background-color: #121722; overflow: hidden; }}
        #tv_chart {{ width: 100vw; height: 520px; position: relative; }}
        
        /* Floating Reset / Real-time Jump Button */
        #reset_btn {{
            position: absolute;
            bottom: 35px;
            right: 80px;
            width: 34px;
            height: 34px;
            background: #1c2432;
            border: 1px solid #2d3b52;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 100;
            color: #788699;
            font-size: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            user-select: none;
        }}
        #reset_btn:active {{
            background: #2a3649;
            color: #ffffff;
            transform: scale(0.92);
        }}
    </style>
</head>
<body>
    <div id="tv_chart">
        <div id="reset_btn" title="Scroll to Real-time">🔄</div>
    </div>
    <script>
        const chart = LightweightCharts.createChart(document.getElementById('tv_chart'), {{
            width: window.innerWidth,
            height: 520,
            layout: {{
                backgroundColor: '#121722',
                textColor: '#788699',
            }},
            grid: {{
                vertLines: {{ color: '#1a2230' }},
                horzLines: {{ color: '#1a2230' }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
            }},
            rightPriceScale: {{
                borderColor: '#232c3d',
                scaleMargins: {{ top: 0.1, bottom: 0.15 }},
                autoScale: true,
            }},
            timeScale: {{
                borderColor: '#232c3d',
                timeVisible: true,
                secondsVisible: false,
                shiftVisibleRangeOnNewBar: true,
            }},
            handleScroll: {{ vertTouchDrag: true }},
            handleScale: {{
                axisPressedMouseMove: {{
                    time: true,
                    price: true,
                }},
            }},
        }});

        // Candlestick Series
        const candleSeries = chart.addCandlestickSeries({{
            upColor: '#00d09c',
            downColor: '#eb5b62',
            borderUpColor: '#00d09c',
            borderDownColor: '#eb5b62',
            wickUpColor: '#00d09c',
            wickDownColor: '#eb5b62',
        }});
        candleSeries.setData({candles_json});

        // SuperTrend Overlay Line Series
        const stLineSeries = chart.addLineSeries({{
            color: '{st_color}',
            lineWidth: 2,
            title: 'SuperTrend',
            priceLineVisible: true,
        }});
        stLineSeries.setData({st_json});

        // 1. SuperTrend Price Label on the Right Scale
        stLineSeries.createPriceLine({{
            price: {st_last_val},
            color: '{st_color}',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: 'SuperTrend',
        }});

        // 2. Buy Entry Price Line & Label
        candleSeries.createPriceLine({{
            price: {buy_price},
            color: '#00d09c',
            lineWidth: 1.5,
            lineStyle: LightweightCharts.LineStyle.Solid,
            axisLabelVisible: true,
            title: 'BUY INT | 1,000',
        }});

        // 3. Sell Target Price Line & Label
        candleSeries.createPriceLine({{
            price: {target_price},
            color: '#eb5b62',
            lineWidth: 1.5,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            axisLabelVisible: true,
            title: 'TARGET EXIT',
        }});

        // 🔄 Reset / Scroll to Most Recent Real-Time Bar
        document.getElementById('reset_btn').addEventListener('click', () => {{
            chart.timeScale().scrollToRealTime();
            chart.priceScale('right').applyOptions({{ autoScale: true }});
        }});

        // Initial Real-time view
        chart.timeScale().scrollToRealTime();

        window.addEventListener('resize', () => {{
            chart.applyOptions({{ width: window.innerWidth }});
        }});
    </script>
</body>
</html>
"""

components.html(html_code, height=530)

# 5. Fixed Mobile Bottom Buttons (Angel One Style)
st.markdown(f"""
<div class="action-dock">
    <button class="btn-buy">BUY @ ₹{curr_ltp:.2f}</button>
    <button class="btn-sell">SELL @ ₹{curr_ltp:.2f}</button>
</div>
""", unsafe_allow_html=True)
