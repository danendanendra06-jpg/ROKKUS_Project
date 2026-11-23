import { LOW_STOCK_THRESHOLD } from '../config/constants';

/**
 * Returns bread status based on stock count
 * @param {number} stock 
 * @param {number} threshold 
 * @returns {'Aman' | 'Menipis' | 'Habis'}
 */
export function getBreadStockStatus(stock, threshold = LOW_STOCK_THRESHOLD) {
  if (stock <= 0) return 'Habis';
  if (stock < threshold) return 'Menipis';
  return 'Aman';
}

/**
 * Calculate average days between consecutive purchases
 * Returns '-' if fewer than 2 purchases
 * @param {Array<{ date: string }>} purchases 
 * @returns {string | number}
 */
export function calculateAverageRepurchaseDays(purchases = []) {
  if (!purchases || purchases.length < 2) {
    return '-';
  }

  // Sort chronologically ascending
  const sorted = [...purchases].sort((a, b) => new Date(a.date) - new Date(b.date));
  let totalDiffDays = 0;
  const count = sorted.length - 1;

  for (let i = 0; i < count; i++) {
    const d1 = new Date(sorted[i].date);
    const d2 = new Date(sorted[i + 1].date);
    const diffTime = Math.abs(d2 - d1);
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    totalDiffDays += diffDays;
  }

  const avg = Math.round((totalDiffDays / count) * 10) / 10;
  return `${avg} hari`;
}
