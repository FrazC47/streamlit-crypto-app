import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Function to fetch historical data from CoinGecko
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

# Function to calculate Fibonacci retracement levels
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

# Function to calculate resistance levels
def calculate_resistance_levels(df):
    highs = df["High"].rolling(window=10).max()
    resistance = highs[-10:].max()  # Recent significant resistance level
    return resistance

# Function to calculate indicators (RSI, Bollinger Bands)
def calculate_indicators(df):
    # Bollinger Bands
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["Bollinger_Upper"] = df["SMA_20"] + (2 * df["Close"].rolling(window=20).std())
    df["Bollinger_Lower"] = df["SMA_20"] - (2 * df["Close"].rolling(window=20).std())
    
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# Function to recommend a trade
def recommend_trade(df, fibonacci_levels, resistance, trend):
    last_price = df["Close"].iloc[-1]
    rsi = df["RSI"].iloc[-1]
    recommendation = ""
    entry_price = last_price
    stop_loss = None
    take_profit = None

    if trend == "uptrend" and rsi < 30:  # Buy signal
        recommendation = "Buy"
        stop_loss = fibonacci_levels["61.8%"]
        take_profit = resistance
    elif trend == "downtrend" and rsi > 70:  # Sell signal
        recommendation = "Sell"
        stop_loss = resistance
        take_profit = fibonacci_levels["61.8%"]
    else:  # Hold signal
        recommendation = "Hold"

    # Ensure a fallback stop-loss
    if stop_loss is None:
        stop_loss = last_price * 0.98  # Default to 2% below the current price

    return recommendation, entry_price, stop_loss, take_profit

# Function to detect trend
def detect_trend(df):
    recent_high = df["High"].iloc[-10:].max()
    recent_low = df["Low"].iloc[-10:].min()
    trend = "uptrend" if recent_high > recent_low else "downtrend"
    return trend

# Streamlit app setup
st.title("Comprehensive Crypto Analysis with Trade Recommendations")
st.sidebar.header("Settings")

# Sidebar inputs
symbol = st.sidebar.text_input("Cryptocurrency Slug (e.g., bitcoin)", value="bitcoin")
currency = st.sidebar.text_input("Fiat Currency (e.g., usd)", value="usd")
days = st.sidebar.selectbox("Historical Data Range (Days)", options=["2", "7", "30", "90"], index=1)
interval = st.sidebar.selectbox("Data Granularity", options=["daily", "hourly"], index=0 if int(days) < 2 else 1)

# Fetch data when the user clicks the button
if st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        try:
            df = fetch_coingecko_data(symbol, currency, days, interval)

            if len(df) < 20:
                st.error("Not enough data to calculate indicators. Try increasing the data range.")
            else:
                df = calculate_indicators(df)
                fibonacci_levels = calculate_fibonacci_levels(df)
                resistance = calculate_resistance_levels(df)
                trend = detect_trend(df)
                recommendation, entry_price, stop_loss, take_profit = recommend_trade(
                    df, fibonacci_levels, resistance, trend
                )

                # Candlestick chart with Fibonacci levels, Bollinger Bands, and Resistance
                st.subheader(f"{symbol.capitalize()} Candlestick Chart with Indicators")
                fig = go.Figure()

                # Add candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df["Open Time"],
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"],
                        name="Candlesticks",
                    )
                )

                # Add Bollinger Bands
                fig.add_trace(
                    go.Scatter(
                        x=df["Open Time"],
                        y=df["Bollinger_Upper"],
                        mode="lines",
                        line=dict(color="blue", dash="dot"),
                        name="Bollinger Upper",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df["Open Time"],
                        y=df["Bollinger_Lower"],
                        mode="lines",
                        line=dict(color="blue", dash="dot"),
                        name="Bollinger Lower",
                    )
                )

                # Add Fibonacci levels
                for level, value in fibonacci_levels.items():
                    fig.add_hline(
                        y=value,
                        line_dash="dot",
                        annotation_text=level,
                        annotation_position="right",
                        line_color="green",
                    )

                # Add resistance level
                fig.add_hline(
                    y=resistance, line_dash="dot", annotation_text="Resistance", line_color="red"
                )

                fig.update_layout(
                    title=f"{symbol.capitalize()} Candlestick Chart with Indicators",
                    xaxis_title="Date",
                    yaxis_title=f"Price ({currency.upper()})",
                    template="plotly_dark",
                )
                st.plotly_chart(fig)

                # Display RSI as a separate chart
                st.subheader(f"{symbol.capitalize()} Relative Strength Index (RSI)")
                st.line_chart(df["RSI"])

                # Display Trade Recommendation
                st.subheader("Trade Recommendation")
                st.write(f"**Recommendation**: {recommendation}")
                st.write(f"**Entry Price**: {entry_price:.2f}")
                st.write(f"**Stop Loss**: {stop_loss:.2f}")
                if take_profit is not None:
                    st.write(f"**Take Profit**: {take_profit:.2f}")
                else:
                    st.write("**Take Profit**: Not applicable")

        except Exception as e:
            st.error(f"An error occurred: {e}")
