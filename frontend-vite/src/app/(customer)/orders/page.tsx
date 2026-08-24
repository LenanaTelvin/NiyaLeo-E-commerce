import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Package } from 'lucide-react'
import { useMyOrders } from '@/lib/hooks/useOrders'
import type { OrderStatus } from '@/types/order'

const formatPrice = (n: number, currency: string) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(n)

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })

export default function OrdersPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useMyOrders({ page, per_page: 20 })

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Your orders</h1>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="space-y-3">
          {data.items.map(order => (
            <Link
              key={order.id}
              to={`/orders/${order.id}`}
              className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:border-gray-300 transition-colors"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {order.order_number ?? `Order #${order.id}`}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {formatDate(order.created_at)} · {order.item_count} item{order.item_count !== 1 ? 's' : ''}
                  {order.seller_count > 1 && ` · ${order.seller_count} sellers`}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-900">
                  {formatPrice(order.total, order.currency)}
                </p>
                <StatusBadge status={order.status} />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
          <Package className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-900 font-medium mb-1">No orders yet</p>
          <p className="text-sm text-gray-400 mb-4">Your order history will show up here.</p>
          <Link to="/products" className="inline-block bg-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-gray-800">
            Browse products
          </Link>
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30">
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {data.page} of {data.total_pages}</span>
          <button disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30">
            Next
          </button>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: OrderStatus }) {
  const styles: Record<OrderStatus, string> = {
    pending: 'bg-amber-50 text-amber-600',
    confirmed: 'bg-blue-50 text-blue-600',
    processing: 'bg-blue-50 text-blue-600',
    shipped: 'bg-purple-50 text-purple-600',
    delivered: 'bg-green-50 text-green-600',
    cancelled: 'bg-gray-100 text-gray-500',
    refunded: 'bg-gray-100 text-gray-500',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${styles[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}