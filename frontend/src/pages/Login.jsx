import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DEMO_ACCOUNTS, ROLES } from '../config/constants';
import logoImg from '../assets/logo.png';
import { Shield, Sparkles, Utensils, AlertCircle, ArrowRight } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Empty validation rules
    if (!username.trim()) {
      setError('Username wajib diisi');
      return;
    }
    if (!password.trim()) {
      setError('Password wajib diisi');
      return;
    }

    try {
      setIsSubmitting(true);
      const user = await login({ username, password });

      // Role based routing after login
      if (user.role === ROLES.PENGELOLA) {
        navigate('/daftar-stok', { replace: true });
      } else if (user.role === ROLES.PEMILIK) {
        navigate('/dashboard', { replace: true });
      } else {
        navigate('/daftar-stok', { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Username atau password salah. Silakan coba lagi.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFillDemo = (demoUsername) => {
    setUsername(demoUsername);
    setPassword('demo123');
    setError('');
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-brand-cream">
      {/* LEFT PANEL: Dark Green Brand Panel */}
      <div className="w-full lg:w-[48%] bg-brand-dark text-white p-8 sm:p-12 lg:p-16 flex flex-col justify-between relative overflow-hidden">
        {/* Glow Effects */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-brand-light/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full bg-brand-accent/20 blur-3xl pointer-events-none" />

        <div className="relative z-10">
          {/* Header Brand */}
          <div className="flex items-center justify-between flex-wrap gap-4 mb-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md p-1.5 flex items-center justify-center border border-white/20 shadow-md">
                <img src={logoImg} alt="ROKKUS Logo" className="w-full h-full object-contain" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight flex items-center gap-1.5">
                  ROKKUS <span className="font-light text-brand-light">Stok</span>
                </h1>
                <p className="text-xs text-brand-cream/80 uppercase tracking-wider font-medium">
                  Outlet Mardani Raya
                </p>
              </div>
            </div>

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-brand-light border border-white/15">
              <span className="w-2 h-2 rounded-full bg-brand-light animate-pulse" />
              <span>Outlet Aktif</span>
            </div>
          </div>

          {/* Headline & Description */}
          <div className="space-y-4 max-w-lg mt-6">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight text-white">
              Pantau stok harian dalam satu tempat.
            </h2>
            <p className="text-sm sm:text-base text-brand-cream/90 leading-relaxed">
              Sistem pencatatan dan monitoring stok roti kukus & bakar hijau pandan segar setiap hari dengan kendali presisi untuk operasional gerai.
            </p>
          </div>
        </div>

        {/* Mascot / Bread Visual */}
        <div className="relative z-10 my-8 flex flex-col items-center justify-center">
          <div className="relative flex items-center justify-center">
            <div className="w-44 h-44 sm:w-52 sm:h-52 rounded-full bg-brand-light/20 p-3 shadow-inner border border-white/10 flex items-center justify-center">
              <img
                src={logoImg}
                alt="Roti Pandan ROKKUS"
                className="w-36 h-36 sm:w-44 sm:h-44 object-contain rounded-full drop-shadow-xl"
              />
            </div>
          </div>
          <span className="mt-4 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/15 backdrop-blur-md text-xs font-semibold text-brand-cream border border-white/15">
            <Utensils className="w-3.5 h-3.5 text-brand-accent" />
            Kukus & Bakar Pandan Segar Tiap Hari
          </span>
        </div>

        {/* Feature Highlights */}
        <div className="relative z-10 pt-4 flex flex-wrap gap-2.5">
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/10 backdrop-blur-md text-xs font-medium text-white border border-white/10">
            <Sparkles className="w-4 h-4 text-brand-accent" />
            <span>Pencatatan Cepat</span>
          </div>
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/10 backdrop-blur-md text-xs font-medium text-white border border-white/10">
            <Shield className="w-4 h-4 text-brand-light" />
            <span>Notifikasi Stok Menipis</span>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: Login Form Area */}
      <div className="w-full lg:w-[52%] flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16">
        <div className="w-full max-w-md">
          {/* Card Box */}
          <div className="bg-white rounded-3xl p-8 sm:p-10 shadow-xl border border-slate-200/60">
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-slate-800">Masuk ke Akun</h3>
              <p className="text-sm text-slate-500 mt-1">
                Silakan masukkan kredensial untuk membuka sistem stok gerai.
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="mb-5 p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 shrink-0 text-red-500 mt-0.5" />
                <p className="leading-snug">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (error) setError('');
                  }}
                  placeholder="Contoh: pengelola / pemilik"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light focus:border-brand-light transition text-sm bg-slate-50/50"
                  disabled={isSubmitting}
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError('');
                  }}
                  placeholder="Minimal 4 karakter"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light focus:border-brand-light transition text-sm bg-slate-50/50"
                  disabled={isSubmitting}
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-2 py-3.5 px-4 bg-brand-light hover:bg-brand-lightHover text-white rounded-xl font-bold text-sm transition-all shadow-md active:scale-98 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {isSubmitting ? (
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Masuk ke ROKKUS Stok</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* DEMO ACCOUNTS HELPER BOX */}
            <div className="mt-8 pt-6 border-t border-slate-100">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                Akun Demo Prototipe (Klik untuk isi cepat)
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.username}
                    type="button"
                    onClick={() => handleFillDemo(acc.username)}
                    className="p-3 rounded-xl border border-slate-200 bg-brand-creamLight hover:border-brand-light hover:bg-white text-left transition-all group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-slate-800 text-xs group-hover:text-brand-dark">
                        {acc.name}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                        {acc.role}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      User: <code className="text-brand-dark font-bold">{acc.username}</code>
                    </p>
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-2 text-center">
                *Password: bebas minimal 4 karakter (mode mock).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
