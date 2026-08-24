import { Link } from 'react-router-dom'
import { Palette, FileText, Layout, Image, ExternalLink, AlertCircle } from 'lucide-react'
import { useMyStore } from '@/lib/hooks/useStores'

export default function StoreOverviewPage() {
  const { data: store, isLoading, error } = useMyStore()

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-start gap-3 p-4 border border-red-100 bg-red-50 rounded-xl text-sm text-red-700">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <p>Could not load store settings. Make sure your store has been set up.</p>
        </div>
      </div>
    )
  }

  const sections = [
    {
      to: '/seller/store/theme',
      icon: Palette,
      label: 'Theme & Colors',
      description: 'Pick a theme and customize your brand colors, fonts, and layout.',
      meta: store ? `Current: ${store.theme}` : null,
    },
    {
      to: '/seller/store/pages',
      icon: FileText,
      label: 'Pages',
      description: 'Manage your About, Contact, FAQ, and custom pages.',
      meta: null,
    },
    {
      to: '/seller/store/sections',
      icon: Layout,
      label: 'Sections',
      description: 'Add and reorder homepage sections like hero banners and featured products.',
      meta: null,
    },
    {
      to: '/seller/store/media',
      icon: Image,
      label: 'Media',
      description: 'Upload your store logo, banners, and other images.',
      meta: null,
    },
  ]

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Store</h1>
        {store && (
          <a
            href={`/stores/${store.seller_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900"
          >
            View storefront
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {store && (
        <div className="border border-gray-100 rounded-xl p-4 mb-6 flex items-center gap-4">
          <div
            className="w-8 h-8 rounded-full border border-gray-200 shrink-0"
            style={{ backgroundColor: store.primary_color }}
          />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 capitalize">{store.theme} theme</p>
            <p className="text-xs text-gray-400 truncate">
              {store.primary_color} · {store.font_family}
            </p>
          </div>
          <Link
            to="/seller/store/theme"
            className="ml-auto text-xs text-gray-500 hover:text-gray-900 shrink-0"
          >
            Edit
          </Link>
        </div>
      )}

      <div className="space-y-3">
        {sections.map(({ to, icon: Icon, label, description, meta }) => (
          <Link
            key={to}
            to={to}
            className="flex items-center gap-4 border border-gray-100 rounded-xl p-4 hover:border-gray-300 transition-colors group"
          >
            <div className="w-9 h-9 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-gray-100 transition-colors shrink-0">
              <Icon className="w-4 h-4 text-gray-600" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-900">{label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{description}</p>
            </div>
            {meta && (
              <span className="text-xs text-gray-400 shrink-0 capitalize">{meta}</span>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}
