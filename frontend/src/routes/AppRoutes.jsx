import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROLES } from '../config/constants';

import DashboardLayout from '../layouts/DashboardLayout';
import ProtectedRoute from './ProtectedRoute';

import Login from '../pages/Login';
import AksesDitolak from '../pages/AksesDitolak';
import DaftarStok from '../pages/DaftarStok';
import CatatTransaksi from '../pages/CatatTransaksi';
import RiwayatTransaksi from '../pages/RiwayatTransaksi';
import StokTopping from '../pages/StokTopping';
import Dashboard from '../pages/Dashboard';

// Index redirect based on logged in role
function RootRedirect() {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (user?.role === ROLES.PEMILIK) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Navigate to="/daftar-stok" replace />;
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes wrapped in main DashboardLayout */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<RootRedirect />} />
        <Route path="/akses-ditolak" element={<AksesDitolak />} />

        {/* Pengelola Only routes */}
        <Route
          path="/daftar-stok"
          element={
            <ProtectedRoute allowedRoles={[ROLES.PENGELOLA]}>
              <DaftarStok />
            </ProtectedRoute>
          }
        />
        <Route
          path="/catat-transaksi"
          element={
            <ProtectedRoute allowedRoles={[ROLES.PENGELOLA]}>
              <CatatTransaksi />
            </ProtectedRoute>
          }
        />

        {/* Shared routes (Pengelola & Pemilik) */}
        <Route
          path="/riwayat"
          element={
            <ProtectedRoute allowedRoles={[ROLES.PENGELOLA, ROLES.PEMILIK]}>
              <RiwayatTransaksi />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-topping"
          element={
            <ProtectedRoute allowedRoles={[ROLES.PENGELOLA, ROLES.PEMILIK]}>
              <StokTopping />
            </ProtectedRoute>
          }
        />

        {/* Pemilik Only routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute allowedRoles={[ROLES.PEMILIK]}>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Fallback to root */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
