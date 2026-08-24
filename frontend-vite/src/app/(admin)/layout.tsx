import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Store, Users, LogOut } from 'lucide-react'
import { toast } from 'sonner'
import { useAuthStore } from '@/lib/store/authStore'
import { authApi } from '@/lib/api/auth'

const NAV = [
  { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admin/sellers', label: 'Sellers', icon: Store },
  { to: '/admin/users', label: 'Users', icon: Users },
]

export default function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    clearAuth()
    toast.success('Signed out')
    navigate('/auth/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 shrink-0 bg-white border-r border-gray-100 min-h-screen py-6 px-3 flex flex-col">
        <div className="px-3 mb-6">
          <span className="text-sm font-semibold text-gray-900">Admin</span>
        </div>

        <nav className="space-y-1 flex-1">
          {NAV.map(item => {
            const active = location.pathname.startsWith(item.to)
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  active ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Identity + sign out — always visible, bottom of sidebar */}
        <div className="border-t border-gray-100 pt-3 px-3">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center shrink-0">
              <span className="text-xs font-semibold text-gray-600">
                {user?.username?.[0]?.toUpperCase() ?? 'A'}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-900 truncate">{user?.username}</p>
              <p className="text-xs text-gray-400">Admin</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  )
}