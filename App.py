import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Function to fetch historical data from CoinGecko
def fetch_coingecko_data(symbol="bitcoin", currency="usd", days="7", interval="hourly"):
    """
    Fetch OHLC data from CoinGecko API.
    - symbol: The cryptocurrency slug (e.g., "bitcoin").
    - currency: The fiat currency (e.g., "usd").
    - days: Number of days of historical data to fetch (e.g., "1", "7", "max").
    - interval: Data granularity ("hourly" or "daily").
    """
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {"vs_currency": currency, "days": days, "interval": interval}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Error fetching data from CoinGecko: {response.json()}")

    data = response.json()
    prices = data["prices"]  # Get the timestamp and close price
    df = pd.DataFrame(prices, columns=["timestamp", "Close"])
    df["Open Time"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["Open Time", "Close"]]

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
symbol = st.sidebar.text_input("Cryptocurrency Slug (e.g., bitcoin)", value="bitcoin")
currency = st.sidebar.text_input("Fiat Currency (e.g., usd)", value="usd")
days = st.sidebar.selectbox("Historical Data Range (Days)", options=["1", "7", "30", "90", "365"], index=1)
interval = st.sidebar.selectbox("Data Granularity", options=["hourly", "daily"], index=0)

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
                df = calculate_indicators(df)
                st.success("Data fetched and processed successfully!")

                # Display raw data
                st.subheader("Raw Data")
                st.dataframe(df.tail())

                # Plot closing price with Bollinger Bands
                st.subheader(f"{symbol.capitalize()} Price and Bollinger Bands")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df["Open Time"], df["Close"], label="Close Price", color="blue")
                ax.plot(df["Open Time"], df["Bollinger_Upper"], label="Upper Band", linestyle="--", color="red")
                ax.plot(df["Open Time"], df["Bollinger_Lower"], label="Lower Band", linestyle="--", color="green")
                ax.fill_between(df["Open Time"], df["Bollinger_Lower"], df["Bollinger_Upper"], color="lightgrey", alpha=0.3)
                ax.set_title(f"{symbol.capitalize()} Bollinger Bands")
                ax.legend()
                st.pyplot(fig)

                # Plot RSI
                if "RSI" not in df or df["RSI"].isna().all():
                    st.error("RSI cannot be calculated. Ensure enough data is available.")
                else:
                    last_rsi = df["RSI"].iloc[-1]
                    st.subheader(f"{symbol.capitalize()} Relative Strength Index (RSI)")
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
