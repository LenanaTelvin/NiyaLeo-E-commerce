import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ChevronLeft, RotateCcw } from 'lucide-react'
import { useMyStore, useStoreThemes, useApplyTheme, useUpdateMyStore } from '@/lib/hooks/useStores'
import type { StoreTheme, StoreThemeType } from '@/types/store'

const FONTS = ['Inter', 'Roboto', 'Poppins', 'Merriweather', 'Playfair Display', 'DM Sans']
const FONT_SIZES = ['small', 'medium', 'large']

export default function ThemePage() {
  const navigate = useNavigate()
  const { data: store, isLoading } = useMyStore()
  const { data: themes = [] } = useStoreThemes()
  const applyTheme = useApplyTheme()
  const updateStore = useUpdateMyStore()

  const [colors, setColors] = useState<Record<string, string>>({})
  const [font, setFont] = useState('')
  const [fontSize, setFontSize] = useState('')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)

  if (isLoading || !store) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }


  const currentColors = {
    primary_color: colors.primary_color ?? store.primary_color,
    secondary_color: colors.secondary_color ?? store.secondary_color,
    accent_color: colors.accent_color ?? store.accent_color,
    background_color: colors.background_color ?? store.background_color,
    text_color: colors.text_color ?? store.text_color,
  }

  const currentFont = font || store.font_family
  const currentFontSize = fontSize || store.font_size

  async function handleApplyTheme(theme_type: StoreThemeType) {
    await applyTheme.mutateAsync({ theme_type, preserve_colors: true })
  }

  async function handleSave() {
    setSaving(true)
    try {
      await updateStore.mutateAsync({
        ...currentColors,
        font_family: currentFont,
        font_size: currentFontSize,
      })
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  const colorFields: { key: string; label: string }[] = [
    { key: 'primary_color', label: 'Primary' },
    { key: 'secondary_color', label: 'Secondary' },
    { key: 'accent_color', label: 'Accent' },
    { key: 'background_color', label: 'Background' },
    { key: 'text_color', label: 'Text' },
  ]

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/seller/store')} className="text-gray-400 hover:text-gray-900">
          <ChevronLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">Theme & Colors</h1>
      </div>

      {/* Theme picker */}
      <section className="mb-8">
        <h2 className="text-sm font-medium text-gray-900 mb-3">Theme preset</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {themes.map((theme: StoreTheme) => {
            const active = store.theme_type === theme.id
            return (
              <button
                key={theme.id}
                onClick={() => handleApplyTheme(theme.id as StoreThemeType)}
                disabled={applyTheme.isPending}
                className={`relative border rounded-xl p-4 text-left transition-all ${
                  active
                    ? 'border-gray-900 bg-gray-900 text-white'
                    : 'border-gray-100 hover:border-gray-300'
                }`}
              >
                {active && (
                  <Check className="absolute top-3 right-3 w-3.5 h-3.5" />
                )}
                <p className="text-sm font-medium">{theme.name}</p>
                <p className={`text-xs mt-1 ${active ? 'text-gray-300' : 'text-gray-400'}`}>
                  {theme.description}
                </p>
                <div className="flex gap-1 mt-3">
                  {theme.features.slice(0, 2).map((f: string) => (
                    <span
                      key={f}
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        active ? 'bg-gray-700 text-gray-200' : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Color customizer */}
      <section className="mb-8">
        <h2 className="text-sm font-medium text-gray-900 mb-3">Brand colors</h2>
        <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
          {colorFields.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-6 h-6 rounded-full border border-gray-200"
                  style={{ backgroundColor: currentColors[key as keyof typeof currentColors] }}
                />
                <span className="text-sm text-gray-700">{label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 font-mono">
                  {currentColors[key as keyof typeof currentColors]}
                </span>
                <input
                  type="color"
                  value={currentColors[key as keyof typeof currentColors]}
                  onChange={e => setColors(prev => ({ ...prev, [key]: e.target.value }))}
                  className="w-8 h-8 rounded cursor-pointer border border-gray-200"
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Typography */}
      <section className="mb-8">
        <h2 className="text-sm font-medium text-gray-900 mb-3">Typography</h2>
        <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
          <div className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-gray-700">Font family</span>
            <select
              value={currentFont}
              onChange={e => setFont(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-2 py-1 text-gray-700"
            >
              {FONTS.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-gray-700">Font size</span>
            <div className="flex gap-1">
              {FONT_SIZES.map(s => (
                <button
                  key={s}
                  onClick={() => setFontSize(s)}
                  className={`text-xs px-3 py-1.5 rounded-lg capitalize transition-colors ${
                    currentFontSize === s
                      ? 'bg-gray-900 text-white'
                      : 'border border-gray-200 text-gray-600 hover:border-gray-400'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Save */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <button
          onClick={() => { setColors({}); setFont(''); setFontSize('') }}
          className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-700"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className={`px-5 py-2 rounded-xl text-sm font-medium transition-all ${
            success
              ? 'bg-green-600 text-white'
              : 'bg-gray-900 text-white hover:bg-gray-700'
          } disabled:opacity-50`}
        >
          {success ? 'Saved!' : saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  )
}
