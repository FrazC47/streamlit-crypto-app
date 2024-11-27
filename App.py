import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# Function to fetch historical data from CoinGecko
def fetch_coingecko_data(symbol="bitcoin", currency="usd", days="7", interval=None):
    """
    Fetch OHLC data from CoinGecko API.
    - symbol: The cryptocurrency slug (e.g., "bitcoin").
    - currency: The fiat currency (e.g., "usd").
    - days: Number of days of historical data to fetch (e.g., "1", "7", "30", "max").
    - interval: Optional. Data granularity ("hourly" or "daily").
    """
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    
    # Adjust parameters dynamically
    params = {"vs_currency": currency, "days": days}
    if interval and int(days) >= 2 and int(days) <= 90:
        params["interval"] = interval  # Only include interval if valid
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data from CoinGecko: {response.json()}")

    data = response.json()
    prices = data["prices"]  # Get the timestamp and close price
    df = pd.DataFrame(prices, columns=["timestamp", "Close"])
    df["Open Time"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["High"] = df["Close"]
    df["Low"] = df["Close"]
    df["Open"] = df["Close"].shift(1).fillna(df["Close"])  # Generate mock Open prices
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

# Streamlit app setup
st.title("Crypto Price Analysis with Fibonacci Levels")
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
            # Fetch and process data
            df = fetch_coingecko_data(symbol, currency, days, interval)

            # Ensure there are enough rows to calculate indicators
            if len(df) < 20:
                st.error("Not enough data to calculate indicators. Try increasing the data range.")
            else:
                st.success("Data fetched successfully!")

                # Display raw data
                st.subheader("Raw Data")
                st.dataframe(df.tail())

                # Calculate Fibonacci Levels
                fibonacci_levels = calculate_fibonacci_levels(df)

                # Plot candlestick chart with Fibonacci levels
                st.subheader(f"{symbol.capitalize()} Candlestick Chart with Fibonacci Levels")
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

                # Add Fibonacci levels
                for level, value in fibonacci_levels.items():
                    fig.add_hline(
                        y=value,
                        line_dash="dot",
                        annotation_text=level,
                        annotation_position="right",
                        line_color="green",
                    )

                # Configure layout
                fig.update_layout(
                    title=f"{symbol.capitalize()} Candlestick Chart with Fibonacci Levels",
                    xaxis_title="Date",
                    yaxis_title=f"Price ({currency.upper()})",
                    template="plotly_dark",
                )

                # Display chart
                st.plotly_chart(fig)
        except Exception as e:
            st.error(f"An error occurred: {e}")
