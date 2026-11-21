import React from 'react';
import QuantityStepper from './QuantityStepper';
import { Flame, Sparkles, UtensilsCrossed, Cookie } from 'lucide-react';
import { MENU_CATEGORIES } from '../config/constants';

export default function MenuCard({ item, quantity, onChange }) {
  const isSelected = quantity > 0;
  const isTambahan = item.category === MENU_CATEGORIES.TAMBAHAN;

  return (
    <div
      className={`rounded-2xl p-4 transition-all duration-200 border flex flex-col justify-between ${
        isSelected
          ? 'bg-amber-50/40 border-brand-accent shadow-md'
          : 'bg-white border-slate-200/80 hover:border-slate-300 shadow-xs'
      }`}
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="min-h-[22px]">
            {item.tag === 'Best Seller' && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#FEF3C7] text-[#904D00] border border-amber-300">
                <Flame className="w-3 h-3 text-amber-600" />
                <span>Best Seller</span>
              </span>
            )}
            {item.tag === 'Baru' && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#EAF4DC] text-[#2D5518] border border-[#9AC351]">
                <Sparkles className="w-3 h-3 text-brand-dark" />
                <span>Baru</span>
              </span>
            )}
            {isTambahan && !item.tag && (
              <span className="inline-block px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 text-[10px] font-bold border border-emerald-200">
                Topping Tambahan
              </span>
            )}
          </div>
          <div
            className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
              isSelected
                ? 'bg-brand-accent text-white'
                : 'bg-slate-100 text-slate-400'
            }`}
          >
            {isTambahan ? (
              <Cookie className="w-4 h-4" />
            ) : (
              <UtensilsCrossed className="w-4 h-4" />
            )}
          </div>
        </div>

        <h4 className="font-bold text-slate-800 text-sm group-hover:text-brand-dark line-clamp-1">
          {item.name}
        </h4>
        <p className="text-[11px] text-slate-400 mt-0.5">
          {isTambahan ? 'Tidak memotong stok roti' : 'Memotong 1 pcs roti'}
        </p>
      </div>

      <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-100">
        <span className="text-xs font-semibold text-slate-500">Porsi:</span>
        <QuantityStepper value={quantity} onChange={onChange} min={0} max={999} />
      </div>
    </div>
  );
}
