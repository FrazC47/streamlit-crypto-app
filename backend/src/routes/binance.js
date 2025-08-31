import { Router } from 'express';
import { fetchCandles } from '../binanceService.js';

const router = Router();
const intervals = ['1m','5m','15m','30m','1h','2h','4h','8h','12h','1d','1w'];

router.get('/candles/:symbol/:interval', async (req, res, next) => {
  try {
    const { symbol, interval } = req.params;
    if (!intervals.includes(interval)) {
      return res.status(400).json({ error: 'Unsupported interval' });
    }
    const candles = await fetchCandles(symbol.toUpperCase(), interval);
    res.json(candles);
  } catch (err) {
    next(err);
  }
});

export default router;
