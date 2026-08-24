import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ArrowRight, Store } from 'lucide-react'
import ProductCard from '@/components/products/ProductCard'
import { productsApi } from '@/lib/api/products'
import type { ProductListItem } from '@/types/product'
import { useAuthStore } from '@/lib/store/authStore'

function CardSkeleton() {
  return (
    <div className="bg-gray-50 rounded-2xl overflow-hidden animate-pulse">
      <div className="aspect-4/5" />
    </div>
  )
}

export default function HomePage() {
  const role = useAuthStore(s => s.user?.role)
  const [products, setProducts] = useState<ProductListItem[]>([])
  const [loading, setLoading] = useState(true)

  if (role === 'admin') return <Navigate to="/admin/dashboard" replace />
  if (role === 'seller') return <Navigate to="/seller/dashboard" replace />

  useEffect(() => {
    productsApi.list({ per_page: 4, sort_by: 'created_at', sort_dir: 'desc' })
      .then(res => setProducts(res.items))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-white">

      {/* ── HERO ─────────────────────────────────────────────── */}
      <section className="border-b border-gray-100">
        <div className="max-w-3xl mx-auto px-6 py-16 lg:py-20 text-center">
          <h1 className="font-heading text-2xl sm:text-3xl lg:text-4xl leading-[1.3] tracking-normal text-gray-900 mb-6">
            <span className="font-bold">Build your website, with just a few clicks,</span>
            <br className="hidden sm:block" />
            <span className="font-light italic text-gray-600"> and sell to thousands of customers across Africa.</span>
          </h1>

          <p className="text-base text-gray-500 mb-8 leading-relaxed max-w-md mx-auto">
            Shop directly from verified sellers — handmade crafts to
            everyday essentials. Fast delivery to your doorstep.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/products"
              className="inline-flex items-center gap-2 bg-gray-900 text-white px-7 py-3.5 rounded-xl text-sm font-medium hover:bg-brand-green transition-colors"
            >
              Browse products <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/stores"
              className="inline-flex items-center gap-2 text-gray-600 px-7 py-3.5 rounded-xl text-sm font-medium border border-gray-200 hover:border-brand-green hover:text-brand-green hover:bg-brand-greenSoft transition-colors"
            >
              <Store className="w-4 h-4" />
              Browse stores
            </Link>
          </div>
        </div>
      </section>

      {/* ── LATEST PRODUCTS ──────────────────────────────────── */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-3 items-center mb-8">
            <div />
            <h2 className="text-2xl font-medium text-gray-900 text-center">Latest products</h2>
            <Link to="/products" className="text-sm text-gray-400 hover:text-brand-green flex items-center gap-1 justify-self-end transition-colors">
              Browse all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {!loading && products.length === 0 ? (
            <div className="max-w-md mx-auto py-16 text-center">
              <p className="text-base font-medium text-gray-900 mb-2">No products yet</p>
              <p className="text-sm text-gray-400 mb-6">
                Sellers are setting up their stores. Check back soon — or be the first.
              </p>
              <Link
                to="/account/become-seller"
                className="inline-flex items-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-xl text-sm font-medium hover:bg-brand-green transition-colors"
              >
                Start selling today <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-8">
              {loading
                ? Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)
                : products.map(p => <ProductCard key={p.id} product={p} />)
              }
            </div>
          )}
        </div>
      </section>

{/* ── BECOME A SELLER ─────────────────────────────────── */}
<section className="py-24 lg:py-32 border-t border-gray-100">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">

      {/* Text — left */}
      <div className="text-center lg:text-left">
        <h2 className="font-heading text-2xl lg:text-3xl font-medium text-gray-900 mb-3">
          Ready to start selling? Build with us today.
        </h2>
        <p className="text-gray-500 mb-8 leading-relaxed max-w-md mx-auto lg:mx-0">
          Apply in minutes and reach thousands of customers across Africa.
          Every seller is reviewed to keep the marketplace trusted.
        </p>
        <Link
          to="/account/become-seller"
          className="inline-flex items-center gap-2 bg-gray-900 text-white px-7 py-3.5 rounded-xl text-sm font-medium hover:bg-brand-green transition-colors"
        >
          Become a seller <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Image — right */}
      <div className="order-first lg:order-last">
        <img
          src="/seller-storefront-preview.jpg"
          alt="Preview of a seller's custom-built storefront"
          className="w-full max-w-sm mx-auto lg:mx-14 rounded-2xl border border-gray-100 shadow-sm"
        />
      </div>

    </div>
  </div>
</section>

      {/* ── FOOTER ───────────────────────────────────────────── */}
      <footer>
        {/* Green CTA bar */}
        <div className="bg-brand-green">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-white font-medium">
              Have questions? We'd love to hear from you.
            </p>
            <Link
              to="/contact"
              className="inline-flex items-center gap-2 bg-white text-brand-green text-sm font-medium px-6 py-3 rounded-full hover:bg-gray-50 transition-colors"
            >
              Contact us <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Black section */}
        <div className="bg-gray-900 text-gray-300">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
            <div className="flex flex-col sm:flex-row sm:items-start gap-10 mb-10">
              <p className="text-sm text-gray-400 max-w-xs leading-relaxed shrink-0">
                Ni Ya Leo is a leading online marketplace connecting buyers and
                sellers across Africa. We provide a platform for businesses to
                reach a wider audience and for customers to discover unique products.
              </p>

              <div className="flex flex-col sm:flex-row gap-10 sm:gap-16 sm:ml-auto">
                <div className="shrink-0">
                  <p className="text-xs font-semibold text-white uppercase tracking-wide mb-3">Contact</p>
                  <div className="flex flex-col gap-2 text-sm text-gray-400">
                    <a href="mailto:hello@niyaleo.com" className="hover:text-brand-green transition-colors">
                      hello@niyaleo.com
                    </a>
                    <p>Nairobi, Kenya</p>
                  </div>
                </div>

                <div className="shrink-0">
                  <p className="text-xs font-semibold text-white uppercase tracking-wide mb-3">Follow us</p>
                  <div className="flex flex-col gap-2 text-sm text-gray-400">
                    <a href="#" className="hover:text-brand-green transition-colors">
                      Facebook
                    </a>
                    <a href="#" className="hover:text-brand-green transition-colors">
                      Instagram
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-800 pt-6 flex flex-col items-center justify-center gap-3 text-center">
              <p className="text-xs text-gray-500">
                © {new Date().getFullYear()} Ni Ya Leo. All rights reserved.
              </p>
              <div className="flex items-center gap-6">
                {['Privacy', 'Terms', 'Contact'].map(l => (
                  <Link key={l} to="#" className="text-xs text-gray-500 hover:text-brand-green transition-colors">{l}</Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </footer>

    </div>
  )
}