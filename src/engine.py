import pandas as pd
import pandas_ta as ta
import yfinance as yf
import google.generativeai as genai
import streamlit as st

# Configure Gemini
genai.configure(api_key=st.secrets["gemini"]["api_key"])
# model = genai.GenerativeModel('gemini-1.5-flash')
model = genai.GenerativeModel('models/gemini-2.5-flash')

def get_gemini_analysis(ticker, price, signal, b_width, rsi, sma50, valuation):
    prompt = f"""
    Act as a professional algorithmic trader using the 'Sniper's Trinity' strategy.
    Analyze the following data for {ticker}:
    - Current Price: ${price}
    - Technical Signal: {signal}
    - Bollinger Band Width (Squeeze): {b_width:.4f}
    - RSI: {rsi:.2f}
    - SMA 50: ${sma50}
    - Fundamental Data: {valuation}

    Provide a sophisticated, minimalist report in the following format:
    1. MARKET SENTIMENT (Brief summary)
    2. THE TRINITY ANALYSIS (Detailed technical interpretation)
    3. THE ACTION (Specific trade guidance based on the Sniper Strategy)
    4. RISK ASSESSMENT (Critical levels to watch)
    Keep it datacentric and professional.
    """
    response = model.generate_content(prompt)
    return response.text

def get_sniper_report(ticker):
    # We no longer pass a custom session. 
    # yfinance 1.0+ handles impersonation internally now.
    stock = yf.Ticker(ticker)
    
    try:
        # auto_adjust=True is critical for technical accuracy
        df = stock.history(period="1y", auto_adjust=True)
    except Exception as e:
        st.error(f"Data Retrieval Error: {e}")
        return None, "ERROR", {}, 0
    
    if df.empty:
        return None, "NO DATA", {}, 0

    # Flatten MultiIndex columns (Fix for the previous KeyError)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    # Standard Indicators
    df['SMA50'] = ta.sma(df['Close'], length=50)
    df['SMA100'] = ta.sma(df['Close'], length=100)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Bollinger Bands
    bb = ta.bbands(df['Close'], length=20, std=2)
    df['BBL'] = bb.iloc[:, 0]
    df['BBM'] = bb.iloc[:, 1]
    df['BBU'] = bb.iloc[:, 2]
    
    curr = df.iloc[-1]
    b_width = (curr['BBU'] - curr['BBL']) / curr['BBM']
    
    # Sniper Logic
    signal = "NEUTRAL"
    if curr['Close'] > curr['SMA50'] and b_width < 0.05:
        signal = "BUY SQUEEZE"
    elif curr['Close'] < curr['SMA50'] and b_width < 0.05:
        signal = "SELL SQUEEZE"
        
    return df, signal, get_valuation_metrics(stock), b_width

def get_valuation_metrics(ticker_obj):
    info = ticker_obj.info
    return {
        "P/E": info.get("trailingPE", "N/A"),
        "Forward P/E": info.get("forwardPE", "N/A"),
        "PEG": info.get("pegRatio", "N/A"),
        "Cap": f"{info.get('marketCap', 0) / 1e12:.2f}T"
    }