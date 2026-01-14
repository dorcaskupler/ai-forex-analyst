import streamlit as st
import tempfile
import openai

# ---------- CONFIG ----------
st.set_page_config(
    page_title="AI Forex Analyst",
    layout="wide",
    page_icon="📊"
)

openai.api_key = st.secrets["My Teest Key"]

# ---------- HEADER ----------
st.markdown("""
# 📊 AI Forex Chart Analyst
Institutional-style technical analysis powered by AI  
*Probability-based insights · No financial advice*
""")

st.divider()

# ---------- SIDEBAR ----------
st.sidebar.header("🔧 Analysis Settings")

trading_style = st.sidebar.selectbox(
    "Trading Style",
    ["Scalping", "Day Trading", "Swing Trading", "Position Trading"]
)

bias_tf = st.sidebar.selectbox(
    "Bias Timeframe",
    ["15m", "1H", "4H", "1D", "1W"]
)

entry_tf = st.sidebar.selectbox(
    "Entry Timeframe",
    ["1m", "5m", "15m", "30m", "1H"]
)

risk_model = st.sidebar.selectbox(
    "Risk Model",
    ["Conservative", "Balanced", "Aggressive"]
)

st.sidebar.info(
    "Upload a **TradingView chart screenshot**.\n\n"
    "Make sure price levels & timeframe are visible."
)

# ---------- ANALYSIS FUNCTION ----------
def analyze_chart(image_path):
    prompt = f"""
You are a professional institutional forex technical analyst.

Analyze the uploaded TradingView chart using smart money concepts.

Context:
- Trading style: {trading_style}
- Bias timeframe: {bias_tf}
- Entry timeframe: {entry_tf}
- Risk model: {risk_model}

Provide a structured analysis with the following sections:

1. Market Structure
2. Directional Bias (Buy / Sell / Neutral)
3. Key Support & Resistance
4. Liquidity & Inducement
5. Trade Setup (if valid):
   - Entry Zone
   - Stop Loss
   - Take Profit Targets (TP1, TP2 if applicable)
   - Risk-to-Reward Estimate
6. Invalidation Conditions
7. Risk Notes

Rules:
- Price levels must be realistic and chart-based
- Use zones, not exact pip precision
- Probability-based only
- NO financial advice
- If no valid setup, clearly say "No high-probability setup"
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a forex chart AI analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.35
    )

    return response.choices[0].message.content

# ---------- MAIN CONTENT ----------
col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📤 Upload Chart")
    uploaded_file = st.file_uploader(
        "TradingView Screenshot (PNG / JPG)",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:
        st.image(uploaded_file, use_column_width=True)

with col2:
    st.subheader("📈 AI Trade Analysis")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            chart_path = tmp.name

        if st.button("🔍 Analyze Chart", use_container_width=True):
            with st.spinner("Analyzing market structure & risk..."):
                analysis = analyze_chart(chart_path)

            st.success("Analysis complete")
            st.markdown(analysis)

    else:
        st.info("Upload a chart to receive AI-based trade analysis.")

# ---------- FOOTER ----------
st.divider()
st.caption(
    "⚠️ Educational purposes only. "
    "Trade ideas are probabilistic and not financial advice."
)
