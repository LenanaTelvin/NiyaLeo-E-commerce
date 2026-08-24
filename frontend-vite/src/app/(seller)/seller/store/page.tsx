import { useEffect, useState } from 'react'
import { Check, Palette, Store, Globe, Save, Eye, EyeOff } from 'lucide-react'
import { storesApi } from '@/lib/api/stores'
import type { StoreCustomization, StoreCustomizationUpdate } from '@/lib/api/stores'
import { sellersApi } from '@/lib/api/sellers'
import { toast } from 'sonner'

// ── Theme presets with local visual data ────────────────────────────────────

const THEME_PRESETS = [
  {
    id: 'modern',
    name: 'Modern',
    description: 'Clean and contemporary',
    primary: '#4F46E5',
    secondary: '#10B981',
    accent: '#F59E0B',
    background: '#FFFFFF',
    text: '#1F2937',
    preview: 'bg-gradient-to-br from-indigo-500 to-emerald-400',
  },
  {
    id: 'minimalist',
    name: 'Minimalist',
    description: 'Simple and focused',
    primary: '#111827',
    secondary: '#6B7280',
    accent: '#D1D5DB',
    background: '#FAFAFA',
    text: '#111827',
    preview: 'bg-gradient-to-br from-gray-800 to-gray-400',
  },
  {
    id: 'vibrant',
    name: 'Vibrant',
    description: 'Bold and energetic',
    primary: '#7C3AED',
    secondary: '#DB2777',
    accent: '#F59E0B',
    background: '#FFFFFF',
    text: '#1F2937',
    preview: 'bg-gradient-to-br from-violet-600 to-pink-500',
  },
  {
    id: 'elegant',
    name: 'Elegant',
    description: 'Sophisticated and premium',
    primary: '#92400E',
    secondary: '#D97706',
    accent: '#FCD34D',
    background: '#FFFBEB',
    text: '#1C1917',
    preview: 'bg-gradient-to-br from-amber-800 to-yellow-400',
  },
  {
    id: 'bold',
    name: 'Bold',
    description: 'Strong and impactful',
    primary: '#DC2626',
    secondary: '#1D4ED8',
    accent: '#16A34A',
    background: '#FFFFFF',
    text: '#0F172A',
    preview: 'bg-gradient-to-br from-red-600 to-blue-700',
  },
]

const FONT_OPTIONS = [
  { value: 'Inter',     label: 'Inter — Clean & modern'       },
  { value: 'Playfair Display', label: 'Playfair — Elegant serif' },
  { value: 'Roboto',    label: 'Roboto — Familiar & readable'  },
  { value: 'Poppins',   label: 'Poppins — Friendly & rounded'  },
  { value: 'Montserrat', label: 'Montserrat — Bold & geometric' },
]

type Tab = 'theme' | 'colors' | 'identity' | 'social'

// ── Main page ───────────────────────────────────────────────────────────────

export default function StoreCustomizationPage() {
  const [tab, setTab] = useState<Tab>('theme')
  const [form, setForm] = useState<StoreCustomizationUpdate>({})
  const [current, setCurrent] = useState<StoreCustomization | null>(null)
  const [sellerProfile, setSellerProfile] = useState<{ store_name: string; store_description: string | null } | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [applyingTheme, setApplyingTheme] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(true)

  useEffect(() => {
    Promise.all([
      storesApi.getMyStore(),
      sellersApi.getMe(),
    ])
      .then(([store, seller]) => {
        setCurrent(store)
        setSellerProfile({ store_name: seller.store_name ?? '', store_description: seller.store_description ?? null })
        setForm({
          primary_color:    store.primary_color,
          secondary_color:  store.secondary_color,
          accent_color:     store.accent_color,
          background_color: store.background_color,
          text_color:       store.text_color,
          font_family:      store.font_family,
          font_size:        store.font_size,
          meta_title:       store.meta_title ?? '',
          meta_description: store.meta_description ?? '',
          social_links:     store.social_links,
          contact_info:     store.contact_info,
        })
      })
      .catch(() => toast.error('Could not load store settings'))
      .finally(() => setLoading(false))
  }, [])

  
  const handleApplyTheme = async (themeId: string) => {
    setApplyingTheme(themeId)
    try {
      const updated = await storesApi.applyTheme(themeId)
      setCurrent(updated)
      const preset = THEME_PRESETS.find(t => t.id === themeId)
      if (preset) {
        setForm(f => ({
          ...f,
          primary_color:    preset.primary,
          secondary_color:  preset.secondary,
          accent_color:     preset.accent,
          background_color: preset.background,
          text_color:       preset.text,
          theme_type:       themeId,
        }))
      }
      toast.success(`${themeId.charAt(0).toUpperCase() + themeId.slice(1)} theme applied`)
      setTab('colors')
    } catch {
      toast.error('Could not apply theme')
    } finally {
      setApplyingTheme(null)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await storesApi.updateMyStore(form)
      setCurrent(updated)
      toast.success('Store customization saved')
    } catch {
      toast.error('Could not save changes')
    } finally {
      setSaving(false)
    }
  }

  const setColor = (key: keyof StoreCustomizationUpdate, value: string) =>
    setForm(f => ({ ...f, [key]: value }))

  const TABS: Array<{ id: Tab; label: string; icon: typeof Palette }> = [
    { id: 'theme',    label: 'Theme',    icon: Palette },
    { id: 'colors',   label: 'Colors',   icon: Palette },
    { id: 'identity', label: 'Identity', icon: Store   },
    { id: 'social',   label: 'Social',   icon: Globe   },
  ]

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8 animate-pulse space-y-4">
        <div className="h-8 bg-gray-100 rounded w-48" />
        <div className="grid grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Store customization</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Design how buyers see your storefront
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowPreview(p => !p)}
            className="flex items-center gap-2 text-sm text-gray-500 border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showPreview ? 'Hide' : 'Show'} preview
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-gray-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </div>

      <div className={`grid gap-8 ${showPreview ? 'lg:grid-cols-5' : 'lg:grid-cols-1'}`}>

        {/* Left — editor */}
        <div className={showPreview ? 'lg:col-span-3' : ''}>

          {/* Tab navigation */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium rounded-lg transition-colors
                  ${tab === id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* ── THEME TAB ── */}
          {tab === 'theme' && (
            <div>
              <p className="text-sm text-gray-500 mb-4">
                Pick a starting point. You can fine-tune colors in the next step.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {THEME_PRESETS.map(theme => {
                  const isActive = current?.theme === theme.id || form.theme_type === theme.id
                  const isApplying = applyingTheme === theme.id
                  return (
                    <button
                      key={theme.id}
                      onClick={() => handleApplyTheme(theme.id)}
                      disabled={!!applyingTheme}
                      className={`relative text-left border rounded-xl overflow-hidden transition-all
                        ${isActive
                          ? 'border-gray-900 ring-2 ring-gray-900 ring-offset-1'
                          : 'border-gray-100 hover:border-gray-300'}`}
                    >
                      {/* Color preview strip */}
                      <div className={`h-20 ${theme.preview} relative`}>
                        {isActive && (
                          <div className="absolute top-2 right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-sm">
                            <Check className="w-3.5 h-3.5 text-gray-900" />
                          </div>
                        )}
                        {/* Mini color swatches */}
                        <div className="absolute bottom-2 left-3 flex gap-1.5">
                          {[theme.primary, theme.secondary, theme.accent].map((c, i) => (
                            <div
                              key={i}
                              className="w-4 h-4 rounded-full border-2 border-white shadow-sm"
                              style={{ backgroundColor: c }}
                            />
                          ))}
                        </div>
                      </div>
                      <div className="p-3 bg-white">
                        <p className="text-sm font-medium text-gray-900 flex items-center gap-2">
                          {theme.name}
                          {isApplying && (
                            <span className="text-xs text-gray-400 font-normal">Applying…</span>
                          )}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">{theme.description}</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* ── COLORS TAB ── */}
          {tab === 'colors' && (
            <div className="space-y-6">
              <p className="text-sm text-gray-500">
                Customize your store's color palette. Click any swatch to change it.
              </p>

              {/* Main colors */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Brand colors
                </h3>
                <div className="space-y-3">
                  {[
                    { key: 'primary_color' as const,    label: 'Primary',    hint: 'Buttons, links, key actions' },
                    { key: 'secondary_color' as const,  label: 'Secondary',  hint: 'Supporting elements'         },
                    { key: 'accent_color' as const,     label: 'Accent',     hint: 'Badges, highlights'          },
                  ].map(({ key, label, hint }) => (
                    <ColorRow
                      key={key}
                      label={label}
                      hint={hint}
                      value={form[key] as string ?? '#000000'}
                      onChange={v => setColor(key, v)}
                    />
                  ))}
                </div>
              </div>

              {/* Surface colors */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Surface colors
                </h3>
                <div className="space-y-3">
                  {[
                    { key: 'background_color' as const, label: 'Background', hint: 'Page background'      },
                    { key: 'text_color' as const,       label: 'Text',       hint: 'Body text color'      },
                  ].map(({ key, label, hint }) => (
                    <ColorRow
                      key={key}
                      label={label}
                      hint={hint}
                      value={form[key] as string ?? '#000000'}
                      onChange={v => setColor(key, v)}
                    />
                  ))}
                </div>
              </div>

              {/* Typography */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Typography
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Font family
                    </label>
                    <select
                      value={form.font_family ?? 'Inter'}
                      onChange={e => setForm(f => ({ ...f, font_family: e.target.value }))}
                      className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                      style={{ fontFamily: form.font_family }}
                    >
                      {FONT_OPTIONS.map(f => (
                        <option key={f.value} value={f.value} style={{ fontFamily: f.value }}>
                          {f.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Font size
                    </label>
                    <div className="flex gap-2">
                      {['small', 'medium', 'large'].map(size => (
                        <button
                          key={size}
                          onClick={() => setForm(f => ({ ...f, font_size: size }))}
                          className={`flex-1 py-2 text-sm border rounded-lg capitalize transition-colors
                            ${form.font_size === size
                              ? 'border-gray-900 bg-gray-900 text-white'
                              : 'border-gray-200 text-gray-700 hover:border-gray-400'}`}
                        >
                          {size}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── IDENTITY TAB ── */}
          {tab === 'identity' && (
            <div className="space-y-5">
              <p className="text-sm text-gray-500">
                This information appears on your public storefront and in search results.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Store display name
                </label>
                <input
                  type="text"
                  value={sellerProfile?.store_name ?? ''}
                  disabled
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm bg-gray-50 text-gray-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  To change your store name, update your seller profile.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  SEO title
                  <span className="text-gray-400 font-normal ml-1">(max 255 chars)</span>
                </label>
                <input
                  type="text"
                  value={form.meta_title ?? ''}
                  onChange={e => setForm(f => ({ ...f, meta_title: e.target.value }))}
                  placeholder={sellerProfile?.store_name ?? 'Your store name'}
                  maxLength={255}
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Shown in browser tabs and Google search results.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Meta description
                  <span className="text-gray-400 font-normal ml-1">(max 500 chars)</span>
                </label>
                <textarea
                  value={form.meta_description ?? ''}
                  onChange={e => setForm(f => ({ ...f, meta_description: e.target.value }))}
                  placeholder="Describe your store in a sentence or two…"
                  maxLength={500}
                  rows={3}
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none"
                />
                <p className="text-xs text-gray-400 mt-1">
                  {(form.meta_description ?? '').length}/500 characters
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { key: 'phone',   label: 'Phone number',   placeholder: '+254 700 000 000'     },
                  { key: 'email',   label: 'Contact email',  placeholder: 'store@example.com'    },
                  { key: 'address', label: 'Store address',  placeholder: 'Nairobi, Kenya'        },
                  { key: 'hours',   label: 'Business hours', placeholder: 'Mon–Fri 9am–6pm'      },
                ].map(({ key, label, placeholder }) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-gray-700 mb-1.5">{label}</label>
                    <input
                      type="text"
                      value={(form.contact_info as Record<string, string | null>)?.[key] ?? ''}
                      onChange={e => setForm(f => ({
                        ...f,
                        contact_info: { ...(f.contact_info ?? {}), [key]: e.target.value || null },
                      }))}
                      placeholder={placeholder}
                      className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── SOCIAL TAB ── */}
          {tab === 'social' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">
                Add your social links so buyers can follow your brand.
              </p>
              {[
                { key: 'instagram',  label: 'Instagram',  placeholder: 'https://instagram.com/yourstore' },
                { key: 'facebook',   label: 'Facebook',   placeholder: 'https://facebook.com/yourstore'  },
                { key: 'twitter',    label: 'X / Twitter', placeholder: 'https://x.com/yourstore'        },
                { key: 'tiktok',     label: 'TikTok',     placeholder: 'https://tiktok.com/@yourstore'   },
                { key: 'youtube',    label: 'YouTube',    placeholder: 'https://youtube.com/@yourstore'  },
                { key: 'whatsapp',   label: 'WhatsApp',   placeholder: 'https://wa.me/254700000000'      },
              ].map(({ key, label, placeholder }) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
                  <input
                    type="url"
                    value={(form.social_links as Record<string, string | null>)?.[key] ?? ''}
                    onChange={e => setForm(f => ({
                      ...f,
                      social_links: { ...(f.social_links ?? {}), [key]: e.target.value || null },
                    }))}
                    placeholder={placeholder}
                    className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                  />
                </div>
              ))}
            </div>
          )}

        </div>

        {/* Right — live preview */}
        {showPreview && (
          <div className="lg:col-span-2">
            <div className="sticky top-6">
              <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wider">
                Live preview
              </p>
              <StorePreview
                storeName={sellerProfile?.store_name ?? 'Your Store'}
                primaryColor={form.primary_color ?? '#4F46E5'}
                secondaryColor={form.secondary_color ?? '#10B981'}
                accentColor={form.accent_color ?? '#F59E0B'}
                backgroundColor={form.background_color ?? '#FFFFFF'}
                textColor={form.text_color ?? '#1F2937'}
                fontFamily={form.font_family ?? 'Inter'}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Color row component ──────────────────────────────────────────────────────

function ColorRow({
  label,
  hint,
  value,
  onChange,
}: {
  label: string
  hint: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="flex items-center gap-4">
      <label
        className="w-7 h-7 rounded-lg border-2 border-white shadow-md cursor-pointer shrink-0 transition-transform hover:scale-110"
        style={{ backgroundColor: value }}
      >
        <input
          type="color"
          value={value}
          onChange={e => onChange(e.target.value)}
          className="sr-only"
        />
      </label>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{label}</p>
        <p className="text-xs text-gray-400">{hint}</p>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={value}
          onChange={e => {
            const v = e.target.value
            if (/^#[0-9A-Fa-f]{0,6}$/.test(v)) onChange(v)
          }}
          maxLength={7}
          className="w-24 border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-gray-900 text-center"
        />
      </div>
    </div>
  )
}

// ── Store preview panel ──────────────────────────────────────────────────────

function StorePreview({
  storeName,
  primaryColor,
  secondaryColor,
  accentColor,
  backgroundColor,
  textColor,
  fontFamily,
}: {
  storeName: string
  primaryColor: string
  secondaryColor: string
  accentColor: string
  backgroundColor: string
  textColor: string
  fontFamily: string
}) {
  return (
    <div
      className="border border-gray-200 rounded-2xl overflow-hidden shadow-sm text-xs"
      style={{ backgroundColor, color: textColor, fontFamily }}
    >
      {/* Store header */}
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{ backgroundColor: primaryColor }}
      >
        <span className="text-white font-semibold text-sm truncate">{storeName}</span>
        <div className="flex gap-1.5">
          <div className="w-5 h-5 bg-white/20 rounded" />
          <div className="w-5 h-5 bg-white/20 rounded" />
        </div>
      </div>

      {/* Hero section */}
      <div
        className="px-4 py-6 text-center"
        style={{ backgroundColor: `${primaryColor}12` }}
      >
        <p className="font-semibold text-sm mb-1" style={{ color: textColor }}>
          Welcome to {storeName}
        </p>
        <p className="text-xs mb-3" style={{ color: `${textColor}88` }}>
          Quality products from a verified seller
        </p>
        <button
          className="px-4 py-1.5 rounded-lg text-white text-xs font-medium"
          style={{ backgroundColor: primaryColor }}
        >
          Shop now
        </button>
      </div>

      {/* Product grid */}
      <div className="px-4 py-4">
        <p className="font-medium text-xs mb-3" style={{ color: textColor }}>
          Featured products
        </p>
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg overflow-hidden border" style={{ borderColor: `${textColor}15` }}>
              <div className="aspect-square" style={{ backgroundColor: `${secondaryColor}18` }}>
                <div className="w-full h-full flex items-center justify-center">
                  <div className="w-8 h-8 rounded-md" style={{ backgroundColor: `${secondaryColor}30` }} />
                </div>
              </div>
              <div className="p-2">
                <div className="h-1.5 rounded mb-1" style={{ backgroundColor: `${textColor}25`, width: '70%' }} />
                <div className="flex items-center justify-between">
                  <div className="h-1.5 rounded" style={{ backgroundColor: primaryColor, width: '40%' }} />
                  <div
                    className="w-4 h-4 rounded flex items-center justify-center"
                    style={{ backgroundColor: primaryColor }}
                  >
                    <span className="text-white text-[8px]">+</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer strip */}
      <div className="px-4 py-2.5 flex gap-2 border-t" style={{ borderColor: `${textColor}10` }}>
        {[accentColor, secondaryColor, primaryColor].map((c, i) => (
          <div key={i} className="w-3 h-3 rounded-full" style={{ backgroundColor: c }} />
        ))}
        <span className="text-xs ml-auto" style={{ color: `${textColor}50` }}>
          {fontFamily}
        </span>
      </div>
    </div>
  )
}