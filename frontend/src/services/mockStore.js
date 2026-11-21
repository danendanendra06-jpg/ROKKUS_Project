import {
  initialBreadStock,
  initialMenuItems,
  initialToppings,
  initialTransactions,
} from '../mocks/seed';
import { getTodayDateString } from '../utils/date';
import {
  shouldSimulateLoadFail,
  shouldSimulateSaveFail,
  shouldSimulateAiFail,
} from './apiClient';

// In-memory state (resets on page refresh)
class MockStore {
  constructor() {
    this.reset();
  }

  reset() {
    this.breadStock = JSON.parse(JSON.stringify(initialBreadStock));
    this.menuItems = JSON.parse(JSON.stringify(initialMenuItems));
    this.toppings = JSON.parse(JSON.stringify(initialToppings));
    this.transactions = JSON.parse(JSON.stringify(initialTransactions));
  }

  // Latency simulator
  delay(min = 400, max = 800) {
    const ms = Math.floor(Math.random() * (max - min + 1)) + min;
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // --- Bread Stock ---
  async getBreadStock() {
    await this.delay();
    if (shouldSimulateLoadFail()) {
      throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
    }
    return { ...this.breadStock };
  }

  async updateInitialStock(newInitialStock) {
    await this.delay();
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const diff = Number(newInitialStock) - (this.breadStock.initialStock || 0);
    this.breadStock.initialStock = Number(newInitialStock);
    this.breadStock.stock += diff;
    return { ...this.breadStock };
  }

  // --- Menu Items ---
  async getMenuItems(category) {
    await this.delay();
    if (shouldSimulateLoadFail()) {
      throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
    }
    if (!category || category === 'Semua') {
      return [...this.menuItems];
    }
    return this.menuItems.filter((m) => m.category === category);
  }

  async createMenuItem(itemData) {
    await this.delay();
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const newItem = {
      id: `m-${Date.now()}`,
      name: itemData.name.trim(),
      category: itemData.category,
      tag: itemData.tag || null,
      todaySales: 0,
    };
    this.menuItems.push(newItem);
    return { ...newItem };
  }

  async updateMenuItem(id, itemData) {
    await this.delay();
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const index = this.menuItems.findIndex((m) => m.id === id);
    if (index === -1) throw new Error('Menu tidak ditemukan');
    this.menuItems[index] = {
      ...this.menuItems[index],
      name: itemData.name.trim(),
      category: itemData.category,
      tag: itemData.tag || null,
    };
    return { ...this.menuItems[index] };
  }

  async deleteMenuItem(id) {
    await this.delay();
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const index = this.menuItems.findIndex((m) => m.id === id);
    if (index === -1) throw new Error('Menu tidak ditemukan');
    const deleted = this.menuItems.splice(index, 1)[0];
    return { success: true, deleted };
  }

  // --- Transactions ---
  async getTransactions({ from, to, type, q, page = 1, limit = 10 } = {}) {
    await this.delay();
    if (shouldSimulateLoadFail()) {
      throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
    }
    let result = [...this.transactions];

    if (type && type !== 'Semua') {
      result = result.filter((t) => t.type === type.toLowerCase());
    }

    if (from) {
      result = result.filter((t) => t.date >= from);
    }

    if (to) {
      result = result.filter((t) => t.date <= to);
    }

    if (q) {
      const query = q.toLowerCase();
      result = result.filter(
        (t) =>
          t.details.toLowerCase().includes(query) ||
          (t.note && t.note.toLowerCase().includes(query)) ||
          t.recordedBy.toLowerCase().includes(query)
      );
    }

    const total = result.length;
    const startIndex = (page - 1) * limit;
    const items = result.slice(startIndex, startIndex + limit);

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit) || 1,
    };
  }

  async createTransaction(payload) {
    await this.delay(500, 900);
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const today = getTodayDateString();
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const datetime = `${payload.date || today} ${hours}:${minutes}`;

    if (payload.type === 'masuk') {
      const qty = Number(payload.qty);
      if (qty <= 0) throw new Error('Jumlah harus lebih dari 0');

      this.breadStock.stock += qty;
      if ((payload.date || today) === today) {
        this.breadStock.masukHariIni += qty;
      }

      const newTrx = {
        id: `trx-${Date.now()}`,
        datetime,
        date: payload.date || today,
        type: 'masuk',
        totalQty: qty,
        details: `${payload.session || 'Sesi 1'} - Pasokan Roti`,
        session: payload.session || 'Sesi 1',
        cookingMethod: '-',
        stockAfter: this.breadStock.stock,
        recordedBy: payload.recordedBy || 'Budi Santoso',
        note: payload.note || '',
      };

      this.transactions.unshift(newTrx);
      return { success: true, transaction: newTrx, currentStock: this.breadStock.stock };
    }

    if (payload.type === 'keluar') {
      const items = payload.items || [];
      // Calculate total bread reduced (Roti Manis + Roti Asin only, NOT Tambahan)
      let totalBreadQty = 0;
      const detailsArr = [];

      items.forEach((item) => {
        const menuItem = this.menuItems.find((m) => m.id === item.menuItemId);
        if (menuItem && item.qty > 0) {
          const isTambahan = menuItem.category === 'Tambahan';
          if (!isTambahan) {
            totalBreadQty += item.qty;
          }
          detailsArr.push(`${menuItem.name} ${item.qty}${isTambahan ? ' (Tambahan)' : ''}`);

          // Update todaySales if date is today
          if ((payload.date || today) === today) {
            menuItem.todaySales = (menuItem.todaySales || 0) + item.qty;
          }
        }
      });

      if (totalBreadQty > this.breadStock.stock) {
        const err = new Error(
          `Stok roti tidak mencukupi. Stok tersedia: ${this.breadStock.stock}, jumlah diminta: ${totalBreadQty}.`
        );
        err.code = 'INSUFFICIENT_STOCK';
        err.available = this.breadStock.stock;
        err.requested = totalBreadQty;
        throw err;
      }

      this.breadStock.stock -= totalBreadQty;
      if ((payload.date || today) === today) {
        this.breadStock.keluarHariIni += totalBreadQty;
      }

      const newTrx = {
        id: `trx-${Date.now()}`,
        datetime,
        date: payload.date || today,
        type: 'keluar',
        totalQty: totalBreadQty,
        details: detailsArr.join(', '),
        items: items.map((i) => {
          const m = this.menuItems.find((x) => x.id === i.menuItemId);
          return {
            menuItemId: i.menuItemId,
            name: m ? m.name : 'Unknown',
            qty: i.qty,
            category: m ? m.category : 'Roti Manis',
          };
        }),
        cookingMethod: payload.cookingMethod || '-',
        stockAfter: this.breadStock.stock,
        recordedBy: payload.recordedBy || 'Budi Santoso',
        note: payload.note || '',
      };

      this.transactions.unshift(newTrx);
      return { success: true, transaction: newTrx, currentStock: this.breadStock.stock };
    }

    throw new Error('Tipe transaksi tidak valid');
  }

  // --- Toppings ---
  async getToppings() {
    await this.delay();
    if (shouldSimulateLoadFail()) {
      throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
    }
    return JSON.parse(JSON.stringify(this.toppings));
  }

  async updateToppingStatus(id, newStatus) {
    await this.delay();
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const topping = this.toppings.find((t) => t.id === id);
    if (!topping) throw new Error('Topping tidak ditemukan');
    topping.status = newStatus;
    return { ...topping };
  }

  async createToppingPurchase({ toppingId, date, qty, unit, recordedBy }) {
    await this.delay();
    if (shouldSimulateSaveFail()) {
      throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
    }
    const topping = this.toppings.find((t) => t.id === toppingId);
    if (!topping) throw new Error('Topping tidak ditemukan');

    const newPurchase = {
      id: `tp-${Date.now()}`,
      date: date || getTodayDateString(),
      qty: Number(qty),
      unit: unit || 'kg',
      recordedBy: recordedBy || 'Budi Santoso',
    };

    if (!topping.purchases) topping.purchases = [];
    topping.purchases.push(newPurchase);

    return { success: true, topping: { ...topping }, purchase: newPurchase };
  }

  async getAllToppingPurchases() {
    await this.delay();
    if (shouldSimulateLoadFail()) {
      throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
    }
    const purchases = [];
    this.toppings.forEach((top) => {
      if (top.purchases) {
        top.purchases.forEach((p) => {
          purchases.push({
            ...p,
            toppingId: top.id,
            toppingName: top.name,
          });
        });
      }
    });

    // Sort descending by date
    return purchases.sort((a, b) => new Date(b.date) - new Date(a.date));
  }

  // --- Dashboard ---
  async getDashboardSummary() {
    await this.delay();
    if (shouldSimulateLoadFail()) {
      throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
    }
    // Top 5 sales today
    const topSales = [...this.menuItems]
      .filter((m) => (m.todaySales || 0) > 0)
      .sort((a, b) => b.todaySales - a.todaySales)
      .slice(0, 7)
      .map((m) => ({
        name: m.name,
        category: m.category,
        sales: m.todaySales,
      }));

    // Recent 5 transactions
    const recentTransactions = this.transactions.slice(0, 5);

    return {
      stock: this.breadStock.stock,
      masukHariIni: this.breadStock.masukHariIni,
      keluarHariIni: this.breadStock.keluarHariIni,
      topSales,
      recentTransactions,
    };
  }

  async getAiSummary(shouldFail = false) {
    await this.delay(600, 1000);
    if (shouldFail || shouldSimulateAiFail()) {
      throw new Error('Layanan AI tidak dapat dihubungi saat ini.');
    }

    return {
      generatedAt: new Date().toISOString(),
      summary:
        "Tren stok roti hijau pandan hari ini berjalan dinamis dengan serapan tertinggi pada varian Coklat Crunchy (14 pcs) dan Coklat Keju (10 pcs). Sisa stok berada di level 45 pcs (Status Menipis), disarankan melakukan persiapan pasokan roti sesi sore/malam untuk menjaga ketersediaan hingga jam operasional berakhir.",
      recommendations: [
        "Persiapkan pasokan sesi sore minimal 40-50 pcs untuk mengantisipasi rush hour malam.",
        "Topping Nutella berstatus Habis dan Keju Parut Hampir Habis; jadwalkan pembelian ulang segera.",
      ],
    };
  }
}

export const mockStore = new MockStore();
