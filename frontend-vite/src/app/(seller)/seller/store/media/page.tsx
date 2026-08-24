import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, Plus, Trash2, Image, X, Star } from 'lucide-react'
import { useStoreMedia, useAddMedia, useDeleteMedia } from '@/lib/hooks/useStores'
import { useMyStore } from '@/lib/hooks/useStores'
import { StoreMedia } from '@/types/store'

const MEDIA_TYPES = [
  { value: 'logo', label: 'Logo', description: 'Your store logo shown in the header' },
  { value: 'banner', label: 'Banner', description: 'Hero banner image at the top of your store' },
  { value: 'gallery', label: 'Gallery', description: 'General store images' },
  { value: 'icon', label: 'Icon', description: 'Small icon or favicon' },
]

export default function StoreMediaPage() {
  const navigate = useNavigate()
  const { data: store } = useMyStore()
  const { data: media = [], isLoading } = useStoreMedia()
  const addMedia = useAddMedia()
  const deleteMedia = useDeleteMedia()

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    media_type: 'logo',
    title: '',
    url: '',
    alt_text: '',
    is_default: true,
  })
  const [preview, setPreview] = useState('')

  function handleUrlChange(url: string) {
    setForm(f => ({ ...f, url }))
    setPreview(url)
  }

  async function handleAdd() {
    if (!form.url) return
    await addMedia.mutateAsync({
      ...form,
      seller_id: store?.seller_id ?? 0,
    })
    setShowForm(false)
    setForm({ media_type: 'logo', title: '', url: '', alt_text: '', is_default: true })
    setPreview('')
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this media?')) return
    await deleteMedia.mutateAsync(id)
  }

  const grouped = MEDIA_TYPES.map(type => ({
    ...type,
    items: media.filter((m: StoreMedia) => m.media_type === type.value)
  }))

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-3">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/seller/store')} className="text-gray-400 hover:text-gray-900">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-semibold text-gray-900">Media</h1>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-700"
        >
          <Plus className="w-4 h-4" />
          Add media
        </button>
      </div>

      <p className="text-sm text-gray-400 mb-6">
        Add image URLs for your store logo, banners, and gallery. Use Cloudinary, Imgur, or any image host.
      </p>

      {/* Grouped by type */}
      <div className="space-y-6">
        {grouped.map(group => (
          <div key={group.value}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="text-sm font-medium text-gray-900">{group.label}</h2>
                <p className="text-xs text-gray-400">{group.description}</p>
              </div>
              <button
                onClick={() => { setForm(f => ({ ...f, media_type: group.value })); setShowForm(true) }}
                className="text-xs text-gray-500 hover:text-gray-900"
              >
                + Add
              </button>
            </div>

            {group.items.length === 0 ? (
              <div className="border border-dashed border-gray-200 rounded-xl h-24 flex items-center justify-center">
                <div className="text-center">
                  <Image className="w-5 h-5 text-gray-300 mx-auto mb-1" />
                  <p className="text-xs text-gray-400">No {group.label.toLowerCase()} yet</p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-3">
                {group.items.map((item: StoreMedia) => (
                  <div key={item.id} className="relative group border border-gray-100 rounded-xl overflow-hidden">
                    <img
                      src={item.url}
                      alt={item.alt_text ?? item.title ?? group.label}
                      className="w-full h-28 object-cover"
                      onError={e => {
                        (e.target as HTMLImageElement).src = 'https://placehold.co/200x112?text=Error'
                      }}
                    />
                    {item.is_default && (
                      <div className="absolute top-2 left-2 bg-gray-900 text-white rounded-full p-1">
                        <Star className="w-3 h-3" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-2 bg-white rounded-full shadow text-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    {item.title && (
                      <p className="text-xs text-gray-500 px-2 py-1 truncate">{item.title}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add media drawer */}
      {showForm && (
        <div className="fixed inset-0 bg-black/20 z-40 flex justify-end">
          <div className="bg-white w-full max-w-md h-full shadow-xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-medium text-gray-900">Add media</h2>
              <button onClick={() => { setShowForm(false); setPreview('') }}>
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Media type</label>
                <select
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  value={form.media_type}
                  onChange={e => setForm(f => ({ ...f, media_type: e.target.value }))}
                >
                  {MEDIA_TYPES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Image URL</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="https://res.cloudinary.com/..."
                  value={form.url}
                  onChange={e => handleUrlChange(e.target.value)}
                />
              </div>

              {preview && (
                <div className="border border-gray-100 rounded-xl overflow-hidden">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full h-40 object-cover"
                    onError={e => {
                      (e.target as HTMLImageElement).src = 'https://placehold.co/400x160?text=Invalid+URL'
                    }}
                  />
                </div>
              )}

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Title (optional)</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Store logo"
                  value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Alt text</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Describe the image"
                  value={form.alt_text}
                  onChange={e => setForm(f => ({ ...f, alt_text: e.target.value }))}
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_default}
                  onChange={e => setForm(f => ({ ...f, is_default: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">Set as default {form.media_type}</span>
              </label>
            </div>

            <div className="px-6 py-4 border-t border-gray-100">
              <button
                onClick={handleAdd}
                disabled={!form.url || addMedia.isPending}
                className="w-full py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-700 disabled:opacity-50"
              >
                Add media
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
