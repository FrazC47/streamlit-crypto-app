import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Binance API endpoint for OHLC data
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"

# Function to fetch historical data from Binance
def fetch_binance_data(symbol="BTCUSDT", interval="1h", limit=100):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(BINANCE_API_URL, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from Binance: {response.json()}")
    data = response.json()
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        "Open Time", "Open", "High", "Low", "Close", "Volume",
        "Close Time", "Quote Asset Volume", "Number of Trades",
        "Taker Buy Base Volume", "Taker Buy Quote Volume", "Ignore"
    ])
    # Process DataFrame
    df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms")
    df["Close"] = df["Close"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Volume"] = df["Volume"].astype(float)
    return df[["Open Time", "Open", "High", "Low", "Close", "Volume"]]

# Function to calculate indicators
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

# Streamlit app setup
st.title("Crypto Price Analysis App")
st.sidebar.header("Settings")

# Sidebar inputs
symbol = st.sidebar.text_input("Cryptocurrency Pair (e.g., BTCUSDT)", value="BTCUSDT")
interval = st.sidebar.selectbox("Time Interval", options=["1m", "5m", "15m", "1h", "4h", "1d"], index=3)
limit = st.sidebar.slider("Number of Candles", min_value=50, max_value=500, value=100)

# Fetch data when the user clicks the button
if st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        try:
            df = fetch_binance_data(symbol, interval, limit)

            # Ensure there are enough rows to calculate indicators
            if len(df) < 20:
                st.error("Not enough data to calculate indicators. Try increasing the number of candles.")
            else:
                df = calculate_indicators(df)
                st.success("Data fetched and processed successfully!")
                
                # Display raw data
                st.subheader("Raw Data")
                st.dataframe(df.tail())
                
                # Plot closing price with Bollinger Bands
                st.subheader(f"{symbol} Price and Bollinger Bands")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df["Open Time"], df["Close"], label="Close Price", color="blue")
                ax.plot(df["Open Time"], df["Bollinger_Upper"], label="Upper Band", linestyle="--", color="red")
                ax.plot(df["Open Time"], df["Bollinger_Lower"], label="Lower Band", linestyle="--", color="green")
                ax.fill_between(df["Open Time"], df["Bollinger_Lower"], df["Bollinger_Upper"], color="lightgrey", alpha=0.3)
                ax.set_title(f"{symbol} Bollinger Bands")
                ax.legend()
                st.pyplot(fig)
                
                # Plot RSI
                if "RSI" not in df or df["RSI"].isna().all():
                    st.error("RSI cannot be calculated. Ensure enough data is available.")
                else:
                    last_rsi = df["RSI"].iloc[-1]
                    st.subheader(f"{symbol} Relative Strength Index (RSI)")
                    st.line_chart(df["RSI"])
                    
                    # RSI trigger messages
                    if last_rsi > 70:
                        st.warning("RSI indicates overbought conditions! Consider selling.")
                    elif last_rsi < 30:
                        st.success("RSI indicates oversold conditions! Consider buying.")
                    else:
                        st.info("RSI is neutral.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
