import { Link } from 'react-router-dom'
import { useAdminDashboard } from '@/lib/hooks/useAdmin'

export default function AdminDashboardPage() {
  const { data, isLoading } = useAdminDashboard()

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  const stats = data?.stats

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Total users" value={stats?.users.total} />
        <StatCard label="Total sellers" value={stats?.sellers.total} />
        <StatCard label="Total products" value={stats?.products.total} />
      </div>

      <Link
        to="/admin/sellers"
        className="block border border-gray-100 rounded-xl p-5 hover:border-gray-300 transition-colors max-w-xs mb-8"
      >
        <p className="text-sm text-gray-400 mb-1">Pending seller applications</p>
        <p className="text-3xl font-semibold text-gray-900">{stats?.sellers.pending ?? '—'}</p>
      </Link>

      {data?.recent_activity.items && data.recent_activity.items.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-900 mb-3">Recent activity</h2>
          <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
            {data.recent_activity.items.slice(0, 8).map((item: typeof data.recent_activity.items[0]) => (
              <div key={item.id} className="px-4 py-3 text-sm">
                <span className="text-gray-900">{item.username ?? 'System'}</span>
                <span className="text-gray-400"> — {item.description ?? item.activity_type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value?: number }) {
  return (
    <div className="border border-gray-100 rounded-xl p-5">
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <p className="text-3xl font-semibold text-gray-900">{value ?? '—'}</p>
    </div>
  )
}