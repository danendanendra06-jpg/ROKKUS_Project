import React, { useState, useEffect, useMemo } from 'react';
import { stockService } from '../services/stockService';
import { menuService } from '../services/menuService';
import StockCard from '../components/StockCard';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { TableSkeleton, CardSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { useToast } from '../components/Toast';
import { MENU_CATEGORIES } from '../config/constants';
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  Sparkles,
  Flame,
  AlertCircle,
} from 'lucide-react';

export default function DaftarStok() {
  const [stockData, setStockData] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [activeTab, setActiveTab] = useState('Semua');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals state
  const [isEditInitialStockOpen, setIsEditInitialStockOpen] = useState(false);
  const [initialStockInput, setInitialStockInput] = useState('');
  const [isUpdatingStock, setIsUpdatingStock] = useState(false);

  const [isMenuModalOpen, setIsMenuModalOpen] = useState(false);
  const [editingMenu, setEditingMenu] = useState(null);
  const [menuForm, setMenuForm] = useState({
    name: '',
    category: MENU_CATEGORIES.ROTI_MANIS,
    tag: '',
  });
  const [menuFormError, setMenuFormError] = useState('');
  const [isSavingMenu, setIsSavingMenu] = useState(false);

  const [deleteDialog, setDeleteDialog] = useState({
    isOpen: false,
    item: null,
    isLoading: false,
  });

  const { addToast } = useToast();

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [stockRes, menuRes] = await Promise.all([
        stockService.getBreadStock(),
        menuService.getMenuItems(),
      ]);
      setStockData(stockRes);
      setMenuItems(menuRes);
      setInitialStockInput(stockRes?.initialStock ?? stockRes?.stock ?? 0);
    } catch (err) {
      setError(err.message || 'Gagal memuat data. Periksa koneksi lalu coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered menu items
  const filteredMenuItems = useMemo(() => {
    return menuItems.filter((item) => {
      const matchCategory =
        activeTab === 'Semua' ? true : item.category === activeTab;
      const matchSearch =
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.category.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCategory && matchSearch;
    });
  }, [menuItems, activeTab, searchQuery]);

  // Tab counts
  const tabCounts = useMemo(() => {
    return {
      Semua: menuItems.length,
      [MENU_CATEGORIES.ROTI_MANIS]: menuItems.filter(
        (m) => m.category === MENU_CATEGORIES.ROTI_MANIS
      ).length,
      [MENU_CATEGORIES.ROTI_ASIN]: menuItems.filter(
        (m) => m.category === MENU_CATEGORIES.ROTI_ASIN
      ).length,
      [MENU_CATEGORIES.TAMBAHAN]: menuItems.filter(
        (m) => m.category === MENU_CATEGORIES.TAMBAHAN
      ).length,
    };
  }, [menuItems]);

  // Initial stock submit
  const handleSaveInitialStock = async (e) => {
    e.preventDefault();
    const qty = parseInt(initialStockInput, 10);
    if (isNaN(qty) || qty < 0) {
      addToast('Jumlah stok awal harus berupa angka 0 atau lebih', 'error');
      return;
    }

    try {
      setIsUpdatingStock(true);
      const updated = await stockService.updateInitialStock(qty);
      setStockData(updated);
      setIsEditInitialStockOpen(false);
      addToast('Stok awal berhasil diperbarui!', 'success');
    } catch (err) {
      addToast(err.message || 'Gagal memperbarui stok awal.', 'error');
    } finally {
      setIsUpdatingStock(false);
    }
  };

  // Menu modal handlers
  const openAddMenuModal = () => {
    setEditingMenu(null);
    setMenuForm({
      name: '',
      category: activeTab === 'Semua' ? MENU_CATEGORIES.ROTI_MANIS : activeTab,
      tag: '',
    });
    setMenuFormError('');
    setIsMenuModalOpen(true);
  };

  const openEditMenuModal = (item) => {
    setEditingMenu(item);
    setMenuForm({
      name: item.name,
      category: item.category,
      tag: item.tag || '',
    });
    setMenuFormError('');
    setIsMenuModalOpen(true);
  };

  const handleSaveMenu = async (e) => {
    e.preventDefault();
    if (!menuForm.name.trim()) {
      setMenuFormError('Nama menu wajib diisi');
      return;
    }

    try {
      setIsSavingMenu(true);
      if (editingMenu) {
        const updated = await menuService.updateMenuItem(editingMenu.id, menuForm);
        setMenuItems((prev) =>
          prev.map((m) => (m.id === updated.id ? updated : m))
        );
        addToast(`Menu "${updated.name}" berhasil diubah!`, 'success');
      } else {
        const created = await menuService.createMenuItem(menuForm);
        setMenuItems((prev) => [...prev, created]);
        addToast(`Menu "${created.name}" berhasil ditambahkan!`, 'success');
      }
      setIsMenuModalOpen(false);
    } catch (err) {
      setMenuFormError(err.message || 'Gagal menyimpan menu');
    } finally {
      setIsSavingMenu(false);
    }
  };

  // Delete menu handlers
  const confirmDeleteMenu = (item) => {
    setDeleteDialog({
      isOpen: true,
      item,
      isLoading: false,
    });
  };

  const handleDeleteMenu = async () => {
    if (!deleteDialog.item) return;
    try {
      setDeleteDialog((prev) => ({ ...prev, isLoading: true }));
      await menuService.deleteMenuItem(deleteDialog.item.id);
      setMenuItems((prev) => prev.filter((m) => m.id !== deleteDialog.item.id));
      addToast(`Menu "${deleteDialog.item.name}" telah dihapus`, 'success');
      setDeleteDialog({ isOpen: false, item: null, isLoading: false });
    } catch (err) {
      addToast(err.message || 'Gagal menghapus menu', 'error');
      setDeleteDialog((prev) => ({ ...prev, isLoading: false }));
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <CardSkeleton />
        <TableSkeleton rows={8} cols={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-6">
      {/* 1. Large Bread Stock Card */}
      <StockCard
        stockData={stockData}
        onOpenEditInitialStock={() => {
          setInitialStockInput(stockData?.initialStock ?? stockData?.stock ?? 0);
          setIsEditInitialStockOpen(true);
        }}
      />

      {/* 2. Menu Management Section */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm space-y-6">
        {/* Header Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-slate-800">Daftar Menu Gerai</h3>
            <p className="text-sm text-slate-500">
              Kelola daftar menu roti manis, roti asin, dan topping tambahan
            </p>
          </div>

          <button
            type="button"
            onClick={openAddMenuModal}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-light hover:bg-brand-lightHover text-white rounded-xl text-sm font-bold shadow-sm transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>Tambah Menu</span>
          </button>
        </div>

        {/* Filters: Category Tabs & Search Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pt-2">
          {/* Tabs */}
          <div className="inline-flex p-1 bg-brand-cream rounded-2xl gap-1 overflow-x-auto max-w-full">
            {['Semua', MENU_CATEGORIES.ROTI_MANIS, MENU_CATEGORIES.ROTI_ASIN, MENU_CATEGORIES.TAMBAHAN].map(
              (tab) => {
                const isActive = activeTab === tab;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2 ${
                      isActive
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
                    }`}
                  >
                    <span>{tab}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                        isActive
                          ? 'bg-brand-cream text-brand-dark'
                          : 'bg-slate-200/70 text-slate-600'
                      }`}
                    >
                      {tabCounts[tab] || 0}
                    </span>
                  </button>
                );
              }
            )}
          </div>

          {/* Search Input */}
          <div className="relative w-full lg:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari menu roti..."
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm bg-slate-50/50"
            />
          </div>
        </div>

        {/* Menu Items Table */}
        {filteredMenuItems.length === 0 ? (
          <EmptyState
            title="Menu tidak ditemukan"
            description="Tidak ada item menu yang cocok dengan filter atau kata kunci pencarian."
            action={
              <button
                type="button"
                onClick={() => {
                  setActiveTab('Semua');
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
                  <th className="py-3.5 px-4 sm:px-6">Nama Menu</th>
                  <th className="py-3.5 px-4">Kategori</th>
                  <th className="py-3.5 px-4">Penanda</th>
                  <th className="py-3.5 px-4 text-right">Terjual Hari Ini</th>
                  <th className="py-3.5 px-4 sm:px-6 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredMenuItems.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-slate-50/80 transition-colors group"
                  >
                    <td className="py-3.5 px-4 sm:px-6 font-bold text-slate-900">
                      {item.name}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${
                          item.category === MENU_CATEGORIES.ROTI_MANIS
                            ? 'bg-amber-50 text-amber-800 border border-amber-200'
                            : item.category === MENU_CATEGORIES.ROTI_ASIN
                            ? 'bg-orange-50 text-orange-800 border border-orange-200'
                            : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        }`}
                      >
                        {item.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {item.tag === 'Best Seller' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-[#FEF3C7] text-[#904D00] border border-amber-300">
                          <Flame className="w-3.5 h-3.5 text-amber-600" />
                          <span>Best Seller</span>
                        </span>
                      )}
                      {item.tag === 'Baru' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-[#EAF4DC] text-[#2D5518] border border-[#9AC351]">
                          <Sparkles className="w-3.5 h-3.5 text-brand-dark" />
                          <span>Baru</span>
                        </span>
                      )}
                      {!item.tag && <span className="text-slate-400">-</span>}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-slate-800 tabular-nums">
                      {item.todaySales || 0}{' '}
                      <span className="text-xs font-normal text-slate-500">pcs</span>
                    </td>
                    <td className="py-3.5 px-4 sm:px-6 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          type="button"
                          onClick={() => openEditMenuModal(item)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-brand-dark hover:bg-brand-cream transition-colors"
                          title="Ubah Menu"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => confirmDeleteMenu(item)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          title="Hapus Menu"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Ubah Stok Awal */}
      <Modal
        isOpen={isEditInitialStockOpen}
        onClose={() => setIsEditInitialStockOpen(false)}
        title="Ubah Stok Awal Roti"
      >
        <form onSubmit={handleSaveInitialStock} className="space-y-4">
          <p className="text-xs text-slate-500 leading-relaxed">
            Perubahan stok awal akan mengkalkulasi ulang total sisa stok yang tersedia di gerai.
          </p>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Stok Awal (pcs)
            </label>
            <input
              type="number"
              min="0"
              value={initialStockInput}
              onChange={(e) => setInitialStockInput(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-bold"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsEditInitialStockOpen(false)}
              className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100"
            >
              Batal
            </button>
            <button
              type="submit"
              disabled={isUpdatingStock}
              className="px-5 py-2 rounded-xl bg-brand-light hover:bg-brand-lightHover text-white text-sm font-bold flex items-center gap-2"
            >
              {isUpdatingStock && (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              <span>Simpan Perubahan</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Tambah / Ubah Menu */}
      <Modal
        isOpen={isMenuModalOpen}
        onClose={() => setIsMenuModalOpen(false)}
        title={editingMenu ? 'Ubah Menu' : 'Tambah Menu Baru'}
      >
        <form onSubmit={handleSaveMenu} className="space-y-4">
          {menuFormError && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{menuFormError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Nama Menu <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={menuForm.name}
              onChange={(e) => {
                setMenuForm({ ...menuForm, name: e.target.value });
                if (menuFormError) setMenuFormError('');
              }}
              placeholder="Contoh: Lotus Biscoff, Coklat Keju"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-medium"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Kategori
            </label>
            <select
              value={menuForm.category}
              onChange={(e) =>
                setMenuForm({ ...menuForm, category: e.target.value })
              }
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-medium bg-white"
            >
              <option value={MENU_CATEGORIES.ROTI_MANIS}>
                {MENU_CATEGORIES.ROTI_MANIS}
              </option>
              <option value={MENU_CATEGORIES.ROTI_ASIN}>
                {MENU_CATEGORIES.ROTI_ASIN}
              </option>
              <option value={MENU_CATEGORIES.TAMBAHAN}>
                {MENU_CATEGORIES.TAMBAHAN}
              </option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Penanda Khusus
            </label>
            <select
              value={menuForm.tag}
              onChange={(e) =>
                setMenuForm({ ...menuForm, tag: e.target.value })
              }
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-light text-sm font-medium bg-white"
            >
              <option value="">Tanpa Penanda</option>
              <option value="Best Seller">Best Seller</option>
              <option value="Baru">Baru</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsMenuModalOpen(false)}
              className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100"
            >
              Batal
            </button>
            <button
              type="submit"
              disabled={isSavingMenu}
              className="px-5 py-2 rounded-xl bg-brand-light hover:bg-brand-lightHover text-white text-sm font-bold flex items-center gap-2"
            >
              {isSavingMenu && (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              <span>{editingMenu ? 'Simpan Perubahan' : 'Tambah Menu'}</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Dialog Konfirmasi Hapus */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, item: null, isLoading: false })}
        onConfirm={handleDeleteMenu}
        title="Hapus Menu"
        message={`Apakah Anda yakin ingin menghapus menu "${deleteDialog.item?.name}"? Tindakan ini tidak dapat dibatalkan.`}
        confirmText="Hapus"
        cancelText="Batal"
        isDestructive={true}
        isLoading={deleteDialog.isLoading}
      />
    </div>
  );
}
