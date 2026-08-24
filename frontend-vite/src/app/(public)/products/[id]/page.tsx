import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ShoppingCart, Minus, Plus, ChevronLeft, Store } from 'lucide-react'
import { toast } from 'sonner'
import { useProduct } from '@/lib/hooks/useProducts'
import { useCartStore } from '@/lib/store/cartStore'
import { apiClient } from '@/lib/api/client'
import type { ProductVariant } from '@/types/product'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: product, isLoading, isError } = useProduct(id)
  const { increment } = useCartStore()

  const [activeImage, setActiveImage] = useState(0)
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [adding, setAdding] = useState(false)

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 animate-pulse">
        <div className="grid md:grid-cols-2 gap-10">
          <div className="aspect-square bg-gray-100 rounded-xl" />
          <div className="space-y-4">
            <div className="h-6 bg-gray-100 rounded w-2/3" />
            <div className="h-4 bg-gray-100 rounded w-1/3" />
            <div className="h-24 bg-gray-100 rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (isError || !product) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-20 text-center">
        <p className="text-gray-900 font-medium mb-1">Product not found</p>
        <p className="text-sm text-gray-400 mb-4">It may have been removed or is no longer available.</p>
        <Link to="/products" className="text-sm text-gray-900 underline">Back to products</Link>
      </div>
    )
  }

  const images = product.images.length > 0
    ? [...product.images].sort((a, b) => a.sort_order - b.sort_order)
    : []

  const effectivePrice = selectedVariant?.price_override ?? product.price
  const effectiveStock = selectedVariant?.stock_quantity ?? product.stock_quantity
  const outOfStock = effectiveStock === 0 && !product.allow_backorder

  const savingsPct = product.compare_price
    ? Math.round(((product.compare_price - product.price) / product.compare_price) * 100)
    : null

  // Group variant attributes for selector, e.g. { color: ["red","blue"], size: ["S","M"] }
  const variantGroups: Record<string, string[]> = {}
  product.variants.forEach(v => {
    if (!v.attributes) return
    Object.entries(v.attributes).forEach(([key, val]) => {
      if (!variantGroups[key]) variantGroups[key] = []
      if (!variantGroups[key].includes(val)) variantGroups[key].push(val)
    })
  })

  const handleAddToCart = async () => {
    setAdding(true)
    try {
      await apiClient.post('/api/v1/cart/items', {
        product_id: product.id,
        variant_id: selectedVariant?.id,
        quantity,
      })
      increment()
      toast.success('Added to cart')
    } catch {
      toast.error('Could not add to cart — sign in first')
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <Link to="/products" className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-gray-900 mb-6">
        <ChevronLeft className="w-4 h-4" /> Back to products
      </Link>

      <div className="grid md:grid-cols-2 gap-10">
        {/* Images */}
        <div>
          <div className="aspect-square bg-gray-50 rounded-xl overflow-hidden mb-3">
            {images.length > 0 ? (
              <img
                src={images[activeImage]?.url}
                alt={images[activeImage]?.alt_text || product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <div className="w-16 h-16 bg-gray-200 rounded-xl" />
              </div>
            )}
          </div>
          {images.length > 1 && (
            <div className="flex gap-2">
              {images.map((img, i) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(i)}
                  className={`w-16 h-16 rounded-lg overflow-hidden border-2 transition-colors ${
                    i === activeImage ? 'border-gray-900' : 'border-transparent'
                  }`}
                >
                  <img src={img.url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div>
          {product.category && (
            <p className="text-xs text-gray-400 mb-2">{product.category.name}</p>
          )}
          <h1 className="text-2xl font-semibold text-gray-900 mb-3">{product.name}</h1>
          {product.seller && (
            <Link
              to={`/stores/${product.seller.store_slug}`}
              className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 mb-4"
            >
              <div className="flex items-center gap-2 mb-4">
                <Store className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-500">{product.seller.store_name}</span>
              </div>
            </Link>
          )}

          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl font-semibold text-gray-900">{formatPrice(effectivePrice)}</span>
            {product.compare_price && (
              <>
                <span className="text-base text-gray-400 line-through">{formatPrice(product.compare_price)}</span>
                <span className="text-xs font-medium bg-red-50 text-red-600 px-2 py-0.5 rounded-full">
                  -{savingsPct}%
                </span>
              </>
            )}
          </div>

          {product.short_description && (
            <p className="text-sm text-gray-500 mb-6">{product.short_description}</p>
          )}

          {/* Variant selectors */}
          {Object.entries(variantGroups).map(([attr, values]) => (
            <div key={attr} className="mb-4">
              <h3 className="text-xs font-medium text-gray-900 uppercase tracking-wide mb-2">{attr}</h3>
              <div className="flex flex-wrap gap-2">
                {values.map(val => {
                  const matchingVariant = product.variants.find(v => v.attributes?.[attr] === val)
                  const isSelected = selectedVariant?.attributes?.[attr] === val
                  return (
                    <button
                      key={val}
                      onClick={() => matchingVariant && setSelectedVariant(matchingVariant)}
                      className={`px-3 py-1.5 text-sm border rounded-lg transition-colors ${
                        isSelected
                          ? 'border-gray-900 bg-gray-900 text-white'
                          : 'border-gray-200 text-gray-700 hover:border-gray-400'
                      }`}
                    >
                      {val}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}

          {/* Quantity + Add to cart */}
          <div className="flex items-center gap-3 mt-6 mb-6">
            <div className="flex items-center border border-gray-200 rounded-lg">
              <button
                onClick={() => setQuantity(q => Math.max(1, q - 1))}
                className="p-2 text-gray-500 hover:text-gray-900"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="w-10 text-center text-sm">{quantity}</span>
              <button
                onClick={() => setQuantity(q => q + 1)}
                className="p-2 text-gray-500 hover:text-gray-900"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={handleAddToCart}
              disabled={adding || outOfStock}
              className="flex-1 flex items-center justify-center gap-2 bg-gray-900 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ShoppingCart className="w-4 h-4" />
              {outOfStock ? 'Out of stock' : 'Add to cart'}
            </button>
          </div>

          {product.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {product.tags.map(tag => (
                <span key={tag.id} className="text-xs text-gray-400 bg-gray-50 px-2 py-1 rounded-full">
                  {tag.name}
                </span>
              ))}
            </div>
          )}

          {product.description && (
            <div className="pt-6 border-t border-gray-100">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Description</h3>
              <p className="text-sm text-gray-500 whitespace-pre-line">{product.description}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}