import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import { getBreadStockStatus } from '../utils/calculations';
import { LOW_STOCK_THRESHOLD } from '../config/constants';
import { ArrowDownLeft, ArrowUpRight, ClipboardPenLine, SlidersHorizontal, Sparkles } from 'lucide-react';

export default function StockCard({
  stockData,
  onOpenEditInitialStock,
}) {
  const navigate = useNavigate();
  const currentStock = stockData?.stock ?? 0;
  const status = getBreadStockStatus(currentStock, LOW_STOCK_THRESHOLD);

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm relative overflow-hidden">
      {/* Decorative subtle background gradient */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-brand-light/10 via-transparent to-transparent rounded-full pointer-events-none -mr-16 -mt-16" />

      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-dark bg-brand-cream px-3 py-1 rounded-full border border-brand-accent/20">
              Inventaris Utama Gerai
            </span>
            <span className="text-xs text-slate-400">â€¢ Tunggal</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-800 tracking-tight">
            Stok Roti Hijau Pandan
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Basis perhitungan seluruh pesanan roti kukus dan roti bakar
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center flex-wrap gap-3">
          <button
            type="button"
            onClick={onOpenEditInitialStock}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 hover:border-brand-dark hover:bg-slate-50 text-slate-700 font-semibold text-sm transition-all shadow-xs active:scale-95"
          >
            <SlidersHorizontal className="w-4 h-4 text-slate-500" />
            <span>Ubah Stok Awal</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/catat-transaksi')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-light hover:bg-brand-lightHover text-white font-bold text-sm transition-all shadow-md active:scale-95"
          >
            <ClipboardPenLine className="w-4 h-4" />
            <span>Catat Transaksi</span>
          </button>
        </div>
      </div>

      {/* Metric Display Grid */}
      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-6 pt-6">
        {/* Main Stock Counter */}
        <div className="sm:border-r border-slate-100 sm:pr-6">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
            Sisa Stok Tersedia
          </span>
          <div className="flex items-baseline gap-3">
            <span className="text-5xl sm:text-6xl font-black text-slate-900 tracking-tight tabular-nums">
              {currentStock}
            </span>
            <span className="text-lg font-bold text-slate-500">pcs</span>
          </div>
          <div className="mt-3">
            <StatusBadge status={status} size="lg" />
          </div>
        </div>

        {/* Masuk Hari Ini */}
        <div className="sm:border-r border-slate-100 sm:px-6 flex flex-col justify-center">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">
            <div className="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <ArrowDownLeft className="w-3.5 h-3.5" />
            </div>
            <span>Masuk Hari Ini</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-800 tabular-nums">
              {stockData?.masukHariIni ?? 0}
            </span>
            <span className="text-sm font-semibold text-slate-500">pcs</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Pasokan roti siap saji</p>
        </div>

        {/* Keluar Hari Ini */}
        <div className="sm:pl-6 flex flex-col justify-center">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">
            <div className="w-6 h-6 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center">
              <ArrowUpRight className="w-3.5 h-3.5" />
            </div>
            <span>Keluar Hari Ini</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-800 tabular-nums">
              {stockData?.keluarHariIni ?? 0}
            </span>
            <span className="text-sm font-semibold text-slate-500">pcs</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Terjual ke pelanggan</p>
        </div>
      </div>
    </div>
  );
}
