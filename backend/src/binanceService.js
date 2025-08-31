import axios from 'axios';

const baseURL = process.env.BINANCE_BASE_URL || 'https://api.binance.com';

export async function fetchCandles(symbol, interval, limit = 500) {
  const url = `${baseURL}/api/v3/klines`;
  const params = { symbol, interval, limit };
  const { data } = await axios.get(url, { params });
  return data.map(c => ({
    openTime: c[0],
    open: parseFloat(c[1]),
    high: parseFloat(c[2]),
    low: parseFloat(c[3]),
    close: parseFloat(c[4]),
    volume: parseFloat(c[5]),
    closeTime: c[6]
  }));
}
