import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, Plus, Trash2, ToggleLeft, ToggleRight, GripVertical, X } from 'lucide-react'
import { useStoreSections, useCreateSection, useUpdateSection, useDeleteSection } from '@/lib/hooks/useStores'
import type { StoreSection } from '@/types/store'

const SECTION_TYPES = [
  { value: 'hero', label: 'Hero Banner', description: 'Full-width banner at the top of your store' },
  { value: 'featured', label: 'Featured Products', description: 'Showcase selected products' },
  { value: 'categories', label: 'Categories', description: 'Display product categories' },
  { value: 'testimonial', label: 'Testimonials', description: 'Customer reviews and quotes' },
  { value: 'newsletter', label: 'Newsletter', description: 'Email signup section' },
  { value: 'custom', label: 'Custom', description: 'Free-form custom section' },
]

export default function StoreSectionsPage() {
  const navigate = useNavigate()
  const { data: sections = [], isLoading } = useStoreSections()
  const createSection = useCreateSection()
  const updateSection = useUpdateSection()
  const deleteSection = useDeleteSection()

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    title: '',
    section_type: 'hero',
    heading: '',
    subheading: '',
    button_text: '',
    button_url: '',
  })

  async function handleCreate() {
    if (!form.section_type) return
    await createSection.mutateAsync({
      title: form.title,
      section_type: form.section_type,
      content: {
        heading: form.heading || null,
        subheading: form.subheading || null,
        button_text: form.button_text || null,
        button_url: form.button_url || null,
        items: [],
        settings: {},
      },
      is_active: true,
      order: sections.length,
      store_id: 0, // resolved server-side
    })
    setShowForm(false)
    setForm({ title: '', section_type: 'hero', heading: '', subheading: '', button_text: '', button_url: '' })
  }

  async function toggleActive(section: StoreSection) {
    await updateSection.mutateAsync({
      id: section.id,
      data: { is_active: !section.is_active },
    })
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this section?')) return
    await deleteSection.mutateAsync(id)
  }

  const sectionLabel = (type: string) =>
    SECTION_TYPES.find(s => s.value === type)?.label ?? type

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
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
          <h1 className="text-2xl font-semibold text-gray-900">Sections</h1>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-700"
        >
          <Plus className="w-4 h-4" />
          Add section
        </button>
      </div>

      <p className="text-sm text-gray-400 mb-4">
        Sections appear on your store homepage. Toggle them on/off without deleting.
      </p>

      {/* Section list */}
      {sections.length === 0 ? (
        <div className="border border-dashed border-gray-200 rounded-xl py-12 text-center">
          <p className="text-sm text-gray-400">No sections yet</p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-3 text-sm text-gray-900 underline underline-offset-2"
          >
            Add your first section
          </button>
        </div>
      ) : (
        <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
          {sections
            .slice()
            .sort((a: StoreSection, b: StoreSection) => a.order - b.order)
            .map((section: StoreSection) => (
              <div key={section.id} className="flex items-center gap-3 px-4 py-3">
                <GripVertical className="w-4 h-4 text-gray-300 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {section.title || sectionLabel(section.section_type)}
                  </p>
                  <p className="text-xs text-gray-400 capitalize">{section.section_type}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  section.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {section.is_active ? 'Active' : 'Hidden'}
                </span>
                <button
                  onClick={() => toggleActive(section)}
                  className="text-gray-400 hover:text-gray-700"
                  title={section.is_active ? 'Hide section' : 'Show section'}
                >
                  {section.is_active
                    ? <ToggleRight className="w-5 h-5 text-gray-900" />
                    : <ToggleLeft className="w-5 h-5" />
                  }
                </button>
                <button
                  onClick={() => handleDelete(section.id)}
                  className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
        </div>
      )}

      {/* Add section drawer */}
      {showForm && (
        <div className="fixed inset-0 bg-black/20 z-40 flex justify-end">
          <div className="bg-white w-full max-w-md h-full shadow-xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-medium text-gray-900">Add section</h2>
              <button onClick={() => setShowForm(false)}>
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {/* Section type picker */}
              <div>
                <label className="text-xs text-gray-500 mb-2 block">Section type</label>
                <div className="space-y-2">
                  {SECTION_TYPES.map(type => (
                    <button
                      key={type.value}
                      onClick={() => setForm(f => ({ ...f, section_type: type.value }))}
                      className={`w-full text-left border rounded-xl px-4 py-3 transition-colors ${
                        form.section_type === type.value
                          ? 'border-gray-900 bg-gray-50'
                          : 'border-gray-100 hover:border-gray-300'
                      }`}
                    >
                      <p className="text-sm font-medium text-gray-900">{type.label}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Title (optional)</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="e.g. Our bestsellers"
                  value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Heading</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Main heading text"
                  value={form.heading}
                  onChange={e => setForm(f => ({ ...f, heading: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Subheading</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Supporting text"
                  value={form.subheading}
                  onChange={e => setForm(f => ({ ...f, subheading: e.target.value }))}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Button text</label>
                  <input
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                    placeholder="Shop now"
                    value={form.button_text}
                    onChange={e => setForm(f => ({ ...f, button_text: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Button URL</label>
                  <input
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                    placeholder="/products"
                    value={form.button_url}
                    onChange={e => setForm(f => ({ ...f, button_url: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-100">
              <button
                onClick={handleCreate}
                disabled={createSection.isPending}
                className="w-full py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-700 disabled:opacity-50"
              >
                Add section
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
