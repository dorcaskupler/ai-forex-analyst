import streamlit as st
import openai

# --- Streamlit App Title ---
st.set_page_config(page_title="AI Forex Analyst", page_icon="💹")
st.title("💹 AI Forex Analyst")

# --- Input your OpenAI API Key ---
api_key = st.text_input("Enter your OpenAI API Key", type="password")
if api_key:
    openai.api_key = api_key

    # --- User Input for Forex Analysis ---
    user_input = st.text_area("Enter Forex chat / trading info:")

    if st.button("Analyze"):
        if user_input.strip() == "":
            st.warning("Please enter some text to analyze.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert Forex analyst."},
                            {"role": "user", "content": user_input}
                        ],
                        max_tokens=300
                    )
                    answer = response.choices[0].message.content
                    st.success("Analysis Complete!")
                    st.write(answer)
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    st.info("Please enter your OpenAI API Key to start.")
