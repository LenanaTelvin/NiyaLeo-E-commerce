import { useEffect, useState } from 'react'
import { SlidersHorizontal, X, Search } from 'lucide-react'
import ProductCard from '@/components/products/ProductCard'
import { useProducts, type ProductFilters, type SortBy, type SortDir } from '@/lib/hooks/useProducts'
import { useCategories } from '@/lib/hooks/useCategories'
import { useSearchParams } from 'react-router-dom'

// sort_by + sort_dir combined into single-select options for the UI
const SORT_OPTIONS: { value: string; label: string; sort_by: SortBy; sort_dir: SortDir }[] = [
  { value: 'newest', label: 'Newest', sort_by: 'created_at', sort_dir: 'desc' },
  { value: 'price_asc', label: 'Price: Low to High', sort_by: 'price', sort_dir: 'asc' },
  { value: 'price_desc', label: 'Price: High to Low', sort_by: 'price', sort_dir: 'desc' },
  { value: 'name_asc', label: 'Name: A to Z', sort_by: 'name', sort_dir: 'asc' },
]

export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState<ProductFilters>(() => ({
    page: 1,
    per_page: 24,
    sort_by: 'created_at',
    sort_dir: 'desc',
    search: searchParams.get('search') || undefined,
    category_id: searchParams.get('category_id') ? Number(searchParams.get('category_id')) : undefined,
  }))
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '')
  const [sortValue, setSortValue] = useState('newest')
  const [showFilters, setShowFilters] = useState(false)
  // Inbound: when the URL changes from outside this page (header nav click, back button),
  // pull the new search/category into local state
  useEffect(() => {
    const urlSearch = searchParams.get('search') || undefined
    const urlCategory = searchParams.get('category_id') ? Number(searchParams.get('category_id')) : undefined

     setFilters(f => {
         if (f.search === urlSearch && f.category_id === urlCategory) return f
        return { ...f, search: urlSearch, category_id: urlCategory, page: 1 }
  })
  if (urlSearch !== undefined) setSearchInput(urlSearch)
}, [searchParams])

// Outbound: keep the URL in sync with active filters, so links are shareable/bookmarkable

  useEffect(() => {
    const params: Record<string, string> = {}
    if (filters.search) params.search = filters.search
    if (filters.category_id) params.category_id = String(filters.category_id)
    if (filters.min_price) params.min_price = String(filters.min_price)
    if (filters.max_price) params.max_price = String(filters.max_price)
    if (filters.is_featured) params.is_featured = 'true'
    if (filters.page && filters.page > 1) params.page = String(filters.page)
    setSearchParams(params, { replace: true })
  }, [filters])



  // Debounce search so we don't fire a request per keystroke
  useEffect(() => {
    const t = setTimeout(() => {
      setFilters(f => ({ ...f, search: searchInput || undefined, page: 1 }))
    }, 400)
    return () => clearTimeout(t)
  }, [searchInput])

  const { data, isLoading, isFetching, isError } = useProducts(filters)
  const { data: categories } = useCategories()

  const updateFilter = (patch: Partial<ProductFilters>) =>
    setFilters(f => ({ ...f, ...patch, page: 1 }))

  const handleSortChange = (value: string) => {
    setSortValue(value)
    const opt = SORT_OPTIONS.find(o => o.value === value)
    if (opt) updateFilter({ sort_by: opt.sort_by, sort_dir: opt.sort_dir })
  }

  const clearFilters = () => {
    setSearchInput('')
    setSortValue('newest')
    setFilters({ page: 1, per_page: 24, sort_by: 'created_at', sort_dir: 'desc' })
  }

  const activeFilterCount = [
    filters.category_id,
    filters.min_price,
    filters.max_price,
    filters.is_featured,
  ].filter(v => v !== undefined && v !== false).length

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Products</h1>
          {data && (
            <p className="text-sm text-gray-400 mt-1">
              {data.total} item{data.total !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        <button
          onClick={() => setShowFilters(s => !s)}
          className="lg:hidden flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-gray-900 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Search + sort bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            id="product-search"
            name="search"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Search products..."
           className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300"
         />
        </div>

        <select
          value={sortValue}
          onChange={e => handleSortChange(e.target.value)}
          className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900/10"
        >
          {SORT_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="flex gap-8">
        {/* Filters sidebar */}
        <aside className={`${showFilters ? 'block' : 'hidden'} lg:block w-full lg:w-56 shrink-0 space-y-6`}>
          {activeFilterCount > 0 && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-700"
            >
              <X className="w-3 h-3" /> Clear filters
            </button>
          )}

          {/* Category */}
          <div>
            <h3 className="text-xs font-medium text-gray-900 uppercase tracking-wide mb-3">Category</h3>
            <div className="space-y-1.5">
              <button
                onClick={() => updateFilter({ category_id: undefined })}
                className={`block text-sm ${!filters.category_id ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-900'}`}
              >
                All
              </button>
              {categories?.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => updateFilter({ category_id: cat.id })}
                  className={`block text-sm ${filters.category_id === cat.id ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-900'}`}
                >
                  {cat.name}
                </button>
              ))}
            </div>
          </div>

          {/* Price range */}
          <div>
            <h3 className="text-xs font-medium text-gray-900 uppercase tracking-wide mb-3">Price</h3>
            <div className="flex items-center gap-2">
              <input
                type="number"
                id="min-price"
                name="min_price"
                min={0}
                placeholder="Min"
                value={filters.min_price ?? ''}
                onChange={e => updateFilter({ min_price: e.target.value ? Number(e.target.value) : undefined })}
                className="w-full px-2 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/10"
              />
              <span className="text-gray-300">–</span>
              <input
                type="number"
                min={0}
                placeholder="Max"
                value={filters.max_price ?? ''}
                onChange={e => updateFilter({ max_price: e.target.value ? Number(e.target.value) : undefined })}
                className="w-full px-2 py-1.5 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/10"
              />
            </div>
          </div>

          {/* Featured only */}
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.is_featured ?? false}
              onChange={e => updateFilter({ is_featured: e.target.checked || undefined })}
              className="rounded border-gray-300 text-gray-900 focus:ring-gray-900/10"
            />
            Featured only
          </label>
        </aside>

        {/* Product grid */}
        <div className="flex-1 min-w-0">
          {isLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="aspect-3/4 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : isError ? (
            <div className="text-center py-20">
              <p className="text-gray-900 font-medium mb-1">Couldn't load products</p>
              <p className="text-sm text-gray-400">Check your connection and try again.</p>
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <div className={`grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4 ${isFetching ? 'opacity-60' : ''} transition-opacity`}>
                {data.items.map(product => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>

              {data.total_pages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <button
                    disabled={filters.page === 1}
                    onClick={() => setFilters(f => ({ ...f, page: (f.page ?? 1) - 1 }))}
                    className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-500 px-2">
                    Page {data.page} of {data.total_pages}
                  </span>
                  <button
                    disabled={data.page >= data.total_pages}
                    onClick={() => setFilters(f => ({ ...f, page: (f.page ?? 1) + 1 }))}
                    className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-20">
              <p className="text-gray-900 font-medium mb-1">No products found</p>
              <p className="text-sm text-gray-400">Try adjusting your filters or search.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}