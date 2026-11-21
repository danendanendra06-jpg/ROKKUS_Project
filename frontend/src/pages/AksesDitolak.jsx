import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { ROLES } from '../config/constants';

export default function AksesDitolak() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleReturn = () => {
    if (user?.role === ROLES.PENGELOLA) {
      navigate('/daftar-stok');
    } else if (user?.role === ROLES.PEMILIK) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 text-center shadow-lg border border-red-100 flex flex-col items-center">
        <div className="w-16 h-16 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mb-4">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-red-100 text-red-800 rounded-full mb-3">
          Akses Terbatas
        </span>

        <h1 className="text-2xl font-bold text-slate-800 mb-2">Akses Ditolak</h1>
        <p className="text-sm text-slate-600 leading-relaxed mb-6">
          Akun Anda ({user?.name || 'Pengguna'} - {user?.title || user?.role}) tidak memiliki izin untuk membuka halaman ini.
          {user?.role === ROLES.PEMILIK && ' Akun Pemilik memiliki akses khusus pemantauan (view-only).'}
          {user?.role === ROLES.PENGELOLA && ' Halaman analitik tingkat lanjut dikhususkan untuk Pemilik usaha.'}
        </p>

        <button
          onClick={handleReturn}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-light hover:bg-brand-lightHover text-white rounded-xl text-sm font-semibold transition-all shadow-sm active:scale-95"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Kembali ke Halaman Utama</span>
        </button>
      </div>
    </div>
  );
}
