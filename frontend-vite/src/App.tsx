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
import StoresDirectoryPage from '@/app/(public)/stores/page'
import StorePage from '@/app/(public)/stores/[slug]/page'
// Seller pages
import BecomeSellerPage from '@/app/(public)/account/become-seller/page'
import RequireSeller from '@/components/auth/RequireSeller'
import SellerLayout from '@/app/(seller)/layout'
import SellerProductsPage from '@/app/(seller)/seller/products/page'
import NewProductPage from '@/app/(seller)/seller/products/new/page'
import SellerDashboardPage from '@/app/(seller)/seller/dashboard/page'
import EditProductPage from '@/app/(seller)/seller/products/[id]/edit/page'
import StoreCustomizationPage from '@/app/(seller)/seller/store/page'
// Admin pages
import RequireAdmin from '@/components/auth/RequireAdmin'
import AdminLayout from '@/app/(admin)/layout'
import AdminDashboardPage from '@/app/(admin)/admin/dashboard/page'
import AdminSellersPage from '@/app/(admin)/admin/sellers/page'
import AdminUsersPage from '@/app/(admin)/admin/users/page'
//orders pages
import OrdersPage from '@/app/(customer)/orders/page'
import OrderDetailPage from '@/app/(customer)/orders/[id]/page'
import SellerOrdersPage from '@/app/(seller)/seller/orders/page'
//store pages
import StoreThemePage from '@/app/(seller)/seller/store/theme/page'
import StorePagesPage from '@/app/(seller)/seller/store/pages/page'
import StoreSectionsPage from '@/app/(seller)/seller/store/sections/page'
import StoreMediaPage from '@/app/(seller)/seller/store/media/page'
//about page
import AboutPage from '@/app/(public)/about/page'
//checkout
import CheckoutPage from '@/app/(customer)/checkout/page'


// Placeholder pages — replace as you build them
const AccountPage       = () => <div className="p-8 text-gray-500">Account — coming soon</div>


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
        <Route path="/account/become-seller" element={<ProtectedRoute><BecomeSellerPage /></ProtectedRoute>} />
        <Route path="/cart"                   element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
        <Route path="/checkout" element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
        <Route path="/orders"                 element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
        <Route path="/account"               element={<ProtectedRoute><AccountPage /></ProtectedRoute>} />
        <Route path="/stores" element={<StoresDirectoryPage />} />
        <Route path="/stores/:slug" element={<StorePage />} />
        <Route path="/about"                  element={<AboutPage />} />
      </Route>

      {/* ── SELLER (with SellerLayout) ───────────────────────── */} 
      <Route element={<RequireSeller><SellerLayout /></RequireSeller>}>
          <Route path="/seller/dashboard" element={<SellerDashboardPage />} />
          <Route path="/seller/products" element={<SellerProductsPage />} />
          <Route path="/seller/orders" element={<SellerOrdersPage />} />
          <Route path="/seller/products/new" element={<NewProductPage />} />
          <Route path="/seller/products/:id/edit" element={<EditProductPage />} />
          <Route path="/seller/store" element={<StoreCustomizationPage />} />
          <Route path="/seller/store/theme" element={<StoreThemePage />} />
          <Route path="/seller/store/pages" element={<StorePagesPage />} />
          <Route path="/seller/store/sections" element={<StoreSectionsPage />} />
          <Route path="/seller/store/media" element={<StoreMediaPage />} />
        </Route>

      {/* ── ADMIN (add AdminLayout with auth guard later) ──── */}
      <Route element={<RequireAdmin><AdminLayout /></RequireAdmin>}>
        <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        <Route path="/admin/sellers" element={<AdminSellersPage />} />
        <Route path="/admin/users" element={<AdminUsersPage />} /> 
      </Route>
      {/* ── ORDERS page ─────────────────────── */}
      <Route path="/orders" element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
      <Route path="/orders/:id" element={<ProtectedRoute><OrderDetailPage /></ProtectedRoute>} />

      {/* 404 */}
      <Route path="*" element={
        <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">
          Page not found
        </div>
      } />
    </Routes>
  )
}