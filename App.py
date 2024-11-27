import streamlit as st
import requests
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
import mplfinance as mpf

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

# Plot candlestick chart using Bokeh
def plot_bokeh_candlestick(df):
    df["Date"] = df["Open Time"]
    inc = df["Close"] > df["Open"]
    dec = df["Open"] > df["Close"]

    source_inc = ColumnDataSource(df.loc[inc])
    source_dec = ColumnDataSource(df.loc[dec])

    p = figure(
        x_axis_type="datetime",
        title="Candlestick Chart",
        height=400,  # Corrected attribute
        tools="pan,wheel_zoom,box_zoom,reset",
    )
    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "Price"

    # Plot candles
    width = 12 * 60 * 60 * 1000  # Half-day in ms
    p.segment(x0="Date", y0="High", x1="Date", y1="Low", source=source_inc, color="green")
    p.segment(x0="Date", y0="High", x1="Date", y1="Low", source=source_dec, color="red")
    p.vbar(x="Date", top="Close", bottom="Open", width=width, fill_color="green", source=source_inc)
    p.vbar(x="Date", top="Open", bottom="Close", width=width, fill_color="red", source=source_dec)

    hover = HoverTool(
        tooltips=[
            ("Date", "@Date{%F}"),
            ("Open", "@Open"),
            ("High", "@High"),
            ("Low", "@Low"),
            ("Close", "@Close"),
        ],
        formatters={"@Date": "datetime"},
    )
    p.add_tools(hover)

    return p

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

    # Ensure stop loss and take profit are always set
    if stop_loss is None:
        stop_loss = last_price * 0.98  # Default stop loss 2% below current price
    if counter_stop_loss is None:
        counter_stop_loss = last_price * 1.02  # Default counter stop loss 2% above current price

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
st.title("Comprehensive Crypto Analysis with Improved Charts and Trade Recommendations")
symbol = st.sidebar.text_input("Cryptocurrency Slug (e.g., bitcoin)", "bitcoin")
currency = st.sidebar.text_input("Fiat Currency (e.g., usd)", "usd")
days = st.sidebar.selectbox("Historical Data Range (Days)", ["7", "30", "90"], index=0)

if st.sidebar.button("Fetch Data"):
    try:
        # Fetch and process data
        df = fetch_coingecko_data(symbol, currency, days)

        # Plot candlestick chart
        st.subheader(f"{symbol.capitalize()} Candlestick Chart")
        bokeh_chart = plot_bokeh_candlestick(df)
        st.bokeh_chart(bokeh_chart)

    except Exception as e:
        st.error(f"An error occurred: {e}")
