import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, Plus, Eye, EyeOff, Trash2, Edit2, X } from 'lucide-react'
import { useStorePages, useCreatePage, useUpdatePage, useDeletePage } from '@/lib/hooks/useStores'
import type { StorePage, StorePageCreate } from '@/types/store'

const PAGE_TYPES = ['about', 'contact', 'faq', 'policy', 'custom'] as const

function slugify(str: string) {
  return str.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
}

export default function StorePagesPage() {
  const navigate = useNavigate()
  const { data: pages = [], isLoading } = useStorePages()
  const createPage = useCreatePage()
  const updatePage = useUpdatePage()
  const deletePage = useDeletePage()

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState({ title: '', slug: '', page_type: 'custom', content: '' })

  function openCreate() {
    setForm({ title: '', slug: '', page_type: 'custom', content: '' })
    setEditingId(null)
    setShowForm(true)
  }

  function openEdit(page: StorePage) {
    setForm({
      title: page.title,
      slug: page.slug,
      page_type: page.page_type,
      content: page.content ?? '',
    })
    setEditingId(page.id)
    setShowForm(true)
  }

  async function handleSubmit() {
    if (!form.title || !form.slug) return
    if (editingId) {
      await updatePage.mutateAsync({ id: editingId, data: { title: form.title, slug: form.slug, content: form.content } })
    } else {
      await createPage.mutateAsync({
        title: form.title,
        slug: form.slug,
        page_type: form.page_type as StorePageCreate['page_type'],
        content: form.content,
        is_published: true,
        show_in_nav: true,
        nav_order: pages.length,
        store_id: 0, // resolved server-side
      })
    }
    setShowForm(false)
  }

  async function togglePublished(page: StorePage) {
    await updatePage.mutateAsync({ id: page.id, data: { is_published: !page.is_published } })
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this page?')) return
    await deletePage.mutateAsync(id)
  }

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
          <h1 className="text-2xl font-semibold text-gray-900">Pages</h1>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-700"
        >
          <Plus className="w-4 h-4" />
          New page
        </button>
      </div>

      {/* Page list */}
      {pages.length === 0 ? (
        <div className="border border-dashed border-gray-200 rounded-xl py-12 text-center">
          <p className="text-sm text-gray-400">No pages yet</p>
          <button onClick={openCreate} className="mt-3 text-sm text-gray-900 underline underline-offset-2">
            Create your first page
          </button>
        </div>
      ) : (
        <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
          {pages.map(page => (
            <div key={page.id} className="flex items-center gap-3 px-4 py-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{page.title}</p>
                <p className="text-xs text-gray-400 font-mono">/{page.slug}</p>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${
                page.is_published ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
              }`}>
                {page.is_published ? 'Published' : 'Draft'}
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => togglePublished(page)}
                  className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-100"
                  title={page.is_published ? 'Unpublish' : 'Publish'}
                >
                  {page.is_published ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => openEdit(page)}
                  className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-100"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(page.id)}
                  className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Slide-in form */}
      {showForm && (
        <div className="fixed inset-0 bg-black/20 z-40 flex justify-end">
          <div className="bg-white w-full max-w-md h-full shadow-xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-medium text-gray-900">
                {editingId ? 'Edit page' : 'New page'}
              </h2>
              <button onClick={() => setShowForm(false)}>
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Title</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="About Us"
                  value={form.title}
                  onChange={e => {
                    const title = e.target.value
                    setForm(f => ({ ...f, title, slug: slugify(title) }))
                  }}
                />
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Slug</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono"
                  placeholder="about-us"
                  value={form.slug}
                  onChange={e => setForm(f => ({ ...f, slug: slugify(e.target.value) }))}
                />
              </div>

              {!editingId && (
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Page type</label>
                  <select
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                    value={form.page_type}
                    onChange={e => setForm(f => ({ ...f, page_type: e.target.value }))}
                  >
                    {PAGE_TYPES.map(t => (
                      <option key={t} value={t} className="capitalize">{t}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="text-xs text-gray-500 mb-1 block">Content</label>
                <textarea
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none"
                  rows={10}
                  placeholder="Write your page content here..."
                  value={form.content}
                  onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-100">
              <button
                onClick={handleSubmit}
                disabled={createPage.isPending || updatePage.isPending}
                className="w-full py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-700 disabled:opacity-50"
              >
                {editingId ? 'Save changes' : 'Create page'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
