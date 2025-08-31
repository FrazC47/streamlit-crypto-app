import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import dotenv from 'dotenv';

import authRoutes from './routes/auth.js';
import binanceRoutes from './routes/binance.js';
import indicatorRoutes from './routes/indicators.js';
import aiRoutes from './routes/ai.js';

dotenv.config();

const app = express();
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.use('/api/auth', authRoutes);
app.use('/api', binanceRoutes);
app.use('/api', indicatorRoutes);
app.use('/api/ai', aiRoutes);

// error handler
app.use((err, req, res, next) => {
  console.error(err); // eslint-disable-line no-console
  res.status(err.status || 500).json({ error: err.message || 'Server error' });
});

export default app;

if (process.env.NODE_ENV !== 'test') {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(`Server listening on port ${port}`); // eslint-disable-line no-console
  });
}
