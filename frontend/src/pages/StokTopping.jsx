import React, { useState, useEffect, useMemo } from 'react';
import { toppingService } from '../services/toppingService';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import { TableSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { calculateAverageRepurchaseDays } from '../utils/calculations';
import { formatDateIndo, formatDaysAgo, getTodayDateString } from '../utils/date';
import { TOPPING_STATUS, TOPPING_UNITS } from '../config/constants';
import {
  Layers,
  Plus,
  Search,
  Info,
  Calendar,
  PackageCheck,
  TrendingUp,
  AlertCircle,
  Clock,
} from 'lucide-react';

export default function StokTopping() {
  const [toppings, setToppings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search & Status Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('Semua');

  // Purchase Modal State (Pengelola Only)
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);
  const [purchaseForm, setPurchaseForm] = useState({
    toppingId: '',
    date: getTodayDateString(),
    qty: '',
    unit: 'kg',
  });
  const [purchaseError, setPurchaseError] = useState('');
  const [isSavingPurchase, setIsSavingPurchase] = useState(false);

  // Status Change State (Pengelola Only)
  const [updatingStatusId, setUpdatingStatusId] = useState(null);

  const { isPengelola, user } = useAuth();
  const { addToast } = useToast();
  const todayStr = getTodayDateString();

  const loadToppings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await toppingService.getToppings();
      setToppings(data || []);
      if (data && data.length > 0 && !purchaseForm.toppingId) {
        setPurchaseForm((prev) => ({ ...prev, toppingId: data[0].id }));
      }
    } catch (err) {
      setError(err.message || 'Gagal memuat data. Periksa koneksi lalu coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadToppings();
  }, []);

  // Filtered Toppings
  const filteredToppings = useMemo(() => {
    return toppings.filter((top) => {
      const matchSearch = top.name
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
      const matchStatus =
        statusFilter === 'Semua' ? true : top.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [toppings, searchQuery, statusFilter]);

  // Status counters
  const statusCounts = useMemo(() => {
    return {
      Semua: toppings.length,
      [TOPPING_STATUS.AMAN]: toppings.filter((t) => t.status === TOPPING_STATUS.AMAN).length,
      [TOPPING_STATUS.HAMPIR_HABIS]: toppings.filter((t) => t.status === TOPPING_STATUS.HAMPIR_HABIS).length,
      [TOPPING_STATUS.HABIS]: toppings.filter((t) => t.status === TOPPING_STATUS.HABIS).length,
    };
  }, [toppings]);

  // Handle Quick Status Change (Pengelola Only)
  const handleStatusChange = async (toppingId, newStatus) => {
    try {
      setUpdatingStatusId(toppingId);
      const updated = await toppingService.updateToppingStatus(toppingId, newStatus);
      setToppings((prev) =>
        prev.map((t) => (t.id === updated.id ? updated : t))
      );
      addToast(`Status "${updated.name}" diubah menjadi ${newStatus}`, 'success');
    } catch (err) {
      addToast(err.message || 'Gagal mengubah status topping', 'error');
    } finally {
      setUpdatingStatusId(null);
    }
  };

  // Open Catat Pembelian Modal
  const openPurchaseModal = (toppingId = '') => {
    setPurchaseForm({
      toppingId: toppingId || toppings[0]?.id || '',
      date: getTodayDateString(),
      qty: '',
      unit: 'kg',
    });
    setPurchaseError('');
    setIsPurchaseModalOpen(true);
  };

  // Save Purchase
  const handleSavePurchase = async (e) => {
    e.preventDefault();
    const qty = parseFloat(purchaseForm.qty);
    if (isNaN(qty) || qty <= 0) {
      setPurchaseError('Jumlah pembelian harus lebih dari 0');
      return;
    }

    try {
      setIsSavingPurchase(true);
      await toppingService.createToppingPurchase({
        toppingId: purchaseForm.toppingId,
        date: purchaseForm.date,
        qty,
        unit: purchaseForm.unit,
        recordedBy: user?.name || 'Budi Santoso',
      });

      // Reload toppings to refresh purchase calculations
      await loadToppings();
      setIsPurchaseModalOpen(false);
      addToast('Pembelian topping berhasil dicatat!', 'success');
    } catch (err) {
      setPurchaseError('Transaksi gagal disimpan. Silakan coba lagi.');
    } finally {
      setIsSavingPurchase(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-16 bg-white rounded-2xl animate-pulse" />
        <TableSkeleton rows={8} cols={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadToppings} />;
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Inventaris Bahan Pelengkap
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-accent/20 text-brand-accent">
              Tambahan
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-800">
            Stok Topping
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Monitoring kondisi persediaan topping, saus, dan bahan pendukung
          </p>
        </div>

        {/* Pengelola CTA */}
        {isPengelola && (
          <button
            type="button"
            onClick={() => openPurchaseModal()}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-brand-light hover:bg-brand-lightHover text-white rounded-xl text-sm font-bold shadow-sm transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>Catat Pembelian</span>
          </button>
        )}
      </div>

      {/* Crucial Business Rule Notice Banner */}
      <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 text-amber-900 flex items-start gap-3 shadow-2xs">
        <Info className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
        <div className="text-xs sm:text-sm leading-relaxed">
          <p className="font-bold">Informasi Status Topping:</p>
          <p className="mt-0.5 text-amber-800">
            Stok topping tidak dihitung otomatis. Status diisi manual oleh pengelola.
            Informasi estimasi beli ulang dihitung berdasarkan riwayat pembelian sebelumnya.
          </p>
        </div>
      </div>

      {/* Filter Toolbar: Status tabs & Search */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Status Tabs */}
          <div className="inline-flex p-1 bg-brand-cream rounded-2xl gap-1 overflow-x-auto max-w-full">
            {['Semua', TOPPING_STATUS.AMAN, TOPPING_STATUS.HAMPIR_HABIS, TOPPING_STATUS.HABIS].map(
              (status) => {
                const isActive = statusFilter === status;
                return (
                  <button
                    key={status}
                    type="button"
                    onClick={() => setStatusFilter(status)}
                    className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 ${
                      isActive
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <span>{status}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                        isActive
                          ? 'bg-brand-cream text-brand-dark'
                          : 'bg-slate-200/70 text-slate-600'
                      }`}
                    >
                      {statusCounts[status] || 0}
                    </span>
                  </button>
                );
              }
            )}
          </div>

          {/* Search Box */}
          <div className="relative w-full lg:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari nama topping..."
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
            />
          </div>
        </div>

        {/* Toppings Table */}
        {filteredToppings.length === 0 ? (
          <EmptyState
            title="Topping tidak ditemukan"
            description="Tidak ada item topping yang cocok dengan filter atau pencarian."
            action={
              <button
                type="button"
                onClick={() => {
                  setStatusFilter('Semua');
                  setSearchQuery('');
                }}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-xs font-bold text-slate-700"
              >
                Reset Filter
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-100">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-brand-creamLight border-b border-slate-100 text-slate-600 font-bold text-xs uppercase tracking-wider">
                  <th className="py-3.5 px-4 sm:px-6">Nama Topping</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Terakhir Dibeli</th>
                  <th className="py-3.5 px-4 text-right">Jumlah Terakhir</th>
                  <th className="py-3.5 px-4 text-center">Rata-rata Beli Ulang</th>
                  {isPengelola && (
                    <th className="py-3.5 px-4 sm:px-6 text-center">Aksi Cepat</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredToppings.map((top) => {
                  // Last purchase calculation
                  const sortedPurchases = top.purchases
                    ? [...top.purchases].sort(
                        (a, b) => new Date(b.date) - new Date(a.date)
                      )
                    : [];
                  const lastPurchase = sortedPurchases[0];
                  const avgRepurchase = calculateAverageRepurchaseDays(sortedPurchases);

                  return (
                    <tr
                      key={top.id}
                      className="hover:bg-slate-50/80 transition-colors group"
                    >
                      {/* Nama Topping */}
                      <td className="py-3.5 px-4 sm:px-6 font-bold text-slate-900">
                        {top.name}
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">
                        {isPengelola ? (
                          // Pengelola can change status via select
                          <select
                            value={top.status}
                            disabled={updatingStatusId === top.id}
                            onChange={(e) =>
                              handleStatusChange(top.id, e.target.value)
                            }
                            className="text-xs font-semibold px-2.5 py-1 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-1 focus:ring-brand-light cursor-pointer"
                          >
                            <option value={TOPPING_STATUS.AMAN}>Aman</option>
                            <option value={TOPPING_STATUS.HAMPIR_HABIS}>
                              Hampir Habis
                            </option>
                            <option value={TOPPING_STATUS.HABIS}>Habis</option>
                          </select>
                        ) : (
                          // Pemilik is strictly VIEW ONLY
                          <StatusBadge status={top.status} size="sm" />
                        )}
                      </td>

                      {/* Terakhir Dibeli */}
                      <td className="py-3.5 px-4 text-slate-700">
                        {lastPurchase ? (
                          <div>
                            <span className="font-semibold block text-xs sm:text-sm">
                              {formatDateIndo(lastPurchase.date)}
                            </span>
                            <span className="text-[11px] text-slate-400">
                              {formatDaysAgo(lastPurchase.date)}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>

                      {/* Jumlah Pembelian Terakhir */}
                      <td className="py-3.5 px-4 text-right font-bold text-slate-800 tabular-nums">
                        {lastPurchase ? (
                          <>
                            {lastPurchase.qty}{' '}
                            <span className="text-xs font-normal text-slate-500">
                              {lastPurchase.unit}
                            </span>
                          </>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>

                      {/* Rata-rata Beli Ulang */}
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-block px-2.5 py-0.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700">
                          {sortedPurchases.length < 2 ? '-' : avgRepurchase}
                        </span>
                      </td>

                      {/* Pengelola Aksi Tambah Pembelian Khusus */}
                      {isPengelola && (
                        <td className="py-3.5 px-4 sm:px-6 text-center">
                          <button
                            type="button"
                            onClick={() => openPurchaseModal(top.id)}
                            className="px-2.5 py-1 text-xs font-semibold text-brand-dark hover:bg-brand-cream rounded-lg transition-colors border border-transparent hover:border-brand-accent/20"
                          >
                            + Beli Lagi
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Catat Pembelian Topping (Pengelola Only) */}
      {isPengelola && (
        <Modal
          isOpen={isPurchaseModalOpen}
          onClose={() => setIsPurchaseModalOpen(false)}
          title="Catat Pembelian Topping"
        >
          <form onSubmit={handleSavePurchase} className="space-y-4">
            {purchaseError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
                <span>{purchaseError}</span>
              </div>
            )}

            {/* Pilihan Topping */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Nama Topping
              </label>
              <select
                value={purchaseForm.toppingId}
                onChange={(e) =>
                  setPurchaseForm({ ...purchaseForm, toppingId: e.target.value })
                }
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-medium bg-white"
                required
              >
                {toppings.map((top) => (
                  <option key={top.id} value={top.id}>
                    {top.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Tanggal Beli */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Tanggal Pembelian</span>
              </label>
              <input
                type="date"
                value={purchaseForm.date}
                max={todayStr}
                onChange={(e) =>
                  setPurchaseForm({ ...purchaseForm, date: e.target.value })
                }
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
                required
              />
            </div>

            {/* Jumlah & Satuan */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Jumlah <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="any"
                  min="0.1"
                  value={purchaseForm.qty}
                  onChange={(e) => {
                    setPurchaseForm({ ...purchaseForm, qty: e.target.value });
                    if (purchaseError) setPurchaseError('');
                  }}
                  placeholder="Contoh: 5"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-bold"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Satuan
                </label>
                <select
                  value={purchaseForm.unit}
                  onChange={(e) =>
                    setPurchaseForm({ ...purchaseForm, unit: e.target.value })
                  }
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-medium bg-white"
                >
                  {TOPPING_UNITS.map((unit) => (
                    <option key={unit} value={unit}>
                      {unit}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsPurchaseModalOpen(false)}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100"
              >
                Batal
              </button>
              <button
                type="submit"
                disabled={isSavingPurchase}
                className="px-5 py-2 rounded-xl bg-brand-light hover:bg-brand-lightHover text-white text-sm font-bold flex items-center gap-2"
              >
                {isSavingPurchase && (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                )}
                <span>Simpan Pembelian</span>
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
