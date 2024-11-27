import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# Fetch data from CoinGecko
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

# Calculate technical indicators
def calculate_indicators(df):
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# Calculate Fibonacci retracement levels
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

# Recommend trades
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
            stop_loss = resistance * 0.98  # Stop loss below resistance
            take_profit = fibonacci_levels["0%"]  # Next Fibonacci level
        else:
            counter_recommendation = "Sell"
            counter_entry_price = last_price
            counter_stop_loss = resistance * 1.02  # Stop loss above resistance
            counter_take_profit = fibonacci_levels["61.8%"]  # Lower Fibonacci level
    elif trend == "downtrend":
        if last_price < fibonacci_levels["61.8%"]:
            recommendation = "Sell"
            entry_price = last_price
            stop_loss = fibonacci_levels["61.8%"] * 1.02  # Stop loss above Fibonacci level
            take_profit = fibonacci_levels["100%"]  # Next Fibonacci level
        else:
            counter_recommendation = "Buy"
            counter_entry_price = last_price
            counter_stop_loss = fibonacci_levels["61.8%"] * 0.98  # Stop loss below Fibonacci level
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
st.title("Comprehensive Crypto Analysis with Trade Recommendations")
symbol = st.sidebar.text_input("Cryptocurrency Slug (e.g., bitcoin)", "bitcoin")
currency = st.sidebar.text_input("Fiat Currency (e.g., usd)", "usd")
days = st.sidebar.selectbox("Historical Data Range (Days)", ["7", "30", "90"], index=0)

if st.sidebar.button("Fetch Data"):
    try:
        # Fetch and process data
        df = fetch_coingecko_data(symbol, currency, days)
        df = calculate_indicators(df)
        fibonacci_levels = calculate_fibonacci_levels(df)
        resistance = df["High"].rolling(10).max().iloc[-1]
        trend = "uptrend" if df["Close"].iloc[-1] > df["SMA_20"].iloc[-1] else "downtrend"

        # Get trade recommendations
        (
            recommendation,
            entry_price,
            stop_loss,
            take_profit,
            counter_recommendation,
            counter_entry_price,
            counter_stop_loss,
            counter_take_profit,
        ) = recommend_trade(df, fibonacci_levels, resistance, trend)

        # Display candlestick chart with indicators
        st.subheader(f"{symbol.capitalize()} Candlestick Chart with Indicators")
        fig = go.Figure()

        # Add candlestick
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

        # Display Trade Recommendations
        st.subheader("Primary Trade Recommendation")
        st.write(f"**Primary Recommendation**: {recommendation}")
        st.write(f"Entry: {entry_price:.2f}")
        st.write(f"Stop Loss: {stop_loss:.2f}" if stop_loss is not None else "Stop Loss: N/A")
        st.write(
            f"Take Profit: {take_profit:.2f}" if take_profit is not None else "Take Profit: N/A"
        )

        st.subheader("Counter Trade Recommendation")
        if counter_recommendation:
            st.write(f"**Counter Recommendation**: {counter_recommendation}")
            st.write(f"Entry: {counter_entry_price:.2f}")
            st.write(
                f"Stop Loss: {counter_stop_loss:.2f}"
                if counter_stop_loss is not None
                else "Stop Loss: N/A"
            )
            st.write(
                f"Take Profit: {counter_take_profit:.2f}"
                if counter_take_profit is not None
                else "Take Profit: N/A"
            )
        else:
            st.write("No counter trade recommendation available.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
