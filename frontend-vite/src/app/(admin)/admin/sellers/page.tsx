import { useState } from 'react'
import { CheckCircle2, XCircle, Trash2, Store, AlertTriangle } from 'lucide-react'
import { usePendingSellers, useSellerAction } from '@/lib/hooks/useAdmin'
import { apiClient } from '@/lib/api/client'
import { useQueryClient } from '@tanstack/react-query'

type Tab = 'pending' | 'all'

interface AllSeller {
  id: number
  store_name: string
  business_name: string
  store_slug: string
  status: string
  is_active: boolean
  user_email?: string
  user_username?: string
  city?: string
  country?: string
}

export default function AdminSellersPage() {
  const [tab, setTab] = useState<Tab>('pending')
  const [page, setPage] = useState(1)
  const [allSellers, setAllSellers] = useState<AllSeller[]>([])
  const [allLoading, setAllLoading] = useState(false)
  const [, setAllTotal] = useState(0)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<AllSeller | null>(null)

  const { data, isLoading } = usePendingSellers(page)
  const sellerAction = useSellerAction()
  const qc = useQueryClient()

  async function loadAllSellers(p = 1) {
    setAllLoading(true)
    try {
      const res = await apiClient.get('/api/v1/admin/sellers/', { params: { page: p, per_page: 20 } })
      setAllSellers(res.data.items)
      setAllTotal(res.data.total)
    } catch {}
    finally { setAllLoading(false) }
  }

  function switchTab(t: Tab) {
    setTab(t)
    if (t === 'all') loadAllSellers()
  }

  async function handleDelete(seller: AllSeller) {
    setConfirmDelete(seller)
  }

  async function confirmDeleteSeller() {
    if (!confirmDelete) return
    setDeletingId(confirmDelete.id)
    try {
      await apiClient.delete(`/api/v1/admin/sellers/${confirmDelete.id}`)
      setAllSellers(prev => prev.filter(s => s.id !== confirmDelete.id))
      qc.invalidateQueries({ queryKey: ['admin'] })
    } catch {}
    finally {
      setDeletingId(null)
      setConfirmDelete(null)
    }
  }

  const statusColor: Record<string, string> = {
    PENDING:   'bg-amber-50 text-amber-600',
    APPROVED:  'bg-green-50 text-green-700',
    REJECTED:  'bg-red-50 text-red-600',
    SUSPENDED: 'bg-gray-100 text-gray-500',
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Sellers</h1>
      <p className="text-sm text-gray-400 mb-6">Manage seller applications and store accounts.</p>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-100 mb-6">
        {(['pending', 'all'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => switchTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              tab === t
                ? 'border-gray-900 text-gray-900'
                : 'border-transparent text-gray-400 hover:text-gray-700'
            }`}
          >
            {t === 'pending' ? 'Pending applications' : 'All sellers'}
            {t === 'pending' && data?.total ? (
              <span className="ml-2 text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                {data.total}
              </span>
            ) : null}
          </button>
        ))}
      </div>

      {/* ── PENDING TAB ── */}
      {tab === 'pending' && (
        <>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-36 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : data && data.items.length > 0 ? (
            <div className="space-y-4">
              {data.items.map((seller: any) => (
                <div key={seller.id} className="border border-gray-100 rounded-xl p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-base font-semibold text-gray-900">{seller.store_name}</h3>
                      <p className="text-sm text-gray-400">{seller.business_name}</p>
                      {seller.user_email && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          {seller.user_email}{seller.user_username && ` · @${seller.user_username}`}
                        </p>
                      )}
                    </div>
                    <span className="text-xs bg-amber-50 text-amber-600 px-2.5 py-1 rounded-full font-medium shrink-0">
                      Pending
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm mb-4">
                    <Detail label="Business type" value={seller.business_type} />
                    <Detail label="Store slug" value={seller.store_slug} />
                    <Detail label="Phone" value={seller.phone_number || '—'} />
                    <Detail label="Location" value={[seller.city, seller.country].filter(Boolean).join(', ') || '—'} />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => sellerAction.mutate({ sellerId: seller.id, action: 'approved' })}
                      disabled={sellerAction.isPending}
                      className="flex items-center gap-1.5 bg-gray-900 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-800 disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-4 h-4" /> Approve
                    </button>
                    <button
                      onClick={() => {
                        const reason = prompt('Reason for rejection (required):')
                        if (!reason) return
                        sellerAction.mutate({ sellerId: seller.id, action: 'rejected', reason })
                      }}
                      disabled={sellerAction.isPending}
                      className="flex items-center gap-1.5 text-sm font-medium text-red-600 px-4 py-2 rounded-lg hover:bg-red-50 disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
              <CheckCircle2 className="w-8 h-8 text-gray-200 mx-auto mb-3" />
              <p className="text-gray-900 font-medium">No pending applications</p>
              <p className="text-sm text-gray-400 mt-1">All caught up!</p>
            </div>
          )}

          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30">
                Previous
              </button>
              <span className="text-sm text-gray-500">Page {data.page} of {data.total_pages}</span>
              <button disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30">
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* ── ALL SELLERS TAB ── */}
      {tab === 'all' && (
        <>
          {allLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : allSellers.length > 0 ? (
            <div className="border border-gray-100 rounded-xl divide-y divide-gray-100">
              {allSellers.map(seller => (
                <div key={seller.id} className="flex items-center gap-4 px-4 py-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center shrink-0">
                    <Store className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{seller.store_name}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {seller.user_email} · /{seller.store_slug}
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize shrink-0 ${statusColor[seller.status] ?? 'bg-gray-100 text-gray-500'}`}>
                    {seller.status?.toLowerCase()}
                  </span>
                  <button
                    onClick={() => handleDelete(seller)}
                    disabled={deletingId === seller.id}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-40 shrink-0"
                    title="Delete seller"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
              <p className="text-gray-400 text-sm">No sellers found</p>
            </div>
          )}
        </>
      )}

      {/* ── DELETE CONFIRM MODAL ── */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center mb-4">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">Delete seller store?</h3>
            <p className="text-sm text-gray-500 mb-6">
              <span className="font-medium text-gray-900">{confirmDelete.store_name}</span> will be permanently closed.
              This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="flex-1 px-4 py-2 text-sm font-medium border border-gray-200 rounded-xl hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteSeller}
                disabled={deletingId !== null}
                className="flex-1 px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-xl hover:bg-red-700 disabled:opacity-50"
              >
                {deletingId !== null ? 'Deleting…' : 'Delete store'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-gray-400">{label}: </span>
      <span className="text-gray-900">{value}</span>
    </div>
  )
}
