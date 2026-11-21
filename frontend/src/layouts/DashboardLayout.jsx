import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ConfirmDialog from '../components/ConfirmDialog';
import logoImg from '../assets/logo.png';
import {
  Boxes,
  ClipboardPenLine,
  History,
  Layers,
  LayoutDashboard,
  LogOut,
  Menu,
  X,
  User,
} from 'lucide-react';

export default function DashboardLayout() {
  const { user, isPengelola, isPemilik, logout } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    setIsLogoutModalOpen(false);
    navigate('/login');
  };

  // Navigation items based on role
  const navItems = isPengelola
    ? [
        {
          name: 'Daftar Stok',
          to: '/daftar-stok',
          icon: Boxes,
        },
        {
          name: 'Catat Transaksi',
          to: '/catat-transaksi',
          icon: ClipboardPenLine,
        },
        {
          name: 'Riwayat Transaksi',
          to: '/riwayat',
          icon: History,
        },
        {
          name: 'Stok Topping',
          to: '/stok-topping',
          icon: Layers,
          badge: 'Tambahan',
        },
      ]
    : [
        {
          name: 'Dashboard',
          to: '/dashboard',
          icon: LayoutDashboard,
        },
        {
          name: 'Riwayat Transaksi',
          to: '/riwayat',
          icon: History,
        },
        {
          name: 'Stok Topping',
          to: '/stok-topping',
          icon: Layers,
          badge: 'Tambahan',
        },
      ];

  const sidebarContent = (
    <div className="flex flex-col h-full justify-between text-white select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-white/10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl overflow-hidden bg-white/15 p-1 flex items-center justify-center border border-white/20 shrink-0">
            <img
              src={logoImg}
              alt="ROKKUS"
              className="w-full h-full object-contain drop-shadow"
            />
          </div>
          <div className="overflow-hidden">
            <h1 className="font-bold text-lg tracking-tight leading-tight flex items-center gap-1.5">
              ROKKUS <span className="font-light text-brand-light">Stok</span>
            </h1>
            <p className="text-xs text-brand-cream/80 truncate">
              Outlet Mardani Raya
            </p>
          </div>
        </div>

        {/* Role indicator chip */}
        <div className="px-5 pt-4 pb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/10 text-xs font-medium text-white/90">
            <span className="w-2 h-2 rounded-full bg-brand-light animate-pulse" />
            <span>Mode {isPengelola ? 'Pengelola (Aktif)' : 'Pemilik (Lihat)'}</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1.5 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setIsMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-3 rounded-xl font-medium text-sm transition-all ${
                    isActive
                      ? 'bg-brand-light text-white font-bold shadow-sm'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-accent/20 text-brand-accent border border-brand-accent/30">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User Info & Logout Footer */}
      <div className="p-4 border-t border-white/10 bg-black/10">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-brand-light font-bold text-sm shrink-0">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-bold truncate text-white leading-tight">
                {user?.name || 'Pengguna'}
              </p>
              <p className="text-xs text-white/70 truncate">{user?.title || user?.role}</p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsLogoutModalOpen(true)}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-white/10 hover:bg-red-500/20 hover:text-red-200 text-white/80 text-xs font-semibold transition-all border border-white/10"
        >
          <LogOut className="w-4 h-4" />
          <span>Keluar</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-brand-cream">
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between px-4 py-3 bg-brand-dark text-white border-b border-white/10 sticky top-0 z-40">
        <div className="flex items-center gap-2.5">
          <img src={logoImg} alt="Logo" className="w-8 h-8 object-contain" />
          <div>
            <h1 className="font-bold text-base leading-tight">
              ROKKUS <span className="font-light text-brand-light">Stok</span>
            </h1>
            <p className="text-[10px] text-white/70">Outlet Mardani Raya</p>
          </div>
        </div>
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-2 rounded-lg bg-white/10 text-white hover:bg-white/20"
        >
          {isMobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm"
            onClick={() => setIsMobileOpen(false)}
          />
          <div className="relative w-72 max-w-xs bg-brand-dark h-full shadow-2xl z-10">
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Desktop Sidebar (fixed dark green #386438) */}
      <aside className="hidden lg:block w-64 bg-brand-dark shrink-0 h-screen sticky top-0 border-r border-white/10 shadow-sm">
        {sidebarContent}
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
        <Outlet />
      </main>

      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={handleLogout}
        title="Konfirmasi Keluar"
        message="Apakah Anda yakin ingin keluar dari akun ROKKUS Stok? Anda perlu masuk kembali untuk mengakses data."
        confirmText="Keluar"
        cancelText="Batal"
        isDestructive={true}
      />
    </div>
  );
}
