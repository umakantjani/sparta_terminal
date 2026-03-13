import streamlit as st
import pandas as pd
from src.engine import get_sniper_report, get_gemini_analysis
from supabase import create_client

# Supabase Setup
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

st.title("🏹 SPARTA SNIPER TERMINAL")
ticker = st.text_input("QUERY TICKER >", value="NVDA").upper()

if ticker:
    df, signal, val, b_width = get_sniper_report(ticker)
    
    # THE SAFETY VALVE: Only show metrics if df is NOT None
    if df is not None and not df.empty:
        curr = df.iloc[-1]
        
        # --- Metrics Grid ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("LAST", f"${curr['Close']:.2f}")
        c2.metric("SMA50", f"${curr['SMA50']:.2f}")
        c3.metric("RSI", f"{curr['RSI']:.2f}")
        c4.metric("BB WIDTH", f"{b_width:.4f}")

        # --- Chart ---
        st.line_chart(df[['Close', 'SMA50']])

    # --- Gemini Report ---
    st.subheader("🤖 AI SNIPER INTELLIGENCE")
    if st.button("GENERATE AI ANALYSIS"):
        with st.spinner("Processing Trinity Data..."):
            ai_report = get_gemini_analysis(ticker, curr['Close'], signal, b_width, curr['RSI'], curr['SMA50'], val)
            st.session_state['last_report'] = ai_report # Save to session state
            st.markdown(ai_report)

    # --- Save to Cloud ---
    if 'last_report' in st.session_state:
        if st.button("💾 ARCHIVE REPORT TO SUPABASE"):
            data = {
                "ticker": ticker,
                "price": float(curr['Close']),
                "signal": signal,
                "valuation_report": val,
                "ai_analysis": st.session_state['last_report']
            }
            supabase.table("sniper_reports").insert(data).execute()
            st.success("Analysis persisted to cloud database.")
else:
        st.warning("⚠️ DATA SOURCE OFFLINE: Yahoo is rate-limiting the cloud IP.")
        st.info("Spartan Protocol: Use your Local VS Code Terminal for live data.")