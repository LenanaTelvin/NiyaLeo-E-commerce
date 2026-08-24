import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ShoppingCart, Search, Menu, X,
  User, LogOut, LayoutDashboard, Store,
  Package, ChevronDown
} from 'lucide-react'
import { useAuthStore } from '@/lib/store/authStore'
import { useCartStore } from '@/lib/store/cartStore'
import { authApi } from '@/lib/api/auth'
import { toast } from 'sonner'
import { useCategories } from '@/lib/hooks/useCategories'


export default function Header() {
  const { user, isAuthenticated, clearAuth } = useAuthStore()
  const { itemCount } = useCartStore()
  const [mobileOpen, setMobileOpen]   = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [search, setSearch]           = useState('')
  const navigate  = useNavigate()
  const menuRef   = useRef<HTMLDivElement>(null)

  // Close user menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (search.trim()) {
      navigate(`/products?search=${encodeURIComponent(search.trim())}`)
      setMobileOpen(false)
    }
  }

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    clearAuth()
    toast.success('Signed out')
    navigate('/')
    setUserMenuOpen(false)
  }

  const dashboardPath =
    user?.role === 'admin'  ? '/admin/dashboard'  :
    user?.role === 'seller' ? '/seller/dashboard' :
    '/account'
  
  const { data: categories } = useCategories()

  return (
    <header className="bg-brand-cream border-b border-gray-200 sticky top-0 z-50">

      {/* ── MAIN BAR ──────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 h-20">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
              <span className="text-white text-xs font-bold">FC</span>
            </div>
            <span className="font-semibold text-gray-900 hidden sm:block text-sm">
              NI YA LEO
            </span>
          </Link>

          {/* Primary nav — now lives in the main bar, vertically centered */}
          <nav className="hidden md:flex items-center gap-6 ml-2">
            <Link to="/" className="text-sm font-medium text-gray-600 hover:text-brand-green transition-colors">
              Home
            </Link>
            <Link to="/products" className="text-sm font-medium text-gray-600 hover:text-brand-green transition-colors">
              Products
            </Link>
            <Link to="/stores" className="text-sm font-medium text-gray-600 hover:text-brand-green transition-colors">
              Stores
            </Link>
            <Link to="/about" className="text-sm font-medium text-gray-700 hover:text-brand-green">
              About
            </Link>
          </nav>

          {/* Spacer pushes search + actions to the right */}
          <div className="flex-1" />

          {/* Search — desktop */}
          <form onSubmit={handleSearch} className="w-full max-w-xs lg:max-w-sm hidden md:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                type="text"
                placeholder="Search products, sellers..."
                className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg
                  focus:outline-none focus:ring-2 focus:ring-brand-green focus:border-transparent
                 placeholder:text-gray-400 transition-all"
              />
            </div>
          </form>

          {/* Right actions */}
          <div className="flex items-center gap-1">

            {/* Cart */}
            <Link
              to="/cart"
              className="relative p-2.5 text-gray-600 hover:text-brand-green hover:bg-brand-greenSoft
                rounded-lg transition-colors"
            >
              <ShoppingCart className="w-5 h-5" />
              {itemCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 bg-gray-900 text-white text-xs
                  w-5 h-5 rounded-full flex items-center justify-center font-medium leading-none">
                  {itemCount > 99 ? '99+' : itemCount}
                </span>
              )}
            </Link>

            {/* Auth */}
            {isAuthenticated && user ? (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setUserMenuOpen(v => !v)}
                  className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-lg
                    hover:bg-gray-50 transition-colors"
                >
                  {/* Avatar */}
                  <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center shrink-0">
                    <span className="text-xs font-semibold text-gray-600">
                      {user.username[0].toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm text-gray-700 hidden sm:block max-w-20 truncate">
                    {user.username}
                  </span>
                  <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown */}
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200
                    rounded-xl shadow-lg py-1 z-50">

                    {/* User info */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-sm font-semibold text-gray-900 truncate">{user.username}</p>
                      <p className="text-xs text-gray-400 capitalize mt-0.5">{user.role}</p>
                    </div>

                    {/* Links */}
                    <div className="py-1">
                      <DropItem to={dashboardPath} icon={LayoutDashboard} label="Dashboard" onClick={() => setUserMenuOpen(false)} />
                      {user.role === 'seller' && (
                        <DropItem to="/seller/products" icon={Store} label="My products" onClick={() => setUserMenuOpen(false)} />
                      )}
                      <DropItem to="/orders" icon={Package} label="My orders" onClick={() => setUserMenuOpen(false)} />
                      <DropItem to="/account" icon={User} label="Account" onClick={() => setUserMenuOpen(false)} />
                    </div>

                    {/* Sign out */}
                    <div className="border-t border-gray-100 py-1">
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full px-4 py-2.5 text-sm
                          text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2 ml-1">
                <Link
                  to="/auth/login"
                  className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2
                    rounded-lg hover:bg-brand-greenSoft transition-colors hidden sm:block"
                >
                  Sign in
                </Link>
                <Link
                  to="/auth/register"
                  className="text-sm bg-gray-900 text-white px-4 py-2 rounded-lg
                    hover:bg-gray-800 transition-colors font-medium"
                >
                  Register
                </Link>
              </div>
            )}

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen(v => !v)}
              className="md:hidden p-2.5 text-gray-600 hover:text-gray-900
                hover:bg-gray-50 rounded-lg transition-colors ml-1"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile search */}
        {mobileOpen && (
          <div className="md:hidden pb-4 pt-2">
            <form onSubmit={handleSearch}>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  type="text"
                  placeholder="Search products..."
                  className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50 border border-gray-200
                    rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
                />
              </div>
            </form>
            {!isAuthenticated && (
              <Link
                to="/auth/login"
                className="flex items-center gap-2 mt-3 text-sm text-gray-600 hover:text-gray-900"
                onClick={() => setMobileOpen(false)}
              >
                <User className="w-4 h-4" />
                Sign in
              </Link>
            )}
          </div>
        )}
      </div>

    </header>
  )
}

// ── small helper ──────────────────────────────────────────────────────
function DropItem({
  to, icon: Icon, label, onClick
}: {
  to: string
  icon: React.ElementType
  label: string
  onClick: () => void
}) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700
        hover:bg-gray-50 transition-colors"
    >
      <Icon className="w-4 h-4 text-gray-400 shrink-0" />
      {label}
    </Link>
  )
}
