import React, { useState, useEffect, useMemo } from 'react';
import { transactionService } from '../services/transactionService';
import { toppingService } from '../services/toppingService';
import { TableSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { formatDateIndo, formatDateTimeIndo } from '../utils/date';
import {
  History,
  Search,
  Filter,
  Calendar,
  ArrowUpRight,
  ArrowDownLeft,
  ShoppingBag,
  ChevronLeft,
  ChevronRight,
  User,
  Layers,
} from 'lucide-react';

export default function RiwayatTransaksi() {
  const [activeTab, setActiveTab] = useState('roti'); // 'roti' | 'topping'

  // Transaksi Roti State
  const [transactions, setTransactions] = useState([]);
  const [totalTrx, setTotalTrx] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loadingRoti, setLoadingRoti] = useState(true);
  const [errorRoti, setErrorRoti] = useState(null);

  // Filters for Roti
  const [filterType, setFilterType] = useState('Semua'); // 'Semua' | 'masuk' | 'keluar'
  const [filterFrom, setFilterFrom] = useState('');
  const [filterTo, setFilterTo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Pembelian Topping State
  const [toppingPurchases, setToppingPurchases] = useState([]);
  const [loadingTopping, setLoadingTopping] = useState(true);
  const [errorTopping, setErrorTopping] = useState(null);
  const [toppingSearch, setToppingSearch] = useState('');

  // Load Transaksi Roti
  const loadTransactions = async () => {
    try {
      setLoadingRoti(true);
      setErrorRoti(null);
      const res = await transactionService.getTransactions({
        type: filterType,
        from: filterFrom,
        to: filterTo,
        q: searchQuery,
        page: currentPage,
        limit: 8,
      });
      setTransactions(res.items || []);
      setTotalTrx(res.total || 0);
      setTotalPages(res.totalPages || 1);
    } catch (err) {
      setErrorRoti(err.message || 'Gagal memuat data. Periksa koneksi lalu coba lagi.');
    } finally {
      setLoadingRoti(false);
    }
  };

  // Load Pembelian Topping
  const loadToppingPurchases = async () => {
    try {
      setLoadingTopping(true);
      setErrorTopping(null);
      const data = await toppingService.getToppingPurchases();
      setToppingPurchases(data || []);
    } catch (err) {
      setErrorTopping(err.message || 'Gagal memuat data. Periksa koneksi lalu coba lagi.');
    } finally {
      setLoadingTopping(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [filterType, filterFrom, filterTo, searchQuery, currentPage]);

  useEffect(() => {
    if (activeTab === 'topping') {
      loadToppingPurchases();
    }
  }, [activeTab]);

  // Summary Metrics
  const summaryMetrics = useMemo(() => {
    const totalMasuk = transactions
      .filter((t) => t.type === 'masuk')
      .reduce((sum, t) => sum + (t.totalQty || 0), 0);
    const totalKeluar = transactions
      .filter((t) => t.type === 'keluar')
      .reduce((sum, t) => sum + (t.totalQty || 0), 0);

    return {
      totalMasuk,
      totalKeluar,
      count: totalTrx,
    };
  }, [transactions, totalTrx]);

  // Filtered topping purchases
  const filteredToppingPurchases = useMemo(() => {
    if (!toppingSearch.trim()) return toppingPurchases;
    const q = toppingSearch.toLowerCase();
    return toppingPurchases.filter(
      (p) =>
        p.toppingName?.toLowerCase().includes(q) ||
        p.recordedBy?.toLowerCase().includes(q) ||
        p.unit?.toLowerCase().includes(q)
    );
  }, [toppingPurchases, toppingSearch]);

  const resetFilters = () => {
    setFilterType('Semua');
    setFilterFrom('');
    setFilterTo('');
    setSearchQuery('');
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Audit & Laporan Gerai
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-800">
            Riwayat Transaksi
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Log lengkap pergerakan stok roti hijau pandan dan pembelian topping
          </p>
        </div>

        {/* Tab switch between Roti and Topping */}
        <div className="flex p-1.5 bg-brand-cream rounded-2xl shadow-xs">
          <button
            type="button"
            onClick={() => setActiveTab('roti')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center gap-2 ${
              activeTab === 'roti'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <History className="w-4 h-4 text-brand-dark" />
            <span>Transaksi Roti</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('topping')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center gap-2 ${
              activeTab === 'topping'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-4 h-4 text-brand-accent" />
            <span>Pembelian Topping</span>
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* TAB 1: TRANSAKSI ROTI */}
      {/* ======================================================== */}
      {activeTab === 'roti' && (
        <div className="space-y-6">
          {/* Quick Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-brand-cream flex items-center justify-center text-brand-dark">
                <History className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Total Transaksi
                </p>
                <p className="text-2xl font-black text-slate-900 tabular-nums">
                  {summaryMetrics.count}{' '}
                  <span className="text-xs font-semibold text-slate-500">record</span>
                </p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                <ArrowDownLeft className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Roti Masuk (Halaman Ini)
                </p>
                <p className="text-2xl font-black text-emerald-700 tabular-nums">
                  +{summaryMetrics.totalMasuk}{' '}
                  <span className="text-xs font-semibold text-slate-500">pcs</span>
                </p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
                <ArrowUpRight className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Roti Keluar (Halaman Ini)
                </p>
                <p className="text-2xl font-black text-amber-700 tabular-nums">
                  -{summaryMetrics.totalKeluar}{' '}
                  <span className="text-xs font-semibold text-slate-500">pcs</span>
                </p>
              </div>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Type Segment Control */}
              <div className="inline-flex p-1 bg-brand-cream rounded-xl gap-1">
                {['Semua', 'masuk', 'keluar'].map((type) => {
                  const label =
                    type === 'Semua'
                      ? 'Semua Transaksi'
                      : type === 'masuk'
                      ? 'Barang Masuk'
                      : 'Barang Keluar';
                  const isActive = filterType === type;
                  return (
                    <button
                      key={type}
                      type="button"
                      onClick={() => {
                        setFilterType(type);
                        setCurrentPage(1);
                      }}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        isActive
                          ? 'bg-white text-slate-900 shadow-sm'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>

              {/* Date Range Inputs & Clear Button */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-500">Dari:</span>
                  <input
                    type="date"
                    value={filterFrom}
                    onChange={(e) => {
                      setFilterFrom(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-500">Sampai:</span>
                  <input
                    type="date"
                    value={filterTo}
                    onChange={(e) => {
                      setFilterTo(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50"
                  />
                </div>

                {(filterFrom || filterTo || filterType !== 'Semua' || searchQuery) && (
                  <button
                    type="button"
                    onClick={resetFilters}
                    className="px-3 py-1.5 text-xs font-bold text-red-600 hover:bg-red-50 rounded-xl"
                  >
                    Reset Filter
                  </button>
                )}
              </div>
            </div>

            {/* Keyword Search */}
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Cari rincian menu, catatan, atau nama staf..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
              />
            </div>
          </div>

          {/* Table or Empty/Error State */}
          {loadingRoti ? (
            <TableSkeleton rows={8} cols={7} />
          ) : errorRoti ? (
            <ErrorState message={errorRoti} onRetry={loadTransactions} />
          ) : transactions.length === 0 ? (
            <EmptyState
              title="Belum ada transaksi"
              description="Tidak ada catatan transaksi yang sesuai dengan filter pencarian Anda."
              action={
                <button
                  type="button"
                  onClick={resetFilters}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-xs font-bold text-slate-700"
                >
                  Kembalikan Filter
                </button>
              }
            />
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-brand-creamLight border-b border-slate-100 text-slate-600 font-bold text-xs uppercase tracking-wider">
                      <th className="py-3.5 px-4 sm:px-6">Tanggal & Waktu</th>
                      <th className="py-3.5 px-4">Jenis</th>
                      <th className="py-3.5 px-4 text-right">Total Roti</th>
                      <th className="py-3.5 px-4">Rincian Menu / Pasokan</th>
                      <th className="py-3.5 px-4 text-center">Cara Masak</th>
                      <th className="py-3.5 px-4 text-right">Stok Akhir</th>
                      <th className="py-3.5 px-4 sm:px-6">Dicatat Oleh</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {transactions.map((trx) => (
                      <tr
                        key={trx.id}
                        className="hover:bg-slate-50/80 transition-colors"
                      >
                        {/* Tanggal & Waktu */}
                        <td className="py-3.5 px-4 sm:px-6 font-semibold text-slate-800 whitespace-nowrap">
                          {formatDateTimeIndo(trx.datetime)}
                        </td>

                        {/* Jenis Badge */}
                        <td className="py-3.5 px-4">
                          {trx.type === 'masuk' ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                              <ArrowDownLeft className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Masuk</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300">
                              <ArrowUpRight className="w-3.5 h-3.5 text-amber-600" />
                              <span>Keluar</span>
                            </span>
                          )}
                        </td>

                        {/* Total Roti */}
                        <td className="py-3.5 px-4 text-right font-black tabular-nums whitespace-nowrap">
                          <span
                            className={
                              trx.type === 'masuk'
                                ? 'text-emerald-700'
                                : 'text-slate-900'
                            }
                          >
                            {trx.type === 'masuk' ? `+${trx.totalQty}` : `-${trx.totalQty}`}{' '}
                            <span className="text-xs font-normal text-slate-500">pcs</span>
                          </span>
                        </td>

                        {/* Rincian Menu */}
                        <td className="py-3.5 px-4 text-slate-700 max-w-xs">
                          <p className="font-medium text-xs sm:text-sm line-clamp-2">
                            {trx.details}
                          </p>
                          {trx.note && (
                            <p className="text-[11px] text-slate-400 italic mt-0.5">
                              Catatan: {trx.note}
                            </p>
                          )}
                        </td>

                        {/* Cara Masak */}
                        <td className="py-3.5 px-4 text-center">
                          {trx.cookingMethod && trx.cookingMethod !== '-' ? (
                            <span className="inline-block px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                              {trx.cookingMethod}
                            </span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>

                        {/* Stok Setelah Transaksi */}
                        <td className="py-3.5 px-4 text-right font-bold text-brand-dark tabular-nums whitespace-nowrap">
                          {trx.stockAfter ?? '-'}{' '}
                          <span className="text-xs font-normal text-slate-500">pcs</span>
                        </td>

                        {/* Dicatat Oleh */}
                        <td className="py-3.5 px-4 sm:px-6 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-[10px] font-bold">
                              <User className="w-3.5 h-3.5" />
                            </div>
                            <span className="text-xs font-semibold text-slate-800">
                              {trx.recordedBy || 'Budi Santoso'}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-brand-creamLight text-xs">
                <span className="text-slate-500 font-medium">
                  Menampilkan {transactions.length} dari {totalTrx} transaksi
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="font-bold text-slate-700 px-2">
                    Halaman {currentPage} dari {totalPages}
                  </span>
                  <button
                    type="button"
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: PEMBELIAN TOPPING */}
      {/* ======================================================== */}
      {activeTab === 'topping' && (
        <div className="space-y-6">
          {/* Search bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div className="relative w-full max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={toppingSearch}
                onChange={(e) => setToppingSearch(e.target.value)}
                placeholder="Cari nama topping atau satuan..."
                className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
              />
            </div>
            <span className="text-xs font-semibold text-slate-500 hidden sm:inline">
              Total {filteredToppingPurchases.length} riwayat pembelian
            </span>
          </div>

          {loadingTopping ? (
            <TableSkeleton rows={6} cols={5} />
          ) : errorTopping ? (
            <ErrorState message={errorTopping} onRetry={loadToppingPurchases} />
          ) : filteredToppingPurchases.length === 0 ? (
            <EmptyState
              title="Belum ada riwayat pembelian topping"
              description="Catatan belanja bahan dan topping akan muncul di sini."
            />
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-brand-creamLight border-b border-slate-100 text-slate-600 font-bold text-xs uppercase tracking-wider">
                      <th className="py-3.5 px-4 sm:px-6">Tanggal Beli</th>
                      <th className="py-3.5 px-4">Nama Topping</th>
                      <th className="py-3.5 px-4 text-right">Jumlah</th>
                      <th className="py-3.5 px-4">Satuan</th>
                      <th className="py-3.5 px-4 sm:px-6">Dicatat Oleh</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredToppingPurchases.map((purchase) => (
                      <tr
                        key={purchase.id}
                        className="hover:bg-slate-50/80 transition-colors"
                      >
                        <td className="py-3.5 px-4 sm:px-6 font-semibold text-slate-800">
                          {formatDateIndo(purchase.date)}
                        </td>
                        <td className="py-3.5 px-4 font-bold text-slate-900">
                          {purchase.toppingName}
                        </td>
                        <td className="py-3.5 px-4 text-right font-black text-slate-900 tabular-nums">
                          {purchase.qty}
                        </td>
                        <td className="py-3.5 px-4 text-slate-600">
                          <span className="inline-block px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700">
                            {purchase.unit}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 sm:px-6">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-[10px] font-bold">
                              <User className="w-3.5 h-3.5" />
                            </div>
                            <span className="text-xs font-semibold text-slate-800">
                              {purchase.recordedBy || 'Budi Santoso'}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
