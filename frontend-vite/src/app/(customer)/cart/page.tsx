import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Minus, Plus, Trash2, Heart, ArrowLeft, ShoppingBag } from 'lucide-react'
import {
  useCart, useUpdateCartItem, useRemoveCartItem,
  useSaveForLater, useMoveToCart,
} from '@/lib/hooks/useCart'
import type { CartItem } from '@/types/cart'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(n)

export default function CartPage() {
  const { data: cart, isLoading, isError } = useCart()

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 animate-pulse space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-28 bg-gray-100 rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError || !cart) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-20 text-center">
        <p className="text-gray-900 font-medium mb-1">Couldn't load your cart</p>
        <p className="text-sm text-gray-400">Please try refreshing the page.</p>
      </div>
    )
  }

  if (cart.items.length === 0 && cart.saved_for_later.length === 0) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-20 text-center">
        <ShoppingBag className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-900 font-medium mb-1">Your cart is empty</p>
        <p className="text-sm text-gray-400 mb-5">Browse products and add something you like.</p>
        <Link
          to="/products"
          className="inline-block bg-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-gray-800 transition-colors"
        >
          Browse products
        </Link>
      </div>
    )
  }

  // Group active items by seller for a marketplace-style cart
  const groups = new Map<number, { sellerName: string; items: CartItem[] }>()
  cart.items.forEach(item => {
    const sellerId = item.seller?.id ?? 0
    const sellerName = item.seller?.store_name ?? 'Unknown seller'
    if (!groups.has(sellerId)) groups.set(sellerId, { sellerName, items: [] })
    groups.get(sellerId)!.items.push(item)
  })

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <Link to="/products" className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4" /> Continue shopping
      </Link>

      <h1 className="text-2xl font-semibold text-gray-900 mb-6">
        Cart <span className="text-gray-400 font-normal">({cart.summary.total_quantity})</span>
      </h1>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Items */}
        <div className="lg:col-span-2 space-y-6">
          {[...groups.entries()].map(([sellerId, group]) => (
            <div key={sellerId} className="border border-gray-100 rounded-xl overflow-hidden">
              <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-100">
                <p className="text-xs font-medium text-gray-500">{group.sellerName}</p>
              </div>
              <div className="divide-y divide-gray-100">
                {group.items.map(item => (
                  <CartRow key={item.id} item={item} />
                ))}
              </div>
            </div>
          ))}

          {cart.saved_for_later.length > 0 && (
            <div>
              <h2 className="text-sm font-medium text-gray-900 mb-3">
                Saved for later ({cart.saved_for_later.length})
              </h2>
              <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
                {cart.saved_for_later.map(item => (
                  <SavedRow key={item.id} item={item} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Summary */}
        {cart.items.length > 0 && (
          <div className="lg:col-span-1">
            <div className="border border-gray-100 rounded-xl p-5 sticky top-24">
              <h2 className="text-sm font-medium text-gray-900 mb-4">Order summary</h2>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-gray-500">
                  <span>Subtotal</span>
                  <span>{formatPrice(cart.summary.subtotal)}</span>
                </div>
                {cart.summary.savings > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Savings</span>
                    <span>-{formatPrice(cart.summary.savings)}</span>
                  </div>
                )}
                {cart.summary.discount_amount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount{cart.coupon_code ? ` (${cart.coupon_code})` : ''}</span>
                    <span>-{formatPrice(cart.summary.discount_amount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-gray-900 font-semibold pt-2 border-t border-gray-100">
                  <span>Total</span>
                  <span>{formatPrice(cart.summary.total)}</span>
                </div>
              </div>

              <Link
                to="/checkout"
                className="mt-5 block text-center bg-gray-900 text-white text-sm font-medium py-2.5 rounded-lg hover:bg-gray-800 transition-colors"
              >
                Proceed to checkout
              </Link>

              {cart.summary.seller_count > 1 && (
                <p className="text-xs text-gray-400 mt-3 text-center">
                  Items from {cart.summary.seller_count} sellers — shipped separately
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function CartRow({ item }: { item: CartItem }) {
  const [quantity, setQuantity] = useState(item.quantity)
  const updateItem = useUpdateCartItem()
  const removeItem = useRemoveCartItem()
  const saveForLater = useSaveForLater()

  const commitQuantity = (next: number) => {
    const clamped = Math.max(1, next)
    setQuantity(clamped)
    updateItem.mutate({ itemId: item.id, data: { quantity: clamped } })
  }

  return (
    <div className="flex gap-4 p-4">
      <Link to={`/products/${item.product_id}`} className="shrink-0 w-20 h-20 bg-gray-50 rounded-lg overflow-hidden">
        {item.product?.primary_image_url ? (
          <img src={item.product.primary_image_url} alt={item.product.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-8 h-8 bg-gray-200 rounded-lg" />
          </div>
        )}
      </Link>

      <div className="flex-1 min-w-0">
        <Link to={`/products/${item.product_id}`} className="text-sm font-medium text-gray-900 hover:underline line-clamp-1">
          {item.product?.name ?? 'Product'}
        </Link>
        {item.variant && (
          <p className="text-xs text-gray-400 mt-0.5">
            {Object.entries(item.variant.attributes ?? {}).map(([k, v]) => `${k}: ${v}`).join(', ')}
          </p>
        )}

        <div className="flex items-center gap-2 mt-2">
          <span className="text-sm font-semibold text-gray-900">{formatPrice(item.unit_price)}</span>
          {item.original_price && item.original_price > item.unit_price && (
            <span className="text-xs text-gray-400 line-through">{formatPrice(item.original_price)}</span>
          )}
        </div>

        <div className="flex items-center gap-4 mt-3">
          <div className="flex items-center border border-gray-200 rounded-lg">
            <button
              onClick={() => commitQuantity(quantity - 1)}
              disabled={updateItem.isPending}
              className="p-1.5 text-gray-500 hover:text-gray-900 disabled:opacity-40"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <span className="w-8 text-center text-sm">{quantity}</span>
            <button
              onClick={() => commitQuantity(quantity + 1)}
              disabled={updateItem.isPending}
              className="p-1.5 text-gray-500 hover:text-gray-900 disabled:opacity-40"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={() => saveForLater.mutate(item.id)}
            disabled={saveForLater.isPending}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-700"
          >
            <Heart className="w-3.5 h-3.5" /> Save for later
          </button>

          <button
            onClick={() => removeItem.mutate(item.id)}
            disabled={removeItem.isPending}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-600"
          >
            <Trash2 className="w-3.5 h-3.5" /> Remove
          </button>
        </div>
      </div>

      <div className="text-sm font-medium text-gray-900 shrink-0">
        {formatPrice(item.subtotal)}
      </div>
    </div>
  )
}

function SavedRow({ item }: { item: CartItem }) {
  const moveToCart = useMoveToCart()
  const removeItem = useRemoveCartItem()

  return (
    <div className="flex gap-4 p-4">
      <div className="shrink-0 w-16 h-16 bg-gray-50 rounded-lg overflow-hidden">
        {item.product?.primary_image_url ? (
          <img src={item.product.primary_image_url} alt={item.product.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-6 h-6 bg-gray-200 rounded-lg" />
          </div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 line-clamp-1">{item.product?.name ?? 'Product'}</p>
        <span className="text-sm text-gray-900 font-semibold">{formatPrice(item.unit_price)}</span>

        <div className="flex items-center gap-4 mt-2">
          <button
            onClick={() => moveToCart.mutate(item.id)}
            disabled={moveToCart.isPending}
            className="text-xs text-gray-900 underline hover:no-underline"
          >
            Move to cart
          </button>
          <button
            onClick={() => removeItem.mutate(item.id)}
            disabled={removeItem.isPending}
            className="text-xs text-gray-400 hover:text-red-600"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  )
}