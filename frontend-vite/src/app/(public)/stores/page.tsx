import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Store, CheckCircle2 } from 'lucide-react'
import { usePublicSellers } from '@/lib/hooks/useStores'

export default function StoresDirectoryPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const { data, isLoading } = usePublicSellers({ page, per_page: 20, search: search || undefined })

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">All stores</h1>
        <p className="text-sm text-gray-400 mt-1">Browse every seller on Free Commerce</p>
      </div>

      <input
        type="text"
        value={search}
        onChange={e => { setSearch(e.target.value); setPage(1) }}
        placeholder="Search stores..."
        className="w-full max-w-sm mb-6 px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900/10"
      />

      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {data.items.map(seller => (
            <Link
              key={seller.id}
              to={`/stores/${seller.store_slug}`}
              className="border border-gray-100 rounded-xl overflow-hidden hover:border-gray-300 hover:shadow-sm transition-all"
            >
              <div className="aspect-3/1 bg-gray-50 relative">
                {seller.store_banner_url ? (
                  <img src={seller.store_banner_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Store className="w-6 h-6 text-gray-300" />
                  </div>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center gap-1.5 mb-1">
                  <p className="text-sm font-medium text-gray-900 truncate">{seller.store_name}</p>
                  {seller.is_verified && <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />}
                </div>
                {seller.store_description && (
                  <p className="text-xs text-gray-400 line-clamp-2">{seller.store_description}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
          <Store className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-900 font-medium">No stores found</p>
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