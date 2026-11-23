import React from 'react';
import { Minus, Plus } from 'lucide-react';

export default function QuantityStepper({
  value = 0,
  onChange,
  min = 0,
  max = 9999,
  disabled = false,
}) {
  const handleDecrement = (e) => {
    e.stopPropagation();
    if (value > min) {
      onChange(value - 1);
    }
  };

  const handleIncrement = (e) => {
    e.stopPropagation();
    if (value < max) {
      onChange(value + 1);
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    if (val === '') {
      onChange(0);
      return;
    }
    const parsed = parseInt(val, 10);
    if (!isNaN(parsed) && parsed >= min && parsed <= max) {
      onChange(parsed);
    }
  };

  return (
    <div className="flex items-center border border-slate-200 bg-white rounded-xl shadow-sm overflow-hidden select-none">
      <button
        type="button"
        onClick={handleDecrement}
        disabled={disabled || value <= min}
        className="w-9 h-9 flex items-center justify-center text-slate-600 hover:bg-slate-100 active:bg-slate-200 disabled:opacity-30 disabled:pointer-events-none transition-colors border-r border-slate-100"
      >
        <Minus className="w-4 h-4" />
      </button>

      <input
        type="number"
        min={min}
        max={max}
        value={value === 0 ? '' : value}
        placeholder="0"
        onChange={handleInputChange}
        disabled={disabled}
        className="w-12 h-9 text-center font-bold text-slate-800 text-sm focus:outline-none focus:bg-amber-50/50 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
      />

      <button
        type="button"
        onClick={handleIncrement}
        disabled={disabled || value >= max}
        className="w-9 h-9 flex items-center justify-center text-slate-600 hover:bg-slate-100 active:bg-slate-200 disabled:opacity-30 disabled:pointer-events-none transition-colors border-l border-slate-100"
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  );
}
