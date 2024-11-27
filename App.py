import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# Fetch data
def fetch_coingecko_data(symbol="bitcoin", currency="usd", days="7", interval=None):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {"vs_currency": currency, "days": days}
    if interval and int(days) >= 2 and int(days) <= 90:
        params["interval"] = interval
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from CoinGecko: {response.json()}")
    data = response.json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "Close"])
    df["Open Time"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["High"] = df["Close"]
    df["Low"] = df["Close"]
    df["Open"] = df["Close"].shift(1).fillna(df["Close"])
    return df[["Open Time", "Open", "High", "Low", "Close"]]

# Indicators
def calculate_indicators(df):
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def calculate_fibonacci_levels(df):
    max_price = df["High"].max()
    min_price = df["Low"].min()
    diff = max_price - min_price
    levels = {
        "0%": max_price,
        "23.6%": max_price - 0.236 * diff,
        "38.2%": max_price - 0.382 * diff,
        "50%": max_price - 0.5 * diff,
        "61.8%": max_price - 0.618 * diff,
        "100%": min_price,
    }
    return levels

# Trade Recommendations
def recommend_trade(df, fibonacci_levels, resistance, trend):
    last_price = df["Close"].iloc[-1]
    rsi = df["RSI"].iloc[-1]
    recommendation = ""
    counter_recommendation = ""
    entry_price = last_price
    counter_entry_price = last_price
    stop_loss = None
    counter_stop_loss = None
    take_profit = None
    counter_take_profit = None

    if trend == "uptrend":
        if last_price > resistance:
            recommendation = "Buy"
            entry_price = last_price
            stop_loss = resistance * 0.98
            take_profit = fibonacci_levels["0%"]
        else:
            counter_recommendation = "Sell"
            counter_entry_price = last_price
            counter_stop_loss = resistance * 1.02
            counter_take_profit = fibonacci_levels["61.8%"]

    elif trend == "downtrend":
        if last_price < fibonacci_levels["61.8%"]:
            recommendation = "Sell"
            entry_price = last_price
            stop_loss = fibonacci_levels["61.8%"] * 1.02
            take_profit = fibonacci_levels["100%"]
        else:
            counter_recommendation = "Buy"
            counter_entry_price = last_price
            counter_stop_loss = fibonacci_levels["61.8%"] * 0.98
            counter_take_profit = resistance

    return (
        recommendation,
        entry_price,
        stop_loss,
        take_profit,
        counter_recommendation,
        counter_entry_price,
        counter_stop_loss,
        counter_take_profit,
    )

# Streamlit UI
st.title("Comprehensive Crypto Analysis")
symbol = st.sidebar.text_input("Cryptocurrency Slug (e.g., bitcoin)", "bitcoin")
currency = st.sidebar.text_input("Fiat Currency (e.g., usd)", "usd")
days = st.sidebar.selectbox("Historical Data Range (Days)", ["7", "30", "90"], index=0)

if st.sidebar.button("Fetch Data"):
    df = fetch_coingecko_data(symbol, currency, days)
    df = calculate_indicators(df)
    fibonacci_levels = calculate_fibonacci_levels(df)
    resistance = df["High"].rolling(10).max().iloc[-1]
    trend = "uptrend" if df["Close"].iloc[-1] > df["SMA_20"].iloc[-1] else "downtrend"

    recommendation, entry_price, stop_loss, take_profit, counter_recommendation, counter_entry_price, counter_stop_loss, counter_take_profit = recommend_trade(
        df, fibonacci_levels, resistance, trend
    )

    st.write("## Trade Recommendations")
    st.write(f"**Primary Trade**: {recommendation}")
    st.write(f"Entry: {entry_price:.2f}, Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f if take_profit else 'N/A'}")
    st.write(f"**Counter Trade**: {counter_recommendation}")
    st.write(f"Entry: {counter_entry_price:.2f}, Stop Loss: {counter_stop_loss:.2f}, Take Profit: {counter_take_profit:.2f if counter_take_profit else 'N/A'}")
