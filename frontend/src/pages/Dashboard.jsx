import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { dashboardService } from '../services/dashboardService';
import StatusBadge from '../components/StatusBadge';
import { CardSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import { getBreadStockStatus } from '../utils/calculations';
import { formatDateTimeIndo } from '../utils/date';
import { LOW_STOCK_THRESHOLD } from '../config/constants';
import {
  Boxes,
  ArrowDownLeft,
  ArrowUpRight,
  TrendingUp,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';

export default function Dashboard() {
  const [summaryData, setSummaryData] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [summaryError, setSummaryError] = useState(null);

  // AI Summary State (Independent Loading & Error Handling)
  const [aiData, setAiData] = useState(null);
  const [loadingAi, setLoadingAi] = useState(true);
  const [aiError, setAiError] = useState(null);

  // Dev Switch triggered strictly by URL parameter ?simulateAiFail=1
  const [searchParams] = useSearchParams();
  const simulateAiFail = searchParams.get('simulateAiFail') === '1';

  const navigate = useNavigate();

  // Load Main Dashboard Summary
  const loadSummary = async () => {
    try {
      setLoadingSummary(true);
      setSummaryError(null);
      const data = await dashboardService.getSummary();
      setSummaryData(data);
    } catch (err) {
      setSummaryError(err.message || 'Gagal memuat data. Periksa koneksi lalu coba lagi.');
    } finally {
      setLoadingSummary(false);
    }
  };

  // Load AI Summary Independently
  const loadAiSummary = async (shouldFail) => {
    try {
      setLoadingAi(true);
      setAiError(null);
      const data = await dashboardService.getAiSummary(shouldFail);
      setAiData(data);
    } catch (err) {
      setAiError(
        'Layanan AI tidak tersedia. Stok dan riwayat transaksi tetap dapat dilihat.'
      );
    } finally {
      setLoadingAi(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    loadAiSummary(simulateAiFail);
  }, [simulateAiFail]);

  if (loadingSummary) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (summaryError) {
    return <ErrorState message={summaryError} onRetry={loadSummary} />;
  }

  const currentStock = summaryData?.stock ?? 0;
  const status = getBreadStockStatus(currentStock, LOW_STOCK_THRESHOLD);
  const chartData = summaryData?.topSales || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Panel Pengawasan Eksekutif
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              View-Only
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-800">
            Dashboard Pemilik
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Monitoring performa perputaran stok roti hijau pandan & analitik penjualan hari ini
          </p>
        </div>

        {/* Status Indicator */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-2xl bg-brand-cream border border-brand-accent/20 text-xs font-semibold text-slate-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Sistem Berjalan Normal</span>
        </div>
      </div>

      {/* 1. Main 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {/* Card 1: Stok Roti Saat Ini */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Stok Roti Saat Ini
            </span>
            <div className="w-10 h-10 rounded-xl bg-brand-cream flex items-center justify-center text-brand-dark">
              <Boxes className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl sm:text-5xl font-black text-slate-900 tabular-nums">
                {currentStock}
              </span>
              <span className="text-sm font-bold text-slate-500">pcs</span>
            </div>
            <div className="mt-3">
              <StatusBadge status={status} size="md" />
            </div>
          </div>
        </div>

        {/* Card 2: Roti Masuk Hari Ini */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Roti Masuk Hari Ini
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
              <ArrowDownLeft className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl sm:text-5xl font-black text-emerald-700 tabular-nums">
                +{summaryData?.masukHariIni ?? 0}
              </span>
              <span className="text-sm font-bold text-slate-500">pcs</span>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Pasokan roti matang dari dapur produksi
            </p>
          </div>
        </div>

        {/* Card 3: Roti Keluar Hari Ini */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Roti Keluar Hari Ini
            </span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
              <ArrowUpRight className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl sm:text-5xl font-black text-amber-700 tabular-nums">
                -{summaryData?.keluarHariIni ?? 0}
              </span>
              <span className="text-sm font-bold text-slate-500">pcs</span>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Terjual ke pelanggan gerai Mardani
            </p>
          </div>
        </div>
      </div>

      {/* 2. Ringkasan Harian AI Card (INDEPENDENT LOADING & ERROR BOUNDARY) */}
      <div className="bg-gradient-to-br from-slate-900 to-brand-dark text-white rounded-3xl p-6 sm:p-8 shadow-lg border border-slate-800 relative overflow-hidden">
        {/* Subtle glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-light/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col gap-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-brand-accent/20 border border-brand-accent/30 flex items-center justify-center text-brand-accent">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-base text-white flex items-center gap-2">
                <span>Ringkasan Harian</span>
                <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-brand-accent text-slate-900 tracking-wider">
                  AI
                </span>
              </h3>
            </div>
          </div>

          {/* AI Loading State: Dedicated Skeleton */}
          {loadingAi && (
            <div className="space-y-2 py-2">
              <div className="h-4 bg-white/10 rounded-lg animate-pulse w-full" />
              <div className="h-4 bg-white/10 rounded-lg animate-pulse w-5/6" />
              <div className="h-4 bg-white/10 rounded-lg animate-pulse w-2/3" />
            </div>
          )}

          {/* AI Failure State: Friendly informative fallback message */}
          {!loadingAi && aiError && (
            <div className="p-4 rounded-2xl bg-red-950/40 border border-red-500/30 text-red-200 text-xs sm:text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Layanan AI tidak tersedia.</p>
                <p className="mt-0.5 opacity-90">
                  Stok dan riwayat transaksi tetap dapat dilihat dan berfungsi normal.
                </p>
              </div>
            </div>
          )}

          {/* AI Success State: Insights text & recommendations */}
          {!loadingAi && !aiError && aiData && (
            <div className="space-y-3 pt-1">
              <p className="text-sm text-brand-cream/90 leading-relaxed font-normal">
                {aiData.summary}
              </p>
              {aiData.recommendations && (
                <div className="pt-2 border-t border-white/10 space-y-1.5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-brand-accent">
                    Rekomendasi Operasional:
                  </span>
                  {aiData.recommendations.map((rec, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 text-xs text-white/80"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-brand-light shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 3. Horizontal Bar Chart: Penjualan per Menu Hari Ini */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-slate-800">
              Penjualan per Menu Hari Ini
            </h3>
            <p className="text-xs sm:text-sm text-slate-500">
              Varian menu terlaris yang terjual di gerai Mardani Raya hari ini
            </p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-brand-cream text-brand-dark flex items-center justify-center">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        {chartData.length === 0 ? (
          <p className="text-sm text-slate-400 py-8 text-center italic">
            Belum ada penjualan menu yang tercatat hari ini.
          </p>
        ) : (
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 30, bottom: 5 }}
              >
                <XAxis
                  type="number"
                  tick={{ fontSize: 12, fill: '#64748B' }}
                  axisLine={{ stroke: '#E2E8F0' }}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 12, fill: '#1E293B', fontWeight: 600 }}
                  axisLine={{ stroke: '#E2E8F0' }}
                  tickLine={false}
                  width={110}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(154, 195, 81, 0.1)' }}
                  formatter={(val) => [`${val} pcs`, 'Terjual']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '12px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                />
                <Bar dataKey="sales" radius={[0, 8, 8, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index === 0 ? '#9AC351' : index === 1 ? '#386438' : '#88AE43'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* 4. Riwayat Transaksi Terbaru (5 items) */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-slate-800">
              Riwayat Transaksi Terbaru
            </h3>
            <p className="text-xs sm:text-sm text-slate-500">
              5 catatan pergerakan stok roti terakhir
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate('/riwayat')}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-brand-dark hover:text-brand-lightHover transition-colors"
          >
            <span>Lihat Semua Riwayat</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {(!summaryData?.recentTransactions || summaryData.recentTransactions.length === 0) ? (
          <div className="p-8 text-center text-slate-400 text-sm italic">
            Belum ada riwayat transaksi terbaru.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-100">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-brand-creamLight border-b border-slate-100 text-slate-600 font-bold text-xs uppercase tracking-wider">
                  <th className="py-3 px-4">Waktu</th>
                  <th className="py-3 px-4">Jenis</th>
                  <th className="py-3 px-4 text-right">Total Roti</th>
                  <th className="py-3 px-4">Rincian</th>
                  <th className="py-3 px-4">Dicatat Oleh</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {summaryData?.recentTransactions?.map((trx) => (
                  <tr key={trx.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-800 whitespace-nowrap text-xs">
                      {formatDateTimeIndo(trx.datetime)}
                    </td>
                    <td className="py-3 px-4">
                      {trx.type === 'masuk' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                          <ArrowDownLeft className="w-3 h-3 text-emerald-600" />
                          <span>Masuk</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-300">
                          <ArrowUpRight className="w-3 h-3 text-amber-600" />
                          <span>Keluar</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-black tabular-nums text-xs whitespace-nowrap">
                      <span
                        className={
                          trx.type === 'masuk'
                            ? 'text-emerald-700'
                            : 'text-slate-900'
                        }
                      >
                        {trx.type === 'masuk' ? `+${trx.totalQty}` : `-${trx.totalQty}`}{' '}
                        <span className="text-[10px] font-normal text-slate-500">pcs</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-700 text-xs max-w-xs truncate">
                      {trx.details}
                    </td>
                    <td className="py-3 px-4 text-slate-600 text-xs whitespace-nowrap">
                      {trx.recordedBy || 'Budi Santoso'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
