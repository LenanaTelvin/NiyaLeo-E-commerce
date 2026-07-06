import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ShoppingCart } from 'lucide-react'
import type { ProductListItem } from '@/types/product'
import { useCartStore } from '@/lib/store/cartStore'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api/client'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)

interface Props { product: ProductListItem }

export default function ProductCard({ product }: Props) {
  const { increment } = useCartStore()
  const [adding, setAdding] = useState(false)

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
    <Link to={`/products/${product.id}`} className="group block">
      <div className="bg-white border border-gray-100 rounded-xl overflow-hidden hover:border-gray-300 hover:shadow-md transition-all duration-200">

        {/* Image */}
        <div className="relative aspect-square bg-gray-50 overflow-hidden">
          {product.primary_image_url ? (
            <img
              src={product.primary_image_url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="w-14 h-14 bg-gray-200 rounded-xl" />
            </div>
          )}

          {savingsPct && (
            <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-medium px-2 py-0.5 rounded-full">
              -{savingsPct}%
            </span>
          )}
          {product.is_featured && (
            <span className="absolute top-2 right-2 bg-gray-900 text-white text-xs font-medium px-2 py-0.5 rounded-full">
              Featured
            </span>
          )}
        </div>

        {/* Info */}
        <div className="p-4">
          {product.category && (
            <p className="text-xs text-gray-400 mb-1">{product.category.name}</p>
          )}
          <h3 className="text-sm font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-gray-700">
            {product.name}
          </h3>
          {product.short_description && (
            <p className="text-xs text-gray-400 line-clamp-2 mb-3">
              {product.short_description}
            </p>
          )}

          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <span className="text-base font-semibold text-gray-900">
                {formatPrice(product.price)}
              </span>
              {product.compare_price && (
                <span className="text-xs text-gray-400 line-through ml-1.5">
                  {formatPrice(product.compare_price)}
                </span>
              )}
            </div>

            <button
              onClick={handleAdd}
              disabled={adding || product.stock_quantity === 0}
              className="shrink-0 p-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ShoppingCart className="w-4 h-4" />
            </button>
          </div>

          {product.stock_quantity === 0 && (
            <p className="text-xs text-red-500 mt-2">Out of stock</p>
          )}
        </div>
      </div>
    </Link>
  )
}
