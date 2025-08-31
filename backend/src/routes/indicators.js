import { Router } from 'express';
import { fetchCandles } from '../binanceService.js';
import { calculateRSI, calculateMACD, calculateBollinger, calculateKDJ, calculateATR } from '../indicatorService.js';

const router = Router();

router.get('/indicators/:symbol/:interval', async (req, res, next) => {
  try {
    const { symbol, interval } = req.params;
    const candles = await fetchCandles(symbol.toUpperCase(), interval);
    const closes = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    res.json({
      rsi: calculateRSI(closes),
      macd: calculateMACD(closes),
      bollinger: calculateBollinger(closes),
      kdj: calculateKDJ(highs, lows, closes),
      atr: calculateATR(highs, lows, closes)
    });
  } catch (err) {
    next(err);
  }
});

export default router;
