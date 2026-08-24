import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useOrder, useCancelOrder } from '@/lib/hooks/useOrders'

const formatPrice = (n: number, currency: string) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(n)

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const orderId = id ? Number(id) : undefined
  const { data: order, isLoading, isError } = useOrder(orderId)
  const cancelOrder = useCancelOrder()

  if (isLoading) {
    return <div className="max-w-3xl mx-auto px-4 py-8 animate-pulse h-64 bg-gray-100 rounded-xl" />
  }

  if (isError || !order) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <p className="text-gray-900 font-medium mb-1">Order not found</p>
        <Link to="/orders" className="text-sm text-gray-900 underline">Back to orders</Link>
      </div>
    )
  }

  const canCancel = order.status === 'pending' || order.status === 'confirmed'

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <Link to="/orders" className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to orders
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            {order.order_number ?? `Order #${order.id}`}
          </h1>
          <p className="text-sm text-gray-400 mt-1">Placed {formatDate(order.created_at)}</p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded-full font-medium capitalize">
          {order.status}
        </span>
      </div>

      {/* Seller sub-orders */}
      <div className="space-y-4 mb-6">
        {order.seller_orders.map(so => (
          <div key={so.id} className="border border-gray-100 rounded-xl overflow-hidden">
            <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
              <span className="text-xs font-medium text-gray-500">Seller order #{so.id}</span>
              <span className="text-xs bg-white border border-gray-200 px-2 py-0.5 rounded-full capitalize">
                {so.status}
              </span>
            </div>
            <div className="divide-y divide-gray-100">
              {so.items.map(item => (
                <div key={item.id} className="flex items-center justify-between px-4 py-3 text-sm">
                  <div>
                    <p className="text-gray-900">{item.product_name}</p>
                    {item.variant_name && <p className="text-xs text-gray-400">{item.variant_name}</p>}
                    <p className="text-xs text-gray-400">Qty {item.quantity}</p>
                  </div>
                  <span className="text-gray-900 font-medium">
                    {formatPrice(item.subtotal, order.currency)}
                  </span>
                </div>
              ))}
            </div>
            {so.tracking_number && (
              <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-100 text-xs text-gray-500">
                Tracking: <span className="font-medium text-gray-900">{so.tracking_number}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="border border-gray-100 rounded-xl p-5 mb-6">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between text-gray-500">
            <span>Subtotal</span>
            <span>{formatPrice(order.subtotal, order.currency)}</span>
          </div>
          {order.discount_amount > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount</span>
              <span>-{formatPrice(order.discount_amount, order.currency)}</span>
            </div>
          )}
          {order.shipping_amount > 0 && (
            <div className="flex justify-between text-gray-500">
              <span>Shipping</span>
              <span>{formatPrice(order.shipping_amount, order.currency)}</span>
            </div>
          )}
          <div className="flex justify-between text-gray-900 font-semibold pt-2 border-t border-gray-100">
            <span>Total</span>
            <span>{formatPrice(order.total, order.currency)}</span>
          </div>
        </div>
      </div>

      {/* Shipping address */}
      {order.shipping_address && (
        <div className="border border-gray-100 rounded-xl p-5 mb-6 text-sm">
          <h3 className="font-medium text-gray-900 mb-2">Shipping address</h3>
          <p className="text-gray-500">
            {order.shipping_address.recipient_name}<br />
            {order.shipping_address.address_line1}
            {order.shipping_address.address_line2 && <>, {order.shipping_address.address_line2}</>}<br />
            {order.shipping_address.city}, {order.shipping_address.country}
          </p>
        </div>
      )}

      {canCancel && (
        <button
          onClick={() => {
            if (confirm('Cancel this order?')) cancelOrder.mutate(order.id)
          }}
          disabled={cancelOrder.isPending}
          className="text-sm text-red-600 hover:underline disabled:opacity-50"
        >
          Cancel order
        </button>
      )}
    </div>
  )
}