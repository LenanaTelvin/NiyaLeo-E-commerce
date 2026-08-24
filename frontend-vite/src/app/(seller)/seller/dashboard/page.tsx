import { Link } from 'react-router-dom'
import { Package, ShoppingBag, TrendingUp, Wallet, Paintbrush, ArrowRight, Plus } from 'lucide-react'
import { useSellerDashboard } from '@/lib/hooks/useSellers'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(n)

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-KE', { day: 'numeric', month: 'short' })

export default function SellerDashboardPage() {
  const { data, isLoading } = useSellerDashboard()

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (!data) return null

  const maxChartValue = Math.max(...data.sales_chart.values, 1)

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div className="flex items-center gap-2">
          <Link
            to="/seller/store"
            className="flex items-center gap-1.5 border border-gray-200 text-sm text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Paintbrush className="w-3.5 h-3.5" />
            Customize store
          </Link>
          <Link
            to="/seller/products/new"
            className="flex items-center gap-1.5 bg-gray-900 text-white text-sm px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add product
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard icon={ShoppingBag} label="Orders" value={data.total_orders} />
        <StatCard icon={Package} label="Products" value={data.total_products} />
        <StatCard icon={TrendingUp} label="Revenue" value={formatPrice(data.total_revenue)} />
        <StatCard icon={Wallet} label="Your earnings" value={formatPrice(data.total_earnings)} highlight />
      </div>

      {/* Earnings breakdown */}
      <div className="border border-gray-100 rounded-xl p-5 mb-8">
        <h2 className="text-sm font-medium text-gray-900 mb-4">Earnings breakdown</h2>
        <div className="space-y-3 text-sm">
          <Row label="Gross revenue" value={formatPrice(data.total_revenue)} />
          <Row label="Platform commission" value={`-${formatPrice(data.total_commission)}`} negative />
          <div className="border-t border-gray-100 pt-3">
            <Row label="Your net earnings" value={formatPrice(data.total_earnings)} bold />
          </div>
          {data.pending_orders > 0 && (
            <p className="text-xs text-gray-400 pt-2">
              {data.pending_orders} order{data.pending_orders !== 1 ? 's' : ''} still pending — earnings may change once confirmed.
            </p>
          )}
        </div>
      </div>

      {/* 7-day sales chart */}
      <div className="border border-gray-100 rounded-xl p-5 mb-8">
        <h2 className="text-sm font-medium text-gray-900 mb-4">Last 7 days</h2>
        {data.sales_chart.values.every(v => v === 0) ? (
          <div className="h-32 flex items-center justify-center">
            <p className="text-sm text-gray-400">No sales in the last 7 days</p>
          </div>
        ) : (
          <div className="flex items-end gap-3 h-32">
            {data.sales_chart.labels.map((label, i) => {
              const value = data.sales_chart.values[i]
              const heightPct = (value / maxChartValue) * 100
              return (
                <div key={label} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full flex-1 flex items-end">
                    <div
                      className="w-full bg-gray-900 rounded-t-sm transition-all"
                      style={{ height: `${Math.max(heightPct, value > 0 ? 4 : 0)}%` }}
                      title={formatPrice(value)}
                    />
                  </div>
                  <span className="text-xs text-gray-400">{label}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Recent orders */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-900">Recent orders</h2>
          <Link to="/seller/orders" className="text-xs text-gray-500 hover:text-gray-900 flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        {data.recent_orders.length > 0 ? (
          <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
            {data.recent_orders.map(order => (
              <div key={order.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div>
                  <p className="text-gray-900 font-medium">{order.order_number ?? `Order #${order.id}`}</p>
                  <p className="text-xs text-gray-400">{formatDate(order.created_at)}</p>
                </div>
                <div className="text-right">
                  <p className="text-gray-900 font-medium">{formatPrice(order.seller_earnings)}</p>
                  <span className={`text-xs capitalize px-2 py-0.5 rounded-full ${
                    order.status === 'delivered' ? 'bg-green-50 text-green-700' :
                    order.status === 'pending' ? 'bg-amber-50 text-amber-600' :
                    order.status === 'cancelled' ? 'bg-red-50 text-red-600' :
                    'bg-gray-100 text-gray-500'
                  }`}>
                    {order.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 border border-dashed border-gray-200 rounded-xl">
            <ShoppingBag className="w-8 h-8 text-gray-200 mx-auto mb-3" />
            <p className="text-sm text-gray-400 mb-4">No orders yet</p>
            <Link
              to="/seller/products/new"
              className="inline-flex items-center gap-1.5 text-sm text-gray-900 font-medium border border-gray-200 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Add your first product
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, highlight }: {
  icon: React.ElementType
  label: string
  value: string | number
  highlight?: boolean
}) {
  return (
    <div className={`border rounded-xl p-4 ${highlight ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-100 bg-white'}`}>
      <Icon className={`w-4 h-4 mb-2 ${highlight ? 'text-gray-300' : 'text-gray-400'}`} />
      <p className={`text-xs mb-0.5 ${highlight ? 'text-gray-300' : 'text-gray-400'}`}>{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  )
}

function Row({ label, value, negative, bold }: {
  label: string
  value: string
  negative?: boolean
  bold?: boolean
}) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`${negative ? 'text-red-500' : 'text-gray-900'} ${bold ? 'font-semibold text-base' : ''}`}>
        {value}
      </span>
    </div>
  )
}
