import React from 'react';

/**
 * StatusBadge for bread and toppings:
 * Bread: 'Aman' | 'Menipis' | 'Habis'
 * Toppings: 'Aman' | 'Hampir Habis' | 'Habis'
 */
export default function StatusBadge({ status, size = 'md' }) {
  const sizeClasses = {
    sm: 'text-xs px-2.5 py-0.5 gap-1.5',
    md: 'text-xs sm:text-sm px-3 py-1 gap-2',
    lg: 'text-sm px-4 py-1.5 gap-2.5 font-bold',
  }[size] || 'text-xs px-3 py-1 gap-2';

  let config = {
    bg: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    dot: 'bg-emerald-500',
    label: status || 'Aman',
  };

  const s = (status || '').toLowerCase();

  if (s === 'aman') {
    config = {
      bg: 'bg-[#EAF4DC] text-[#2D5518] border-[#9AC351]',
      dot: 'bg-[#609B26]',
      label: 'Aman',
    };
  } else if (s === 'menipis' || s === 'hampir habis') {
    config = {
      bg: 'bg-[#FEF3C7] text-[#B45309] border-[#FBBF24]',
      dot: 'bg-[#D97706]',
      label: status,
    };
  } else if (s === 'habis') {
    config = {
      bg: 'bg-[#FEE2E2] text-[#B91C1C] border-[#FCA5A5]',
      dot: 'bg-[#DC2626]',
      label: 'Habis',
    };
  }

  return (
    <span
      className={`inline-flex items-center rounded-full font-semibold border shadow-sm select-none ${config.bg} ${sizeClasses}`}
    >
      <span className={`w-2 h-2 rounded-full ${config.dot}`} />
      <span>{config.label}</span>
    </span>
  );
}
