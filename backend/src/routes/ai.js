import { Router } from 'express';
import { analyzeWithAI } from '../aiAnalysis.js';

const router = Router();

router.post('/analyze', async (req, res, next) => {
  try {
    const { symbol, intervals } = req.body;
    const result = await analyzeWithAI({ symbol, intervals });
    res.json(result);
  } catch (err) {
    next(err);
  }
});

export default router;
