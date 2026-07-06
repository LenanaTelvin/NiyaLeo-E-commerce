import { Routes, Route } from 'react-router-dom'

// Layouts
import PublicLayout from '@/app/(public)/layout'

// Public pages
import HomePage from '@/app/(public)/page'
import LoginPage from '@/app/(public)/auth/login/page'
import RegisterPage from '@/app/(public)/auth/register/page'
import ProductsPage from '@/app/(public)/products/page'
import ProductDetailPage from '@/app/(public)/products/[id]/page'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import CartPage from '@/app/(customer)/cart/page'

// Placeholder pages — replace as you build them
const BecomeSellerPage  = () => <div className="p-8 text-gray-500">Become a seller — coming soon</div>
const OrdersPage        = () => <div className="p-8 text-gray-500">Orders — coming soon</div>
const AccountPage       = () => <div className="p-8 text-gray-500">Account — coming soon</div>

// Admin placeholder
const AdminDashboardPage = () => <div className="p-8 text-gray-500">Admin dashboard — coming soon</div>

// Seller placeholder
const SellerDashboardPage = () => <div className="p-8 text-gray-500">Seller dashboard — coming soon</div>

export default function App() {
  return (
    <Routes>
      {/* ── PUBLIC (with Header) ─────────────────────────────── */}
      <Route element={<PublicLayout />}>
        <Route path="/"                       element={<HomePage />} />
        <Route path="/products"               element={<ProductsPage />} />
        <Route path="/products/:id"           element={<ProductDetailPage />} />
        <Route path="/auth/login"             element={<LoginPage />} />
        <Route path="/auth/register"          element={<RegisterPage />} />
        <Route path="/account/become-seller"  element={<BecomeSellerPage />} />
        <Route path="/cart"                   element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
        <Route path="/orders"                 element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
        <Route path="/account"               element={<ProtectedRoute><AccountPage /></ProtectedRoute>} />
      </Route>

      {/* ── ADMIN (add AdminLayout with auth guard later) ──── */}
      <Route path="/admin/dashboard" element={<AdminDashboardPage />} />

      {/* ── SELLER (add SellerLayout with role guard later) ── */}
      <Route path="/seller/dashboard" element={<SellerDashboardPage />} />

      {/* 404 */}
      <Route path="*" element={
        <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">
          Page not found
        </div>
      } />
    </Routes>
  )
}