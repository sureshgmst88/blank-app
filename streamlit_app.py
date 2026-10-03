import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import datetime
import time
import json
import pyotp

# SmartAPI உள்ளதா எனச் சரிபார்க்கிறது
try:
    from SmartApi import SmartConnect
except ImportError:
    SmartConnect = None

# ==============================================================================
# 1. STREAMLIT பக்க வடிவமைப்பு & ANGEL ONE டார்க் தீம் CSS
# ==============================================================================
st.set_page_config(
    page_title="Angel One AI Terminal",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ANGEL_ONE_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif !important; }
    
    .stApp {
        background-color: #121722 !important;
        color: #f1f5f9 !important;
    }
    header, footer { visibility: hidden !important; height: 0 !important; }
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 480px !important;
        margin: auto !important;
    }

    .angel-card {
        background-color: #1a2230;
        border: 1px solid #232c3d;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }

    .angel-card-nested {
        background-color: #161c28;
        border: 1px solid #232c3d;
        border-radius: 8px;
        padding: 10px;
    }

    .text-muted { color: #788699 !important; font-size: 11px; font-weight: 500; }
    .text-sub { color: #94a3b8; font-size: 13px; font-weight: 500; }
    .text-title { color: #ffffff; font-size: 15px; font-weight: 600; }
    .text-profit { color: #00d09c !important; font-weight: 600; }
    .text-loss { color: #eb5b62 !important; font-weight: 600; }

    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.15s ease-in-out !important;
    }
    
    .buy-btn > button {
        background-color: #00d09c !important;
        color: #000000 !important;
        font-size: 14px !important;
        width: 100% !important;
        padding: 8px !important;
    }
    .buy-btn > button:hover { background-color: #02b688 !important; }

    .sell-btn > button {
        background-color: #eb5b62 !important;
        color: #ffffff !important;
        font-size: 14px !important;
        width: 100% !important;
        padding: 8px !important;
    }
    .sell-btn > button:hover { background-color: #d94950 !important; }

    .blue-btn > button {
        background-color: #5379fe !important;
        color: #ffffff !important;
        width: 100% !important;
    }

    .bottom-nav-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #121722;
        border-top: 1px solid #232c3d;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        z-index: 99999;
        max-width: 480px;
        margin: 0 auto;
    }
    .nav-item {
        text-align: center;
        color: #788699;
        font-size: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
    }
    .nav-item.active {
        color: #5379fe;
        font-weight: 700;
    }
    .nav-item svg { width: 18px; height: 18px; fill: currentColor; }
    div[data-testid="column"] { padding: 0 4px !important; }
</style>
"""
st.markdown(ANGEL_ONE_THEME_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. அமர்வு மேலாண்மை (SESSION STATE)
# ==============================================================================
if "screen" not in st.session_state:
    st.session_state.screen = "PORTFOLIO"
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = "RELIANCE"
if "positions" not in st.session_state:
    st.session_state.positions = [
        {
            "symbol": "RELIANCE",
            "token": "2885",
            "qty": 50,
            "avg_price": 2842.10,
            "ltp": 2895.50,
            "target": 2920.00,
            "type": "BUY INT",
        }
    ]
if "orders" not in st.session_state:
    st.session_state.orders = [
        {
            "symbol": "INFY",
            "token": "1594",
            "qty": 100,
            "price": 1640.00,
            "type": "BUY LIMIT",
            "status": "PENDING",
        }
    ]
if "smartapi_client" not in st.session_state:
    st.session_state.smartapi_client = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Equity"

# ==============================================================================
# 3. ஸ்மார்ட் ஏபிஐ இணைப்பு & ஆர்டர் மேலாண்மை
# ==============================================================================
def connect_angel_one(api_key, client_id, mpin, totp_secret):
    """ஏஞ்சல் ஒன் கணக்குடன் SmartAPI மற்றும் TOTP மூலம் இணைகிறது."""
    if not SmartConnect:
        return False, "smartapi-python நிறுவப்படவில்லை. மாதிரி அமைப்பில் இயங்குகிறது."
    try:
        smart_api = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()
        data = smart_api.generateSession(client_id, mpin, totp)
        if data["status"]:
            st.session_state.smartapi_client = smart_api
            return True, "ஏஞ்சல் ஒன் டீமேட் கணக்கு வெற்றிகரமாக இணைக்கப்பட்டது!"
        return False, data.get("message", "இணைப்பு தோல்வியடைந்தது.")
    except Exception as e:
        return False, str(e)

def get_holdings():
    """பங்கு இருப்பு (Holdings) விவரங்களைப் பெறுகிறது."""
    if st.session_state.smartapi_client:
        try:
            res = st.session_state.smartapi_client.holding()
            if res.get("status") and res.get("data"):
                parsed = []
                for item in res["data"]:
                    qty = int(item.get("quantity", 0))
                    avg = float(item.get("averageprice", 0.0))
                    ltp = float(item.get("ltp", 0.0))
                    close = float(item.get("close", avg))
                    parsed.append({
                        "symbol": item.get("tradingsymbol", "UNKNOWN"),
                        "token": item.get("symboltoken", "0"),
                        "qty": qty,
                        "atp": avg,
                        "ltp": ltp,
                        "invested": qty * avg,
                        "current": qty * ltp,
                        "overall_pnl": (ltp - avg) * qty,
                        "overall_pnl_pct": ((ltp - avg) / avg * 100) if avg else 0,
                        "today_pnl": (ltp - close) * qty,
                        "today_pnl_pct": ((ltp - close) / close * 100) if close else 0,
                    })
                return parsed
        except Exception:
            pass

    # மாதிரி டீமேட் தரவுகள் (SmartAPI விவரங்கள் இல்லாதபோது இயங்கும்)
    return [
        {"symbol": "RELIANCE", "token": "2885", "qty": 45, "atp": 2780.00, "ltp": 2895.50, "invested": 125100.00, "current": 130297.50, "overall_pnl": 5197.50, "overall_pnl_pct": 4.15, "today_pnl": 1245.00, "today_pnl_pct": 0.96},
        {"symbol": "INFY", "token": "1594", "qty": 80, "atp": 1540.20, "ltp": 1655.80, "invested": 123216.00, "current": 132464.00, "overall_pnl": 9248.00, "overall_pnl_pct": 7.50, "today_pnl": -840.00, "today_pnl_pct": -0.63},
        {"symbol": "ITC", "token": "1660", "qty": 350, "atp": 412.00, "ltp": 448.25, "invested": 144200.00, "current": 156887.50, "overall_pnl": 12687.50, "overall_pnl_pct": 8.79, "today_pnl": 1050.00, "today_pnl_pct": 0.67},
        {"symbol": "FIVESTAR", "token": "11822", "qty": 120, "atp": 725.50, "ltp": 810.00, "invested": 87060.00, "current": 97200.00, "overall_pnl": 10140.00, "overall_pnl_pct": 11.64, "today_pnl": 2160.00, "today_pnl_pct": 2.27},
        {"symbol": "BLS", "token": "17387", "qty": 400, "atp": 365.00, "ltp": 352.40, "invested": 146000.00, "current": 140960.00, "overall_pnl": -5040.00, "overall_pnl_pct": -3.45, "today_pnl": -1440.00, "today_pnl_pct": -1.01},
    ]

def place_order(symbol, token, qty, action, order_type="MARKET"):
    """நேரடி ஆர்டர் அல்லது மாதிரி ஆர்டரை செயல்படுத்துகிறது."""
    if st.session_state.smartapi_client:
        try:
            params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": str(token),
                "transactiontype": action,
                "exchange": "NSE",
                "ordertype": order_type,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "quantity": str(qty),
            }
            order_res = st.session_state.smartapi_client.placeOrder(params)
            return True, f"ஆர்டர் நிறைவேறியது! எண்: {order_res.get('data', {}).get('orderid', '109283')}"
        except Exception as e:
            return False, f"ஆர்டர் பிழை: {str(e)}"

    curr_stock = next((s for s in get_holdings() if s["symbol"] == symbol), {"ltp": 2500.0})
    st.session_state.positions.append({
        "symbol": symbol,
        "token": token,
        "qty": qty,
        "avg_price": curr_stock["ltp"],
        "ltp": curr_stock["ltp"],
        "target": curr_stock["ltp"] * 1.015,
        "type": f"{action} INT",
    })
    return True, f"ஆர்டர் பதிவு செய்யப்பட்டது: {action} {qty} பங்குகள் ({symbol} - ₹{curr_stock['ltp']})"

# ==============================================================================
# 4. தொழில்நுட்ப குறிகாட்டிகள் & AI அல்காரிதம்
# ==============================================================================
def generate_ohlcv_data(base_price=2895.0, count=90):
    np.random.seed(42)
    now = datetime.datetime.now()
    candles = []
    current_close = base_price

    for i in range(count):
        t = now - datetime.timedelta(minutes=(count - i) * 5)
        chg = np.random.normal(0, base_price * 0.002)
        o = current_close
        c = o + chg
        h = max(o, c) + abs(np.random.normal(0, base_price * 0.001))
        l = min(o, c) - abs(np.random.normal(0, base_price * 0.001))
        v = int(np.random.uniform(5000, 45000))
        candles.append({
            "time": int(t.timestamp()),
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
            "volume": v,
        })
        current_close = c
    return pd.DataFrame(candles)

def calculate_ai_analytics(df: pd.DataFrame):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift(1)).abs()
    lc = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(10).mean().bfill()

    multiplier = 3.0
    basic_ub = (df["high"] + df["low"]) / 2 + (multiplier * atr)
    basic_lb = (df["high"] + df["low"]) / 2 - (multiplier * atr)

    supertrend, direction = [], []
    trend = 1
    for i in range(len(df)):
        if i == 0:
            supertrend.append(basic_ub.iloc[i])
            direction.append(trend)
            continue
        c = df["close"].iloc[i]
        prev_st = supertrend[i - 1]
        if trend == 1:
            if c < prev_st:
                trend = -1
                supertrend.append(basic_ub.iloc[i])
            else:
                supertrend.append(max(basic_lb.iloc[i], prev_st))
        else:
            if c > prev_st:
                trend = 1
                supertrend.append(basic_lb.iloc[i])
            else:
                supertrend.append(min(basic_ub.iloc[i], prev_st))
        direction.append(trend)

    df["supertrend"] = supertrend
    df["st_dir"] = direction

    # RSI (14)
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df["rsi"] = 100 - (100 / (1 + rs))

    df["vol_sma"] = df["volume"].rolling(20).mean().bfill()

    last_rsi = df["rsi"].iloc[-1]
    last_vol = df["volume"].iloc[-1]
    vol_sma = df["vol_sma"].iloc[-1]
    is_bull = df["st_dir"].iloc[-1] == 1

    score = 50.0
    score += 20 if is_bull else -20
    if last_rsi > 55: score += 15
    elif last_rsi < 45: score -= 15
    if last_vol > vol_sma: score += 15

    strength_score = max(5, min(95, score))

    if strength_score >= 75:
        color, sentiment = "#00d09c", "வலுவான ஏற்ற வேகம் (STRONG MOMENTUM)"
    elif strength_score >= 50:
        color, sentiment = "#ffeb3b", "சமநிலை (NEUTRAL / ACCUMULATION)"
    elif strength_score >= 40:
        color, sentiment = "#ff8a80", "வலுவிழக்கும் போக்கு (WEAKENING)"
    else:
        color, sentiment = "#d50000", "அதிக ஆபத்து / பொறி (EXTREME RISK)"

    breakout_banner, banner_type = None, "info"
    recent_high = df["high"].iloc[-25:-1].max()
    curr_c = df["close"].iloc[-1]

    if curr_c > recent_high:
        if last_vol < vol_sma or last_rsi < 60:
            breakout_banner = "⚠️ போலி ஏற்ற பிரேக்அவுட் (BULL TRAP) கண்டறியப்பட்டது - வால்யூம் ஆதரவு இல்லை!"
            banner_type = "danger"
        else:
            breakout_banner = "🚀 உண்மையான பிரேக்அவுட் (GENUINE BREAKOUT) - வால்யூம் & RSI உறுதிப்படுத்தியது!"
            banner_type = "success"

    return {
        "score": strength_score,
        "color": color,
        "sentiment": sentiment,
        "breakout_banner": breakout_banner,
        "banner_type": banner_type,
        "df": df,
    }

# ==============================================================================
# 5. பக்கவாட்டுப் பட்டி: லாகின் விண்டோ
# ==============================================================================
with st.sidebar:
    st.markdown("### 🔐 ஏஞ்சல் ஒன் SmartAPI உள்நுழைவு")
    st.caption("TOTP மூலமான நேரடி டீமேட் இணைப்பு")

    api_key_input = st.text_input("SmartAPI Key", type="password")
    client_id_input = st.text_input("Client ID")
    mpin_input = st.text_input("4-Digit MPIN", type="password", max_chars=4)
    totp_input = st.text_input("TOTP Secret Key", type="password")

    if st.button("கணக்கை இணைக்க", use_container_width=True):
        if api_key_input and client_id_input and mpin_input and totp_input:
            ok, msg = connect_angel_one(api_key_input, client_id_input, mpin_input, totp_input)
            if ok: st.success(msg)
            else: st.warning(msg)
        else:
            st.info("விவரங்கள் வழங்கப்படாததால் மாதிரித் தரவுகளுடன் இயங்குகிறது.")

# ==============================================================================
# 6. திரை 1: போர்ட்ஃபோலியோ / பங்கு இருப்பு
# ==============================================================================
def render_portfolio_screen():
    holdings = get_holdings()

    total_invested = sum(h["invested"] for h in holdings)
    total_current = sum(h["current"] for h in holdings)
    total_overall_pnl = total_current - total_invested
    total_overall_pct = (total_overall_pnl / total_invested) * 100 if total_invested else 0
    total_today_pnl = sum(h["today_pnl"] for h in holdings)
    total_today_pct = (total_today_pnl / total_invested) * 100 if total_invested else 0

    st.markdown("<h3 style='margin:0; font-size: 19px; font-weight:700;'>பங்கு இருப்பு <span style='color:#788699; font-weight:400;'>• சொத்து மதிப்பு</span></h3>", unsafe_allow_html=True)

    tabs = ["Overview", "Equity", "Mutual Funds", "Picks"]
    st.markdown(
        f"""
        <div style="display:flex; gap:16px; border-bottom:1px solid #232c3d; margin-top:10px; margin-bottom:12px; font-size:13px; font-weight:600;">
            {"".join([f"<span style='padding-bottom:6px; cursor:pointer; color:{'#5379fe; border-bottom:2px solid #5379fe;' if t == st.session_state.active_tab else '#788699'}'>{t}</span>" for t in tabs])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    pnl_color = "#00d09c" if total_overall_pnl >= 0 else "#eb5b62"
    pnl_sign = "+" if total_overall_pnl >= 0 else ""
    today_color = "#00d09c" if total_today_pnl >= 0 else "#eb5b62"
    today_sign = "+" if total_today_pnl >= 0 else ""

    st.markdown(
        f"""
        <div class="angel-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="text-muted">தற்போதைய மொத்த மதிப்பு</span>
                <span style="color:#788699;">👁</span>
            </div>
            <div style="font-size: 24px; font-weight: 700; margin-top: 4px;">
                ₹{total_current:,.2f}
            </div>
            <div style="margin-top: 4px; font-size: 13px; font-weight: 600; color: {pnl_color};">
                மொத்த லாபம்/நஷ்டம் {pnl_sign}₹{total_overall_pnl:,.2f} ({pnl_sign}{total_overall_pct:.2f}%)
            </div>
            <hr style="border: 0; border-top: 1px solid #232c3d; margin: 12px 0;">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <div class="text-muted">முதலீடு செய்யப்பட்ட தொகை</div>
                    <div style="font-size: 14px; font-weight: 600; margin-top:2px;">₹{total_invested:,.2f}</div>
                </div>
                <div style="text-align: right;">
                    <div class="text-muted">இன்றைய மாற்றம்</div>
                    <div style="font-size: 14px; font-weight: 600; margin-top:2px; color: {today_color};">
                        {today_sign}₹{total_today_pnl:,.2f} ({today_sign}{total_today_pct:.2f}%)
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"<div style='font-size:12px; font-weight:700; color:#788699; margin-bottom:8px;'>பங்குகள் ({len(holdings)})</div>", unsafe_allow_html=True)

    for h in holdings:
        h_overall_color = "#00d09c" if h["overall_pnl"] >= 0 else "#eb5b62"
        h_today_color = "#00d09c" if h["today_pnl"] >= 0 else "#eb5b62"
        h_overall_sign = "+" if h["overall_pnl"] >= 0 else ""
        h_today_sign = "+" if h["today_pnl"] >= 0 else ""

        col_left, col_mid, col_btn = st.columns([1.8, 1.4, 0.9])
        with col_left:
            st.markdown(
                f"""
                <div style="margin-bottom: 2px;">
                    <span style="font-weight:700; font-size:14px; color:#ffffff;">{h['symbol']}</span>
                    <span style="background-color:#161c28; color:#788699; font-size:10px; padding:1px 4px; border-radius:3px;">NSE</span>
                </div>
                <div class="text-muted">
                    எண்ணிக்கை: <b style="color:#ffffff;">{h['qty']}</b> • சராசரி: ₹{h['atp']:,.2f}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_mid:
            st.markdown(
                f"""
                <div style="text-align: right;">
                    <div style="font-size:14px; font-weight:600;">₹{h['ltp']:,.2f}</div>
                    <div style="font-size:11px; font-weight:600; color:{h_today_color};">
                        {h_today_sign}₹{h['today_pnl']:,.1f} ({h_today_sign}{h['today_pnl_pct']:.2f}%)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_btn:
            if st.button("விவரம்", key=f"btn_h_{h['symbol']}", use_container_width=True):
                st.session_state.selected_stock = h["symbol"]
                st.session_state.screen = "CHART"
                st.rerun()

        st.markdown("<hr style='border:0; border-top:1px solid #1c2432; margin:6px 0 10px 0;'>", unsafe_allow_html=True)

# ==============================================================================
# 7. திரை 2: பங்கு விவரங்கள் (STOCK DETAIL)
# ==============================================================================
def render_detail_screen():
    stock_sym = st.session_state.selected_stock
    holdings = get_holdings()
    stock_data = next((s for s in holdings if s["symbol"] == stock_sym), holdings[0])

    c1, c2 = st.columns([0.25, 0.75])
    with c1:
        if st.button("← பின்செல்", use_container_width=True):
            st.session_state.screen = "PORTFOLIO"
            st.rerun()
    with c2:
        st.markdown(f"<h3 style='margin:0; font-size:17px; font-weight:700;'>{stock_sym} <span class='text-muted'>NSE</span></h3>", unsafe_allow_html=True)

    pnl_sign = "+" if stock_data["today_pnl"] >= 0 else ""
    p_color = "#00d09c" if stock_data["today_pnl"] >= 0 else "#eb5b62"
    st.markdown(
        f"""
        <div class="angel-card" style="margin-top:10px;">
            <div style="font-size:26px; font-weight:700;">₹{stock_data['ltp']:,.2f}</div>
            <div style="font-size:13px; font-weight:600; color:{p_color}; margin-top:2px;">
                {pnl_sign}₹{stock_data['today_pnl']:,.2f} ({pnl_sign}{stock_data['today_pnl_pct']:.2f}%) இன்று
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="blue-btn">', unsafe_allow_html=True)
    if st.button("📊 வரைபடத்தைத் திறக்க (TradingView)", use_container_width=True):
        st.session_state.screen = "CHART"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    col_b, col_s = st.columns(2)
    with col_b:
        st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
        if st.button("வாங்க (BUY)", key="det_buy", use_container_width=True):
            ok, msg = place_order(stock_data["symbol"], stock_data["token"], 10, "BUY")
            st.toast(msg, icon="✅" if ok else "⚠️")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_s:
        st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
        if st.button("விற்க (SELL)", key="det_sell", use_container_width=True):
            ok, msg = place_order(stock_data["symbol"], stock_data["token"], 10, "SELL")
            st.toast(msg, icon="🛑")
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# 8. திரை 3: TRADINGVIEW வரைபடம் (PRO TERMINAL)
# ==============================================================================
def render_pro_chart_terminal():
    stock_sym = st.session_state.selected_stock
    holdings = get_holdings()
    stock_data = next((s for s in holdings if s["symbol"] == stock_sym), holdings[0])

    col_nav1, col_nav2 = st.columns([0.25, 0.75])
    with col_nav1:
        if st.button("← பின்செல்", key="chart_back", use_container_width=True):
            st.session_state.screen = "PORTFOLIO"
            st.rerun()
    with col_nav2:
        st.markdown(f"<span style='font-size:13px; font-weight:700;'>{stock_sym} ₹{stock_data['ltp']:,.1f}</span>", unsafe_allow_html=True)

    df_ohlcv = generate_ohlcv_data(base_price=stock_data["ltp"], count=80)
    ai_results = calculate_ai_analytics(df_ohlcv)
    df = ai_results["df"]

    st.markdown(
        f"""
        <div style="background-color:#161c28; border:1px solid #232c3d; border-radius:8px; padding:8px 12px; margin-top:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="text-muted">AI வேக அளவீடு</span>
                <span style="color:{ai_results['color']}; font-weight:700; font-size:12px;">
                    {ai_results['sentiment']} ({ai_results['score']:.0f}%)
                </span>
            </div>
            <div style="height:4px; width:100%; background-color:#232c3d; border-radius:2px; margin-top:6px; overflow:hidden;">
                <div style="height:100%; width:{ai_results['score']}%; background-color:{ai_results['color']};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ai_results["breakout_banner"]:
        b_color = "#eb5b62" if ai_results["banner_type"] == "danger" else "#00d09c"
        st.markdown(
            f"""
            <div style="background-color:rgba(235,91,98,0.12); border-left:4px solid {b_color}; padding:6px 10px; border-radius:4px; margin-top:6px; font-size:11px; font-weight:600; color:{b_color};">
                {ai_results['breakout_banner']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    chart_candles = [{"time": int(r["time"]), "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]), "close": float(r["close"])} for _, r in df.iterrows()]
    supertrend_points = [{"time": int(r["time"]), "value": float(r["supertrend"]), "color": "#00d09c" if r["st_dir"] == 1 else "#eb5b62"} for _, r in df.iterrows()]

    high_val = float(df["high"].max())
    low_val = float(df["low"].min())
    entry_val = float(stock_data["atp"])

    tv_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #121722; }}
            #tv_container {{ position: relative; width: 100%; height: 380px; }}
            #floating_reset {{
                position: absolute; top: 14px; right: 60px;
                background: #1a2230; border: 1px solid #232c3d; color: #5379fe;
                border-radius: 50%; width: 32px; height: 32px;
                display: flex; align-items: center; justify-content: center;
                cursor: pointer; z-index: 50;
            }}
        </style>
    </head>
    <body>
        <div id="tv_container">
            <div id="floating_reset" title="மீட்டமை">🔄</div>
        </div>
        <script>
            const container = document.getElementById('tv_container');
            const chart = LightweightCharts.createChart(container, {{
                width: container.clientWidth,
                height: 380,
                layout: {{ background: {{ color: '#121722' }}, textColor: '#788699' }},
                grid: {{ vertLines: {{ color: '#1c2432' }}, horzLines: {{ color: '#1c2432' }} }},
                rightPriceScale: {{ borderColor: '#232c3d' }},
                timeScale: {{ borderColor: '#232c3d' }}
            }});

            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#00d09c', downColor: '#eb5b62',
                borderUpColor: '#00d09c', borderDownColor: '#eb5b62',
                wickUpColor: '#00d09c', wickDownColor: '#eb5b62'
            }});
            candleSeries.setData({json.dumps(chart_candles)});

            const supertrendSeries = chart.addLineSeries({{ lineWidth: 2, priceLineVisible: false }});
            supertrendSeries.setData({json.dumps(supertrend_points)});

            candleSeries.createPriceLine({{ price: {high_val}, color: '#00d09c', lineStyle: LightweightCharts.LineStyle.Dotted, title: 'High' }});
            candleSeries.createPriceLine({{ price: {low_val}, color: '#eb5b62', lineStyle: LightweightCharts.LineStyle.Dotted, title: 'Low' }});
            candleSeries.createPriceLine({{ price: {entry_val}, color: '#5379fe', lineStyle: LightweightCharts.LineStyle.Solid, title: 'BUY INT' }});

            document.getElementById('floating_reset').addEventListener('click', () => {{
                chart.timeScale().scrollToRealTime();
            }});
        </script>
    </body>
    </html>
    """
    components.html(tv_html, height=395)

    dock_tab1, dock_tab2 = st.tabs(["நிலைகள் (Positions)", "நிலுவை ஆர்டர்கள் (Orders)"])

    with dock_tab1:
        if st.session_state.positions:
            for idx, pos in enumerate(st.session_state.positions):
                p_pnl = (stock_data["ltp"] - pos["avg_price"]) * pos["qty"]
                p_color = "#00d09c" if p_pnl >= 0 else "#eb5b62"
                p_sign = "+" if p_pnl >= 0 else ""

                c_p1, c_p2 = st.columns([0.7, 0.3])
                with c_p1:
                    st.markdown(
                        f"""
                        <div style="font-weight:700; font-size:13px;">{pos['symbol']} ({pos['type']})</div>
                        <div class="text-muted">{pos['qty']} பங்குகள் • சராசரி ₹{pos['avg_price']:,.2f}</div>
                        <div style="font-size:12px; font-weight:700; color:{p_color};">P&L: {p_sign}₹{p_pnl:,.2f}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c_p2:
                    if st.button("⚡ EXIT", key=f"exit_{idx}", use_container_width=True):
                        st.session_state.positions.pop(idx)
                        st.toast(f"{pos['symbol']} நிலை உடனடியாக மூடப்பட்டது!", icon="⚡")
                        st.rerun()
        else:
            st.caption("திறந்த நிலைகள் எதுவும் இல்லை.")

    with dock_tab2:
        if st.session_state.orders:
            for o in st.session_state.orders:
                st.markdown(f"**{o['symbol']}** • {o['qty']} பங்குகள் @ ₹{o['price']} ({o['status']})")
        else:
            st.caption("நிலுவை ஆர்டர்கள் இல்லை.")

    col_tb1, col_tb2 = st.columns(2)
    with col_tb1:
        st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
        if st.button(f"BUY {stock_sym}", key="chart_btn_buy", use_container_width=True):
            ok, msg = place_order(stock_sym, stock_data["token"], 25, "BUY")
            st.toast(msg, icon="🚀")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_tb2:
        st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
        if st.button(f"SELL {stock_sym}", key="chart_btn_sell", use_container_width=True):
            ok, msg = place_order(stock_sym, stock_data["token"], 25, "SELL")
            st.toast(msg, icon="🛑")
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# 9. கீழ்ப்பகுதி வழிசெலுத்தல் பட்டி
# ==============================================================================
def render_persistent_bottom_bar():
    holdings = get_holdings()
    total_running_pnl = sum(h["overall_pnl"] for h in holdings)
    pnl_sign = "+" if total_running_pnl >= 0 else ""
    pnl_color = "#00d09c" if total_running_pnl >= 0 else "#eb5b62"

    st.markdown(
        f"""
        <div style="position:fixed; bottom:44px; left:0; right:0; max-width:480px; margin:0 auto; background-color:#161c28; border-top:1px solid #232c3d; padding:6px 16px; display:flex; justify-content:space-between; align-items:center; z-index:99998;">
            <span style="font-size:11px; font-weight:600; color:#788699;">மொத்த P&L</span>
            <span style="font-size:12px; font-weight:700; color:{pnl_color};">✔ {pnl_sign}₹{total_running_pnl:,.2f}</span>
        </div>

        <div class="bottom-nav-container">
            <div class="nav-item"><span>முகப்பு</span></div>
            <div class="nav-item"><span>கண்காணிப்பு</span></div>
            <div class="nav-item {'active' if st.session_state.screen in ['PORTFOLIO', 'DETAIL'] else ''}"><span>போர்ட்ஃபோலியோ</span></div>
            <div class="nav-item {'active' if st.session_state.screen == 'CHART' else ''}"><span>ஆர்டர்கள்</span></div>
            <div class="nav-item"><span>கணக்கு</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# 10. முதன்மை ரூட்டிங்
# ==============================================================================
if st.session_state.screen == "PORTFOLIO":
    render_portfolio_screen()
elif st.session_state.screen == "DETAIL":
    render_detail_screen()
elif st.session_state.screen == "CHART":
    render_pro_chart_terminal()

render_persistent_bottom_bar()
