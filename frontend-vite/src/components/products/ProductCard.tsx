import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { ProductListItem } from '@/types/product'
import { useCartStore } from '@/lib/store/cartStore'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api/client'
import { ShoppingCart } from 'lucide-react'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(n)

interface Props { product: ProductListItem }

export default function ProductCard({ product }: Props) {
  const { increment } = useCartStore()
  const [adding, setAdding] = useState(false)
  const [hovered, setHovered] = useState(false)

  const handleAdd = async (e: React.MouseEvent) => {
    e.preventDefault()
    setAdding(true)
    try {
      await apiClient.post('/api/v1/cart/items', {
        product_id: product.id,
        quantity: 1,
      })
      increment()
      toast.success('Added to cart')
    } catch {
      toast.error('Could not add to cart — sign in first')
    } finally {
      setAdding(false)
    }
  }

  const savingsPct = product.compare_price
    ? Math.round(((product.compare_price - product.price) / product.compare_price) * 100)
    : null

  return (
    <Link
      to={`/products/${product.id}`}
      className="group block"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Card shell — sharp corners, shadow transitions */}
      <div
        className="relative overflow-hidden transition-all duration-300"
        style={{
          backgroundColor: '#f0f0f0',
          borderRadius: '4px',
          boxShadow: hovered
            ? '0 12px 40px rgba(0,0,0,0.15), 0 2px 8px rgba(0,0,0,0.08)'
            : '0 2px 8px rgba(0,0,0,0.06)',
          transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
          padding: '12px',
        }}
      >
        {/* Discount badge */}
        {savingsPct && (
          <span
            className="absolute top-2.5 left-2.5 z-10 text-xs font-bold px-2 py-0.5"
            style={{ backgroundColor: '#111', color: '#4ade80', borderRadius: '2px' }}
          >
            -{savingsPct}%
          </span>
        )}

        {/* Image */}
        <div className="relative aspect-square flex items-center justify-center"style={{ height: '180px' }}>
          {product.primary_image_url ? (
            <img
              src={product.primary_image_url}
              alt={product.name}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 group-hover:-translate-y-1"
              style={{
                borderRadius: '2px',
                boxShadow: hovered
                  ? '0 16px 40px rgba(0,0,0,0.18)'
                  : '0 4px 16px rgba(0,0,0,0.08)',
                transition: 'box-shadow 0.3s ease, transform 0.5s ease',
              }}
            />
          ) : (
            <div
              className="w-full h-full bg-gray-200 flex items-center justify-center"
              style={{ borderRadius: '2px' }}
            >
              <div className="w-10 h-10 bg-gray-300" style={{ borderRadius: '2px' }} />
            </div>
          )}

          {/* Out of stock */}
          {product.stock_quantity === 0 && (
            <div className="absolute inset-0 bg-white/60 flex items-center justify-center">
              <span
                className="text-xs font-medium text-gray-700 bg-white px-3 py-1"
                style={{ borderRadius: '2px' }}
              >
                Out of stock
              </span>
            </div>
          )}
        </div>

        {/* Quick add */}
        {product.stock_quantity > 0 && (
          <button
            onClick={handleAdd}
            disabled={adding}
            className="absolute bottom-2.5 right-2.5 p-2 opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200 disabled:opacity-50"
            style={{
              backgroundColor: '#111',
              color: '#4ade80',
              borderRadius: '2px',
            }}
            aria-label="Add to cart"
          >
            <ShoppingCart className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Info */}
      <div className="px-0.5 pt-3 pb-1 text-center">
        {product.category && (
          <p className="text-[10px] uppercase tracking-widest text-gray-400 mb-1">
            {product.category.name}
          </p>
        )}
        <h3 className="text-sm font-medium text-gray-900 line-clamp-1 mb-1.5 group-hover:text-green-700 transition-colors">
          {product.name}
        </h3>
        <div className="flex items-center justify-center gap-2">
          <span className="text-sm font-bold text-gray-900">
            {formatPrice(product.price)}
          </span>
          {product.compare_price && (
            <span className="text-xs text-gray-400 line-through">
              {formatPrice(product.compare_price)}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
