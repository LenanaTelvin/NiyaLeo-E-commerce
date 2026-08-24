import { useEffect, useState } from 'react'
import { Search, Store, User, Trash2, AlertTriangle, ChevronDown } from 'lucide-react'
import { apiClient } from '@/lib/api/client'

interface AdminUser {
  id: number
  email: string
  username: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

interface UsersResponse {
  items: AdminUser[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

const ROLE_STYLES: Record<string, string> = {
  ADMIN:    'bg-purple-50 text-purple-700',
  SELLER:   'bg-blue-50 text-blue-700',
  CUSTOMER: 'bg-gray-100 text-gray-600',
}


export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [confirmDelete, setConfirmDelete] = useState<AdminUser | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [updatingRoleId, setUpdatingRoleId] = useState<number | null>(null)

  async function fetchUsers(p = 1, q = search) {
    setLoading(true)
    try {
      const res = await apiClient.get<UsersResponse>('/api/v1/admin/users/', {
        params: { page: p, per_page: 20, search: q || undefined, is_active: true },
      })
      setUsers(res.data.items)
      setTotal(res.data.total)
      setTotalPages(res.data.total_pages)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchUsers(1) }, [])

  function handleSearch(q: string) {
    setSearch(q)
    setPage(1)
    fetchUsers(1, q)
  }

  async function handleRoleChange(user: AdminUser, newRole: string) {
    setUpdatingRoleId(user.id)
    try {
      if (newRole === 'SELLER') {
        await apiClient.post(`/api/v1/admin/users/${user.id}/promote-to-seller`)
      } else if (newRole === 'CUSTOMER' && user.role === 'SELLER') {
        await apiClient.post(`/api/v1/admin/users/${user.id}/demote-to-customer`)
      } else {
        await apiClient.put(`/api/v1/admin/users/${user.id}/role`, null, {
            params: { role: newRole },
        })
      }
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, role: newRole } : u))
    } catch (err: any) {
      alert(err?.response?.data?.detail ?? 'Could not update role')
      } finally {
        setUpdatingRoleId(null)
      }
    }

  async function handleDelete() {
    if (!confirmDelete) return
    setDeletingId(confirmDelete.id)
    try {
      await apiClient.delete(`/api/v1/admin/users/${confirmDelete.id}`)
      setUsers(prev => prev.filter(u => u.id !== confirmDelete.id))
      setTotal(t => t - 1)
    } catch {}
    finally {
      setDeletingId(null)
      setConfirmDelete(null)
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 mb-1">Users</h1>
          <p className="text-sm text-gray-400">{total} total users</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search by email or username…"
          value={search}
          onChange={e => handleSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-gray-400"
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-14 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl">
          <User className="w-8 h-8 text-gray-200 mx-auto mb-3" />
          <p className="text-sm text-gray-400">No users found</p>
        </div>
      ) : (
        <div className="border border-gray-100 rounded-xl overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-12 gap-4 px-4 py-2.5 bg-gray-50 border-b border-gray-100 text-xs font-medium text-gray-400 uppercase tracking-wide">
            <div className="col-span-4">User</div>
            <div className="col-span-2">Role</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2">Joined</div>
            <div className="col-span-2 text-right">Actions</div>
          </div>

          {/* Rows */}
          <div className="divide-y divide-gray-100">
            {users.map(user => {
              return (
                <div key={user.id} className="grid grid-cols-12 gap-4 px-4 py-3 items-center hover:bg-gray-50 transition-colors">
                  {/* User */}
                  <div className="col-span-4 flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-semibold text-gray-600 shrink-0">
                      {(user.full_name || user.username || user.email)[0].toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {user.full_name || user.username}
                      </p>
                      <p className="text-xs text-gray-400 truncate">{user.email}</p>
                    </div>
                  </div>

                  {/* Role selector */}
                  <div className="col-span-2">
                    <div className="relative inline-block">
                      <select
                        value={user.role}
                        onChange={e => handleRoleChange(user, e.target.value)}
                        disabled={updatingRoleId === user.id}
                        className={`text-xs font-medium pl-2 pr-6 py-1 rounded-full appearance-none cursor-pointer border-0 focus:outline-none focus:ring-1 focus:ring-gray-300 disabled:opacity-50 ${ROLE_STYLES[user.role] ?? 'bg-gray-100 text-gray-600'}`}
                      >
                        <option value="CUSTOMER">Customer</option>
                        <option value="SELLER">Seller</option>
                        <option value="ADMIN">Admin</option>
                      </select>
                      <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 pointer-events-none opacity-60" />
                    </div>
                  </div>

                  {/* Status */}
                  <div className="col-span-2">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <span className="text-xs text-gray-500">
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    {!user.is_verified && (
                      <p className="text-xs text-amber-500 mt-0.5">Unverified</p>
                    )}
                  </div>

                  {/* Joined */}
                  <div className="col-span-2">
                    <p className="text-xs text-gray-400">{formatDate(user.created_at)}</p>
                  </div>

                  {/* Actions */}
                  <div className="col-span-2 flex items-center justify-end gap-1">
                    <button
                      onClick={() => setConfirmDelete(user)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete user"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            disabled={page === 1}
            onClick={() => { setPage(p => p - 1); fetchUsers(page - 1) }}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => { setPage(p => p + 1); fetchUsers(page + 1) }}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}

      {/* Delete confirm modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center mb-4">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">Delete user?</h3>
            <p className="text-sm text-gray-500 mb-6">
              <span className="font-medium text-gray-900">{confirmDelete.email}</span> will be permanently removed.
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
                onClick={handleDelete}
                disabled={deletingId !== null}
                className="flex-1 px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-xl hover:bg-red-700 disabled:opacity-50"
              >
                {deletingId !== null ? 'Deleting…' : 'Delete user'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
