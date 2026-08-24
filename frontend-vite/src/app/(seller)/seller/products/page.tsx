import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Pencil, Trash2, Eye, EyeOff } from 'lucide-react'
import { useMyProducts, useDeleteProduct, useTogglePublish } from '@/lib/hooks/useProducts'

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'KES' }).format(n)

export default function SellerProductsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useMyProducts({ page, per_page: 20 })
  const deleteProduct = useDeleteProduct()
  const togglePublish = useTogglePublish()

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Products</h1>
        <Link
          to="/seller/products/new"
          className="flex items-center gap-2 bg-gray-900 text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <Plus className="w-4 h-4" /> Add product
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
          {data.items.map(product => (
            <div key={product.id} className="flex items-center gap-4 p-4">
              <div className="w-14 h-14 bg-gray-50 rounded-lg overflow-hidden shrink-0">
                {product.primary_image_url ? (
                  <img src={product.primary_image_url} alt={product.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="w-6 h-6 bg-gray-200 rounded" />
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{product.name}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-sm text-gray-500">{formatPrice(product.price)}</span>
                  <span className="text-xs text-gray-400">· {product.stock_quantity} in stock</span>
                  <StatusBadge published={product.is_published} status={product.status} />
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => togglePublish.mutate({ id: product.id, is_published: !product.is_published })}
                  className="p-2 text-gray-400 hover:text-gray-900 rounded-lg hover:bg-gray-50"
                  title={product.is_published ? 'Unpublish' : 'Publish'}
                >
                  {product.is_published ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
                <Link
                  to={`/seller/products/${product.id}/edit`}
                  className="p-2 text-gray-400 hover:text-gray-900 rounded-lg hover:bg-gray-50"
                >
                  <Pencil className="w-4 h-4" />
                </Link>
                <button
                  onClick={() => {
                    if (confirm(`Archive "${product.name}"?`)) deleteProduct.mutate(product.id)
                  }}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
          <p className="text-gray-900 font-medium mb-1">No products yet</p>
          <p className="text-sm text-gray-400 mb-4">Add your first product to start selling.</p>
          <Link
            to="/seller/products/new"
            className="inline-block bg-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-gray-800"
          >
            Add product
          </Link>
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {data.page} of {data.total_pages}</span>
          <button
            disabled={page >= data.total_pages}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ published, status }: { published: boolean; status: string }) {
  if (!published) {
    return <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Draft</span>
  }
  if (status === 'out_of_stock') {
    return <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">Out of stock</span>
  }
  return <span className="text-xs bg-green-50 text-green-600 px-2 py-0.5 rounded-full">Live</span>
}