import { RSI, MACD, BollingerBands, KDJ, ATR } from 'technicalindicators';

export function calculateRSI(closes, period = 14) {
  return RSI.calculate({ values: closes, period });
}

export function calculateMACD(closes) {
  return MACD.calculate({ values: closes, fastPeriod: 12, slowPeriod: 26, signalPeriod: 9, SimpleMAOscillator: false, SimpleMASignal: false });
}

export function calculateBollinger(closes) {
  return BollingerBands.calculate({ period: 20, stdDev: 2, values: closes });
}

export function calculateKDJ(highs, lows, closes) {
  return KDJ.calculate({ high: highs, low: lows, close: closes, period: 14 });
}

export function calculateATR(highs, lows, closes) {
  return ATR.calculate({ high: highs, low: lows, close: closes, period: 14 });
}
