import { useParams } from 'react-router-dom'
import { Store } from 'lucide-react'
import ProductCard from '@/components/products/ProductCard'
import { useSellerIdFromSlug, useStoreTheme } from '@/lib/hooks/useStores'
import { useProducts } from '@/lib/hooks/useProducts'
import { useMemo } from 'react'

export default function StorePage() {
  const { slug } = useParams<{ slug: string }>()
  const { data: theme, isLoading: themeLoading, isError: themeError } = useStoreTheme(slug)

  // Need the seller's numeric id to filter products — theme config doesn't
  // include it, so we look it up via the public seller detail endpoint.
  // (sellersApi.getMe is for the authed self; this reuses the same
  // GET /sellers/{identifier} wildcard, just passing the slug.)
  const { data: sellerId } = useSellerIdFromSlug(slug)

  const { data: products, isLoading: productsLoading } = useProducts({
    ...(sellerId && { seller_id: sellerId }),
    per_page: 24,
  })

  // CSS custom properties so the whole page (including ProductCard)
  // can pick up the seller's theme colors without prop-drilling
  const themeVars = useMemo(() => {
    if (!theme) return {}
    return {
      '--store-primary': theme.primary_color,
      '--store-secondary': theme.secondary_color,
      '--store-accent': theme.accent_color,
      '--store-bg': theme.background_color,
      '--store-text': theme.text_color,
      fontFamily: theme.font_family || undefined,
    } as React.CSSProperties
  }, [theme])

  if (themeLoading) {
    return <div className="max-w-6xl mx-auto px-4 py-8 h-96 bg-gray-100 rounded-xl animate-pulse" />
  }

  if (themeError || !theme) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center">
        <Store className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-900 font-medium">Store not found</p>
      </div>
    )
  }

  return (
    <div style={{ backgroundColor: theme.background_color, color: theme.text_color, ...themeVars }}>
      {/* Hero */}
      <div
        className="py-16 px-4 sm:px-6 text-center"
        style={{ backgroundColor: theme.primary_color }}
      >
        {theme.store_logo && (
          <img
            src={theme.store_logo}
            alt={theme.store_name}
            className="w-16 h-16 rounded-xl object-cover mx-auto mb-4 border-2 border-white/20"
          />
        )}
        <h1 className="text-3xl font-bold text-white mb-2">{theme.store_name}</h1>
        {theme.store_description && (
          <p className="text-white/80 max-w-lg mx-auto">{theme.store_description}</p>
        )}
      </div>

      {/* Products */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <h2 className="text-lg font-semibold mb-6" style={{ color: theme.text_color }}>
          Products
        </h2>

        {productsLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="aspect-3/4 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : products && products.items.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {products.items.map(p => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl">
            <p className="text-gray-400">No products yet</p>
          </div>
        )}
      </div>
    </div>
  )
}