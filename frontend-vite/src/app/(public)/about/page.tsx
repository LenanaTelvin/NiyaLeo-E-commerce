// app/(public)/about/page.tsx
import { Link } from 'react-router-dom'
import { ArrowRight, Store, ShieldCheck, Truck } from 'lucide-react'

const STEPS = [
  {
    icon: Store,
    title: 'Sellers open a store.',
    desc: 'Any verified seller can set up their own storefront in minutes.',
  },
  {
    icon: ShieldCheck,
    title: 'We review every seller.',
    desc: 'Each application is checked before approval, so buyers can shop with confidence.',
  },
  {
    icon: Truck,
    title: 'Buyers shop directly.',
    desc: 'Customers browse, buy, and get products delivered straight from the seller.',
  },
]

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      <section className="max-w-3xl mx-auto px-6 py-16 lg:py-20 text-center">

        <h1 className="font-heading text-2xl sm:text-3xl lg:text-4xl leading-[1.3] text-gray-900 mb-6">
          <span className="font-bold">A marketplace built for African sellers,</span>
          <br className="hidden sm:block" />
          <span className="font-light italic text-gray-600"> and the customers who trust them.</span>
        </h1>

        <p className="text-sm text-gray-500 leading-relaxed max-w-lg mx-auto mb-12">
          Too many small businesses across the continent struggle to reach
          customers beyond their immediate community. Ni Ya Leo gives every
          seller — from a home baker to a growing brand — a storefront of
          their own, and gives customers a trusted place to discover them.
        </p>

        <div className="grid sm:grid-cols-3 gap-8 mb-12 text-left sm:text-center">
          {STEPS.map(({ icon: Icon, title, desc }, i) => (
            <div key={title} className="flex flex-col sm:items-center">
              <div className={`w-10 h-10 bg-brand-greenSoft rounded-xl flex items-center justify-center mb-3 sm:mx-auto ${i === 1 ? 'sm:-translate-y-6' : 'sm:translate-y-6'}`}>
                <Icon className="w-4.5 h-4.5 text-brand-green" />
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                <span className="font-semibold text-gray-900">{title}</span> {desc}
              </p>
            </div>
          ))}
        </div>

        <Link
          to="/account/become-seller"
          className="inline-flex items-center gap-2 bg-gray-900 text-white px-7 py-3.5 rounded-xl text-sm font-medium hover:bg-brand-green transition-colors"
        >
          Become a seller <ArrowRight className="w-4 h-4" />
        </Link>

      </section>
    </div>
  )
}