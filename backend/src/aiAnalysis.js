import OpenAI from 'openai';
import { fetchCandles } from './binanceService.js';
import { calculateRSI, calculateMACD, calculateBollinger, calculateKDJ, calculateATR } from './indicatorService.js';

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function analyzeWithAI({ symbol, intervals }) {
  const allData = {};
  for (const interval of intervals) {
    const candles = await fetchCandles(symbol, interval);
    const closes = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    allData[interval] = {
      candles,
      indicators: {
        rsi: calculateRSI(closes),
        macd: calculateMACD(closes),
        bollinger: calculateBollinger(closes),
        kdj: calculateKDJ(highs, lows, closes),
        atr: calculateATR(highs, lows, closes)
      }
    };
  }

  const prompt = `Act as an ETH/AVAX futures trader. Analyze the following multi-timeframe data for ${symbol} and provide signals. Data: ${JSON.stringify(allData)}.`;
  const response = await client.responses.create({ model: 'gpt-4o-mini', input: prompt });
  const text = response.output[0].content[0].text;
  return { raw: text };
}
