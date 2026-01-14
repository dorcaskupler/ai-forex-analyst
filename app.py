import openai
import streamlit as st

st.write("OpenAI library version:", openai.__version__)

import streamlit as st
import json
import os
import hashlib
from PIL import Image, ImageDraw
from openai import OpenAI

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Forex Analyst", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

USERS_FILE = "users.json"
HISTORY_DIR = "trade_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# ---------------- AUTH UTILS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def save_trade(username, trade):
    path = f"{HISTORY_DIR}/{username}.json"
    history = []
    if os.path.exists(path):
        with open(path, "r") as f:
            history = json.load(f)
    history.append(trade)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)

def load_trade_history(username):
    path = f"{HISTORY_DIR}/{username}.json"
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 User Access")
users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    mode = st.sidebar.radio("Choose", ["Login", "Register"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if mode == "Register" and st.sidebar.button("Create Account"):
        if username in users:
            st.sidebar.error("Username already exists")
        else:
            users[username] = hash_password(password)
            save_users(users)
            st.sidebar.success("Account created. Please login.")

    if mode == "Login" and st.sidebar.button("Login"):
        if users.get(username) == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")

    st.stop()

# ---------------- MAIN APP ----------------
st.title("📈 AI Multi-Timeframe Forex Trading Analyst")

style = st.selectbox("Trading Style", ["Day Trading", "Swing Trading"])

tools = st.multiselect(
    "Analysis Tools",
    ["Support & Resistance", "Moving Averages", "Market Structure"],
    default=["Support & Resistance"]
)

st.divider()
st.subheader("📤 Upload TradingView Chart Screenshots")

c1, c2, c3 = st.columns(3)
with c1:
    htf = st.file_uploader("4H Chart", type=["png", "jpg"])
with c2:
    mtf = st.file_uploader("1H Chart", type=["png", "jpg"])
with c3:
    ltf = st.file_uploader("15m Chart", type=["png", "jpg"])

# ---------------- DRAWING ----------------
def draw_horizontal(image, levels, color):
    img = image.copy()
    d = ImageDraw.Draw(img)
    w, h = img.size
    for lvl in levels:
        y = int(h * lvl)
        d.line([(0, y), (w, y)], fill=color, width=3)
    return img

def draw_trendline(image, start, end, color):
    img = image.copy()
    d = ImageDraw.Draw(img)
    w, h = img.size
    d.line(
        [(int(start[0]*w), int(start[1]*h)), (int(end[0]*w), int(end[1]*h))],
        fill=color,
        width=3
    )
    return img

def draw_ma(image, points, color):
    img = image.copy()
    d = ImageDraw.Draw(img)
    w, h = img.size
    pts = [(int(x*w), int(y*h)) for x, y in points]
    d.line(pts, fill=color, width=3)
    return img

# ---------------- ANALYSIS ----------------
if st.button("🔍 Analyze Market", use_container_width=True):
    if not (htf and mtf and ltf):
        st.error("Please upload all three charts.")
        st.stop()

    img_4h = Image.open(htf)
    img_1h = Image.open(mtf)
    img_15m = Image.open(ltf)

    prompt = f"""
You are a professional forex trader.

Trading style: {style}
Tools: {tools}

Analyze:
- 4H: trend bias
- 1H: structure, support/resistance, MA, trendline
- 15m: entry, stop loss, take profit

Respond ONLY in valid JSON:

{{
  "bias": "bullish | bearish | range",
  "support_resistance": [0.3, 0.6],
  "moving_average": {{
    "type": "EMA 50",
    "line": [[0.1, 0.55], [0.9, 0.45]]
  }},
  "trendline": {{
    "start": [0.1, 0.6],
    "end": [0.9, 0.4]
  }},
  "entry_sl_tp": {{
    "entry": 0.48,
    "stop_loss": 0.55,
    "take_profit": 0.35
  }},
  "confidence_score": 80,
  "explanation": "HTF trend aligns with structure and entry confirmation."
}}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    try:
        ai = json.loads(res.choices[0].message.content)
    except json.JSONDecodeError:
        st.error("AI response could not be parsed. Retry.")
        st.stop()

    save_trade(
        st.session_state.user,
        {
            "bias": ai["bias"],
            "entry": ai["entry_sl_tp"]["entry"],
            "stop_loss": ai["entry_sl_tp"]["stop_loss"],
            "take_profit": ai["entry_sl_tp"]["take_profit"],
            "confidence": ai["confidence_score"]
        }
    )

    st.metric("Market Bias", ai["bias"].upper())
    st.metric("Trade Confidence", f"{ai['confidence_score']}%")
    st.write(ai["explanation"])

    if "Support & Resistance" in tools:
        img_4h = draw_horizontal(img_4h, ai["support_resistance"], "blue")
        img_1h = draw_horizontal(img_1h, ai["support_resistance"], "orange")

    if "Moving Averages" in tools:
        img_1h = draw_ma(img_1h, ai["moving_average"]["line"], "purple")

    if "Market Structure" in tools:
        img_1h = draw_trendline(
            img_1h,
            ai["trendline"]["start"],
            ai["trendline"]["end"],
            "red"
        )

    img_15m = draw_horizontal(
        img_15m,
        [
            ai["entry_sl_tp"]["entry"],
            ai["entry_sl_tp"]["stop_loss"],
            ai["entry_sl_tp"]["take_profit"]
        ],
        "green"
    )

    img_15m.save("trade_setup.png")

    st.divider()
    st.subheader("📊 Annotated Charts")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.image(img_4h, use_container_width=True)
    with c2:
        st.image(img_1h, use_container_width=True)
    with c3:
        st.image(img_15m, use_container_width=True)

    with open("trade_setup.png", "rb") as f:
        st.download_button(
            "📥 Download Trade Setup",
            f,
            file_name="AI_Forex_Trade.png"
        )

# ---------------- HISTORY ----------------
st.sidebar.divider()
st.sidebar.subheader("📜 Trade History")

history = load_trade_history(st.session_state.user)
if history:
    for trade in reversed(history[-5:]):
        st.sidebar.markdown(
            f"""
            **Bias:** {trade['bias']}  
            Entry: {trade['entry']}  
            SL: {trade['stop_loss']}  
            TP: {trade['take_profit']}  
            Confidence: {trade['confidence']}%
            """
        )
else:
    st.sidebar.info("No trades yet.")
