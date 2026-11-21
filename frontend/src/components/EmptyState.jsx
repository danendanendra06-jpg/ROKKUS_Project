import React from 'react';
import { PackageOpen } from 'lucide-react';

export default function EmptyState({
  title = 'Belum ada data',
  description = 'Data transaksi atau stok saat ini masih kosong.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-10 text-center bg-white rounded-2xl border border-slate-200/80 my-4">
      <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center text-brand-accent mb-3">
        <PackageOpen className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-slate-800 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-sm mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}
