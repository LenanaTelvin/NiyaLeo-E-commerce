import { useState } from 'react'
import { useIncomingOrders, useUpdateSellerOrderStatus } from '@/lib/hooks/useOrders'
import { SELLER_STATUS_TRANSITIONS, type SellerOrderStatus } from '@/types/order'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'KES' }).format(n)

export default function SellerOrdersPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useIncomingOrders({ page, per_page: 20 })
  const updateStatus = useUpdateSellerOrderStatus()

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Incoming orders</h1>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
          {data.items.map((order: any) => {
            const nextOptions = SELLER_STATUS_TRANSITIONS[order.status as SellerOrderStatus] ?? []
            return (
              <div key={order.id} className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {order.order_number ?? `Order #${order.id}`}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {order.item_count} item{order.item_count !== 1 ? 's' : ''} · {formatPrice(order.total)}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded-full capitalize">
                    {order.status}
                  </span>
                  {nextOptions.length > 0 && (
                    <select
                      defaultValue=""
                      onChange={e => {
                        if (!e.target.value) return
                        let tracking_number: string | undefined
                        if (e.target.value === 'shipped') {
                          tracking_number = prompt('Tracking number (optional):') || undefined
                        }
                        updateStatus.mutate({
                          sellerOrderId: order.id,
                          data: { status: e.target.value, tracking_number },
                        })
                      }}
                      className="text-xs border border-gray-200 rounded-lg px-2 py-1.5"
                    >
                      <option value="">Update status…</option>
                      {nextOptions.map(opt => (
                        <option key={opt} value={opt}>Mark as {opt}</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
          <p className="text-gray-900 font-medium">No incoming orders yet</p>
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