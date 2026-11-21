import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { stockService } from '../services/stockService';
import { menuService } from '../services/menuService';
import { transactionService } from '../services/transactionService';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import MenuCard from '../components/MenuCard';
import StatusBadge from '../components/StatusBadge';
import { getBreadStockStatus } from '../utils/calculations';
import { getTodayDateString } from '../utils/date';
import {
  MENU_CATEGORIES,
  COOKING_METHODS,
  ENTRY_SESSIONS,
  LOW_STOCK_THRESHOLD,
} from '../config/constants';
import { CardSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import {
  ArrowDownLeft,
  ArrowUpRight,
  Search,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Calendar,
  Utensils,
  Clock,
  FileText,
  Boxes,
} from 'lucide-react';

export default function CatatTransaksi() {
  const [activeTab, setActiveTab] = useState('keluar'); // 'keluar' | 'masuk'
  const [stockData, setStockData] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Form states - Barang Keluar
  const [quantities, setQuantities] = useState({});
  const [cookingMethod, setCookingMethod] = useState('');
  const [keluarDate, setKeluarDate] = useState(getTodayDateString());
  const [keluarNote, setKeluarNote] = useState('');
  const [keluarSearch, setKeluarSearch] = useState('');

  // Form states - Barang Masuk
  const [masukQty, setMasukQty] = useState('');
  const [masukSession, setMasukSession] = useState('Sesi 1');
  const [masukDate, setMasukDate] = useState(getTodayDateString());
  const [masukNote, setMasukNote] = useState('');

  // Submission feedback states
  const [validationError, setValidationError] = useState('');
  const [serverError, setServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { user } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const todayStr = getTodayDateString();

  const loadData = async () => {
    try {
      setLoading(true);
      setFetchError(null);
      const [stockRes, menuRes] = await Promise.all([
        stockService.getBreadStock(),
        menuService.getMenuItems(),
      ]);
      setStockData(stockRes);
      setMenuItems(menuRes);
    } catch (err) {
      setFetchError(err.message || 'Gagal memuat data. Periksa koneksi lalu coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Sort and group menus: Best Seller first, then Baru, then name
  const sortMenuFn = (a, b) => {
    if (a.tag === 'Best Seller' && b.tag !== 'Best Seller') return -1;
    if (b.tag === 'Best Seller' && a.tag !== 'Best Seller') return 1;
    if (a.tag === 'Baru' && b.tag !== 'Baru') return -1;
    if (b.tag === 'Baru' && a.tag !== 'Baru') return 1;
    return a.name.localeCompare(b.name);
  };

  const filteredMenus = useMemo(() => {
    const q = keluarSearch.toLowerCase();
    const filtered = menuItems.filter((item) =>
      item.name.toLowerCase().includes(q)
    );

    return {
      [MENU_CATEGORIES.ROTI_MANIS]: filtered
        .filter((m) => m.category === MENU_CATEGORIES.ROTI_MANIS)
        .sort(sortMenuFn),
      [MENU_CATEGORIES.ROTI_ASIN]: filtered
        .filter((m) => m.category === MENU_CATEGORIES.ROTI_ASIN)
        .sort(sortMenuFn),
      [MENU_CATEGORIES.TAMBAHAN]: filtered
        .filter((m) => m.category === MENU_CATEGORIES.TAMBAHAN)
        .sort(sortMenuFn),
    };
  }, [menuItems, keluarSearch]);

  // Selected items breakdown
  const selectedItems = useMemo(() => {
    return Object.entries(quantities)
      .filter(([_, qty]) => qty > 0)
      .map(([id, qty]) => {
        const item = menuItems.find((m) => m.id === id);
        return {
          menuItemId: id,
          name: item ? item.name : 'Unknown',
          category: item ? item.category : 'Roti Manis',
          qty,
          isTambahan: item?.category === MENU_CATEGORIES.TAMBAHAN,
        };
      });
  }, [quantities, menuItems]);

  // Total bread reduction (Roti Manis + Roti Asin only)
  const totalBreadOut = useMemo(() => {
    return selectedItems
      .filter((item) => !item.isTambahan)
      .reduce((sum, item) => sum + item.qty, 0);
  }, [selectedItems]);

  const currentStock = stockData?.stock ?? 0;
  const stockAfterKeluar = currentStock - totalBreadOut;

  // Masuk calculations
  const parsedMasukQty = parseInt(masukQty, 10) || 0;
  const stockAfterMasuk = currentStock + parsedMasukQty;

  const handleQuantityChange = (id, newQty) => {
    setQuantities((prev) => ({
      ...prev,
      [id]: Math.max(0, newQty),
    }));
    // Clear validation error on change
    if (validationError) setValidationError('');
    if (serverError) setServerError('');
  };

  // Submit Barang Keluar
  const handleSubmitKeluar = async (e) => {
    e.preventDefault();
    setValidationError('');
    setServerError('');

    // Rule 1: Minimal 1 menu
    if (selectedItems.length === 0 || totalBreadOut + selectedItems.filter(i => i.isTambahan).reduce((a,b)=>a+b.qty,0) <= 0) {
      setValidationError('Pilih minimal satu menu');
      return;
    }

    // Rule 2: Total roti keluar tidak boleh melebihi stok
    if (totalBreadOut > currentStock) {
      setValidationError(
        `Stok roti tidak mencukupi. Stok tersedia: ${currentStock}, jumlah diminta: ${totalBreadOut}.`
      );
      return;
    }

    try {
      setIsSubmitting(true);
      const payload = {
        type: 'keluar',
        date: keluarDate,
        cookingMethod: cookingMethod || '-',
        note: keluarNote.trim(),
        items: selectedItems.map((i) => ({ menuItemId: i.menuItemId, qty: i.qty })),
        recordedBy: user?.name || 'Budi Santoso',
      };

      const res = await transactionService.createTransaction(payload);
      addToast(
        `Transaksi berhasil disimpan. Stok saat ini: ${res.currentStock} pcs`,
        'success',
        5000
      );
      navigate('/daftar-stok');
    } catch (err) {
      if (err.code === 'INSUFFICIENT_STOCK') {
        setValidationError(err.message);
      } else {
        setServerError('Transaksi gagal disimpan. Silakan coba lagi.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Barang Masuk
  const handleSubmitMasuk = async (e) => {
    e.preventDefault();
    setValidationError('');
    setServerError('');

    if (parsedMasukQty <= 0) {
      setValidationError('Jumlah harus lebih dari 0');
      return;
    }

    try {
      setIsSubmitting(true);
      const payload = {
        type: 'masuk',
        date: masukDate,
        session: masukSession,
        qty: parsedMasukQty,
        note: masukNote.trim(),
        recordedBy: user?.name || 'Budi Santoso',
      };

      const res = await transactionService.createTransaction(payload);
      addToast(
        `Transaksi berhasil disimpan. Stok saat ini: ${res.currentStock} pcs`,
        'success',
        5000
      );
      navigate('/daftar-stok');
    } catch (err) {
      setServerError('Transaksi gagal disimpan. Silakan coba lagi.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <CardSkeleton />
        <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-10 bg-slate-100 rounded-xl animate-pulse" />
            <div className="h-10 bg-slate-100 rounded-xl animate-pulse" />
            <div className="h-10 bg-slate-100 rounded-xl animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-32 bg-white rounded-2xl border border-slate-200/80 p-4 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (fetchError) {
    return <ErrorState message={fetchError} onRetry={loadData} />;
  }

  return (
    <div className="space-y-6 pb-24">
      {/* Header & Stock Summary Banner */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Pencatatan Stok Harian
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-800">
            Catat Transaksi
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Pencatatan barang keluar (penjualan) & barang masuk (pasokan siap saji)
          </p>
        </div>

        {/* Live Bread Stock Pill */}
        <div className="flex items-center gap-3 bg-brand-creamLight p-3.5 rounded-2xl border border-slate-200/70">
          <div className="w-10 h-10 rounded-xl bg-brand-dark text-white flex items-center justify-center">
            <Boxes className="w-5 h-5 text-brand-light" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500">Stok Roti Saat Ini:</span>
              <StatusBadge status={getBreadStockStatus(currentStock, LOW_STOCK_THRESHOLD)} size="sm" />
            </div>
            <p className="text-xl font-black text-slate-900 tabular-nums">
              {currentStock} <span className="text-xs font-bold text-slate-500">pcs</span>
            </p>
          </div>
        </div>
      </div>

      {/* Main Mode Tabs: Barang Keluar vs Barang Masuk */}
      <div className="flex p-1.5 bg-brand-cream rounded-2xl max-w-md shadow-xs">
        <button
          type="button"
          onClick={() => {
            setActiveTab('keluar');
            setValidationError('');
            setServerError('');
          }}
          className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${
            activeTab === 'keluar'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <ArrowUpRight className="w-4 h-4 text-amber-600" />
          <span>Barang Keluar (Penjualan)</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('masuk');
            setValidationError('');
            setServerError('');
          }}
          className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${
            activeTab === 'masuk'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <ArrowDownLeft className="w-4 h-4 text-emerald-600" />
          <span>Barang Masuk (Pasokan)</span>
        </button>
      </div>

      {/* ERROR FEEDBACK BANNERS */}
      {/* 1. Validation Error (e.g. Stok tidak mencukupi / Minimal 1 menu) */}
      {validationError && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 text-sm flex items-start gap-3 shadow-sm animate-shake">
          <AlertCircle className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
          <div>
            <p className="font-bold">Peringatan Validasi Form</p>
            <p className="mt-0.5 leading-relaxed">{validationError}</p>
          </div>
        </div>
      )}

      {/* 2. Server Connection Error (Visually distinct red alert) */}
      {serverError && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-300 text-red-900 text-sm flex items-start gap-3 shadow-sm">
          <AlertTriangle className="w-5 h-5 shrink-0 text-red-600 mt-0.5" />
          <div>
            <p className="font-bold">Kegagalan Sistem</p>
            <p className="mt-0.5 leading-relaxed">{serverError}</p>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 1: BARANG KELUAR */}
      {/* ======================================================== */}
      {activeTab === 'keluar' && (
        <form onSubmit={handleSubmitKeluar} className="space-y-6">
          {/* Controls Bar: Tanggal, Cara Masak, Catatan */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-dark" />
              <span>Detail Transaksi Keluar</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
              {/* Tanggal Transaksi */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>Tanggal Transaksi</span>
                </label>
                <input
                  type="date"
                  value={keluarDate}
                  max={todayStr}
                  onChange={(e) => setKeluarDate(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-semibold bg-slate-50/50"
                  required
                />
              </div>

              {/* Cara Masak (Kukus | Bakar) */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <Utensils className="w-3.5 h-3.5 text-slate-400" />
                  <span>Cara Masak (Opsional)</span>
                </label>
                <div className="flex items-center gap-2">
                  {COOKING_METHODS.map((method) => {
                    const isSelected = cookingMethod === method;
                    return (
                      <button
                        key={method}
                        type="button"
                        onClick={() =>
                          setCookingMethod(isSelected ? '' : method)
                        }
                        className={`flex-1 py-2.5 px-3 rounded-xl text-xs font-bold border transition-all ${
                          isSelected
                            ? 'bg-brand-dark text-white border-brand-dark shadow-xs'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                      >
                        {method}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Catatan Transaksi */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  <span>Catatan Khusus (Opsional)</span>
                </label>
                <input
                  type="text"
                  value={keluarNote}
                  onChange={(e) => setKeluarNote(e.target.value)}
                  placeholder="Contoh: Pesanan katering, bungkus pisah"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
                />
              </div>
            </div>
          </div>

          {/* Search bar for quick filter */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={keluarSearch}
              onChange={(e) => setKeluarSearch(e.target.value)}
              placeholder="Cari nama roti atau varian cepat..."
              className="w-full pl-11 pr-4 py-3 rounded-2xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-brand-light text-sm shadow-xs"
            />
          </div>

          {/* Grouped Menu Cards */}
          {/* Section 1: Roti Manis */}
          {filteredMenus[MENU_CATEGORIES.ROTI_MANIS].length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <h3 className="text-lg font-bold text-slate-800">Roti Manis</h3>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 font-semibold">
                    {filteredMenus[MENU_CATEGORIES.ROTI_MANIS].length} Menu
                  </span>
                </div>
                <span className="text-xs text-slate-400 hidden sm:inline">
                  Setiap porsi memotong 1 pcs stok roti
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {filteredMenus[MENU_CATEGORIES.ROTI_MANIS].map((item) => (
                  <MenuCard
                    key={item.id}
                    item={item}
                    quantity={quantities[item.id] || 0}
                    onChange={(qty) => handleQuantityChange(item.id, qty)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Section 2: Roti Asin */}
          {filteredMenus[MENU_CATEGORIES.ROTI_ASIN].length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
                  <h3 className="text-lg font-bold text-slate-800">Roti Asin</h3>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-orange-100 text-orange-900 font-semibold">
                    {filteredMenus[MENU_CATEGORIES.ROTI_ASIN].length} Menu
                  </span>
                </div>
                <span className="text-xs text-slate-400 hidden sm:inline">
                  Setiap porsi memotong 1 pcs stok roti
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {filteredMenus[MENU_CATEGORIES.ROTI_ASIN].map((item) => (
                  <MenuCard
                    key={item.id}
                    item={item}
                    quantity={quantities[item.id] || 0}
                    onChange={(qty) => handleQuantityChange(item.id, qty)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Section 3: Tambahan */}
          {filteredMenus[MENU_CATEGORIES.TAMBAHAN].length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <h3 className="text-lg font-bold text-slate-800">Tambahan (Topping)</h3>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-900 font-semibold">
                    {filteredMenus[MENU_CATEGORIES.TAMBAHAN].length} Item
                  </span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                  <span>Tambahan tidak mengurangi stok roti.</span>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {filteredMenus[MENU_CATEGORIES.TAMBAHAN].map((item) => (
                  <MenuCard
                    key={item.id}
                    item={item}
                    quantity={quantities[item.id] || 0}
                    onChange={(qty) => handleQuantityChange(item.id, qty)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State when search returns 0 items */}
          {filteredMenus[MENU_CATEGORIES.ROTI_MANIS].length === 0 &&
            filteredMenus[MENU_CATEGORIES.ROTI_ASIN].length === 0 &&
            filteredMenus[MENU_CATEGORIES.TAMBAHAN].length === 0 && (
              <EmptyState
                title="Menu tidak ditemukan"
                description="Tidak ada menu roti atau varian yang cocok dengan pencarian Anda."
                action={
                  <button
                    type="button"
                    onClick={() => setKeluarSearch('')}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-xs font-bold text-slate-700"
                  >
                    Reset Pencarian
                  </button>
                }
              />
            )}

          {/* STICKY BOTTOM SUMMARY BAR */}
          <div className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200/90 shadow-2xl p-4 sm:px-8">
            <div className="max-w-7xl mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Ringkasan Catatan List (Menus with qty > 0) */}
              <div className="flex-1 overflow-x-auto">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Ringkasan Catatan:
                  </span>
                  <span className="text-[11px] text-slate-400">
                    ({selectedItems.length} menu dipilih)
                  </span>
                </div>

                {selectedItems.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">
                    Belum ada menu yang dipilih. Atur kuantitas pada kartu menu di atas.
                  </p>
                ) : (
                  <div className="flex items-center gap-2 flex-nowrap py-1">
                    {selectedItems.map((item) => (
                      <span
                        key={item.menuItemId}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold shrink-0 ${
                          item.isTambahan
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : 'bg-brand-cream text-slate-800 border border-brand-accent/20'
                        }`}
                      >
                        <span>{item.name}</span>
                        <span className="font-black bg-white px-1.5 py-0.2 rounded-md shadow-2xs">
                          Ã—{item.qty}
                        </span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Total calculations & Submit button */}
              <div className="flex items-center justify-between sm:justify-end gap-6 border-t lg:border-t-0 pt-3 lg:pt-0 shrink-0">
                <div className="text-right">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                    Total Roti Keluar
                  </span>
                  <div className="text-lg font-black text-slate-900 tabular-nums">
                    {totalBreadOut}{' '}
                    <span className="text-xs font-semibold text-slate-500">pcs</span>
                  </div>
                </div>

                <div className="text-right pl-4 border-l border-slate-200">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                    Stok Setelah Transaksi
                  </span>
                  <div
                    className={`text-lg font-black tabular-nums ${
                      stockAfterKeluar < 0
                        ? 'text-red-600 font-extrabold animate-pulse'
                        : 'text-brand-dark'
                    }`}
                  >
                    {stockAfterKeluar}{' '}
                    <span className="text-xs font-semibold text-slate-500">pcs</span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || selectedItems.length === 0}
                  className="px-6 py-3 bg-brand-light hover:bg-brand-lightHover disabled:opacity-50 disabled:pointer-events-none text-white font-bold text-sm rounded-xl transition-all shadow-md active:scale-95 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4" />
                  )}
                  <span>Simpan Transaksi</span>
                </button>
              </div>
            </div>
          </div>
        </form>
      )}

      {/* ======================================================== */}
      {/* TAB 2: BARANG MASUK */}
      {/* ======================================================== */}
      {activeTab === 'masuk' && (
        <div className="max-w-2xl bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm">
          <div className="mb-6 pb-4 border-b border-slate-100">
            <h3 className="text-xl font-bold text-slate-800">
              Catat Pasokan Roti Masuk
            </h3>
            <p className="text-sm text-slate-500 mt-0.5">
              Masukkan total roti kukus pandan segar yang disiapkan dari dapur
            </p>
          </div>

          <form onSubmit={handleSubmitMasuk} className="space-y-5">
            {/* Jumlah Roti Masuk */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Jumlah Roti Masuk (pcs) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min="1"
                value={masukQty}
                onChange={(e) => {
                  setMasukQty(e.target.value);
                  if (validationError) setValidationError('');
                  if (serverError) setServerError('');
                }}
                placeholder="Contoh: 50"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-base font-bold tabular-nums"
                required
              />
              <p className="text-xs text-slate-400 mt-1">
                Jumlah harus lebih dari 0 dan dalam satuan pcs.
              </p>
            </div>

            {/* Sesi Pasokan */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Sesi Pasokan
              </label>
              <div className="grid grid-cols-3 gap-2.5">
                {ENTRY_SESSIONS.map((session) => (
                  <button
                    key={session}
                    type="button"
                    onClick={() => setMasukSession(session)}
                    className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all ${
                      masukSession === session
                        ? 'bg-brand-dark text-white border-brand-dark shadow-sm'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    {session}
                  </button>
                ))}
              </div>
            </div>

            {/* Tanggal */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Tanggal</span>
              </label>
              <input
                type="date"
                value={masukDate}
                max={todayStr}
                onChange={(e) => setMasukDate(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-semibold bg-slate-50/50"
                required
              />
            </div>

            {/* Catatan */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                <span>Catatan Tambahan (Opsional)</span>
              </label>
              <textarea
                value={masukNote}
                onChange={(e) => setMasukNote(e.target.value)}
                placeholder="Contoh: Kondisi pasokan hangat, batch adonan kedua"
                rows="3"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
              />
            </div>

            {/* Live Calculation Preview Card */}
            <div className="p-4 rounded-2xl bg-brand-creamLight border border-slate-200/80 grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                  Stok Saat Ini
                </span>
                <span className="text-xl font-bold text-slate-800 tabular-nums">
                  {currentStock} pcs
                </span>
              </div>
              <div className="border-l border-slate-200 pl-4">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                  Stok Setelah Transaksi
                </span>
                <span className="text-xl font-black text-brand-dark tabular-nums">
                  {stockAfterMasuk} pcs
                </span>
              </div>
            </div>

            {/* Submit button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting || parsedMasukQty <= 0}
                className="w-full py-3.5 bg-brand-light hover:bg-brand-lightHover disabled:opacity-50 text-white font-bold text-sm rounded-xl transition-all shadow-md active:scale-95 flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                <span>Simpan Transaksi Masuk</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
