import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight, ShieldCheck, Truck,
  RefreshCw, Star, TrendingUp, Store, Package
} from 'lucide-react'
import ProductCard from '@/components/products/ProductCard'
import { productsApi } from '@/lib/api/products'
import type { ProductListItem } from '@/types/product'

const CATEGORIES = [
  { name: 'Electronics',   emoji: '💻', q: 'Electronics',  bg: 'bg-blue-50'   },
  { name: 'Clothing',      emoji: '👕', q: 'Clothing',      bg: 'bg-purple-50' },
  { name: 'Home & Living', emoji: '🏡', q: 'Home',          bg: 'bg-amber-50'  },
  { name: 'Sports',        emoji: '⚽', q: 'Sports',        bg: 'bg-green-50'  },
  { name: 'Beauty',        emoji: '✨', q: 'Beauty',        bg: 'bg-pink-50'   },
  { name: 'Books',         emoji: '📚', q: 'Books',         bg: 'bg-orange-50' },
]

const TRUST = [
  { icon: ShieldCheck, label: 'Secure checkout',  sub: 'SSL encrypted payments'  },
  { icon: Truck,       label: 'Fast delivery',    sub: 'From verified sellers'    },
  { icon: RefreshCw,   label: 'Easy returns',     sub: '30-day return policy'     },
  { icon: Star,        label: 'Verified sellers', sub: 'Curated marketplace'      },
]

function CardSkeleton() {
  return (
    <div className="bg-white border border-gray-100 rounded-xl overflow-hidden animate-pulse">
      <div className="aspect-square bg-gray-100" />
      <div className="p-4 space-y-2">
        <div className="h-3 bg-gray-100 rounded w-1/3" />
        <div className="h-3 bg-gray-100 rounded w-3/4" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
      </div>
    </div>
  )
}

export default function HomePage() {
  const [featured, setFeatured] = useState<ProductListItem[]>([])
  const [recent,   setRecent]   = useState<ProductListItem[]>([])
  const [loading,  setLoading]  = useState(true)

  useEffect(() => {
    Promise.all([
      productsApi.list({ is_featured: true, per_page: 4 }),
      productsApi.list({ per_page: 8, sort_by: 'created_at', sort_dir: 'desc' }),
    ])
      .then(([feat, rec]) => {
        setFeatured(feat.items)
        setRecent(rec.items)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-white">

      {/* HERO */}
      <section className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 bg-white/10 text-gray-300 text-xs px-3 py-1.5 rounded-full mb-6 border border-white/10">
              <TrendingUp className="w-3.5 h-3.5" />
              Multi-seller marketplace
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold leading-tight tracking-tight mb-6">
              Everything you need,{' '}
              <span className="text-gray-400">from sellers you can trust</span>
            </h1>
            <p className="text-gray-400 text-lg mb-10 leading-relaxed max-w-xl">
              Discover products from verified independent sellers.
              Every seller is reviewed and approved before going live —
              so you shop with confidence, every time.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/products"
                className="inline-flex items-center gap-2 bg-white text-gray-900 px-6 py-3 rounded-xl font-medium hover:bg-gray-100 transition-colors"
              >
                Browse products
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/account/become-seller"
                className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
              >
                <Store className="w-4 h-4" />
                Become a seller
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST STRIP */}
      <section className="border-b border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {TRUST.map(({ icon: Icon, label, sub }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-gray-700" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{label}</p>
                  <p className="text-xs text-gray-500">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xl font-semibold text-gray-900">Shop by category</h2>
            <Link to="/products" className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1 transition-colors">
              All products <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {CATEGORIES.map(({ name, emoji, q, bg }) => (
              <Link
                key={name}
                to={`/products?search=${encodeURIComponent(q)}`}
                className="flex flex-col items-center gap-2.5 p-4 rounded-2xl hover:bg-gray-50 transition-colors group"
              >
                <div className={`w-14 h-14 ${bg} rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-200`}>
                  {emoji}
                </div>
                <span className="text-xs text-gray-600 font-medium text-center leading-tight">{name}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURED */}
      {(loading || featured.length > 0) && (
        <section className="py-14 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Featured products</h2>
                <p className="text-sm text-gray-400 mt-0.5">Hand-picked by our team</p>
              </div>
              <Link to="/products?is_featured=true" className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1">
                See all <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {loading
                ? Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
                : featured.map(p => <ProductCard key={p.id} product={p} />)
              }
            </div>
          </div>
        </section>
      )}

      {/* NEW ARRIVALS */}
      <section className="py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">New arrivals</h2>
              <p className="text-sm text-gray-400 mt-0.5">Just added by our sellers</p>
            </div>
            <Link to="/products" className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1">
              Browse all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
            </div>
          ) : recent.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {recent.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          ) : (
            <div className="text-center py-20">
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Package className="w-8 h-8 text-gray-300" />
              </div>
              <p className="text-sm font-medium text-gray-900 mb-1">No products yet</p>
              <p className="text-xs text-gray-400 mb-6">
                Check back soon — sellers are adding products every day.
              </p>
              <Link
                to="/account/become-seller"
                className="inline-flex items-center gap-2 text-sm text-gray-900 font-medium border border-gray-200 px-5 py-2.5 rounded-xl hover:bg-gray-50 transition-colors"
              >
                Be the first to sell here <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* SELLER CTA */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-xl mx-auto text-center">
            <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-white/10">
              <Store className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Ready to start selling?</h2>
            <p className="text-gray-400 mb-8 leading-relaxed">
              Apply in minutes. Our team reviews every seller before approval,
              so customers know they can trust every store on Free Commerce.
            </p>
            <Link
              to="/account/become-seller"
              className="inline-flex items-center gap-2 bg-white text-gray-900 px-8 py-3.5 rounded-xl font-medium hover:bg-gray-100 transition-colors"
            >
              Apply to sell <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-gray-100 bg-white py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 bg-gray-900 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs font-bold">FC</span>
              </div>
              <span className="text-sm font-semibold text-gray-900">Free Commerce</span>
            </div>
            <p className="text-xs text-gray-400 order-last sm:order-0">
              © {new Date().getFullYear()} Free Commerce. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              {['Privacy', 'Terms', 'Contact'].map(l => (
                <Link key={l} to="#" className="text-xs text-gray-400 hover:text-gray-900 transition-colors">{l}</Link>
              ))}
            </div>
          </div>
        </div>
      </footer>

    </div>
  )
}
