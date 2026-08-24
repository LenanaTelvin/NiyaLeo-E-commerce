import { apiClient } from './client'

export interface PendingSellerItem {
  id: number
  user_id: number
  business_name: string
  business_type: string
  store_name: string
  store_slug: string
  phone_number?: string
  city?: string
  country?: string
  is_verified: boolean
  kyb_status?: string
  created_at: string
  user_email?: string
  user_username?: string
}

interface PendingSellerListResponse {
  items: PendingSellerItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface PlatformStats {
  users: { total: number; active: number; verified: number; new_today: number; new_this_week: number; new_this_month: number; by_role: Record<string, number> }
  sellers: { total: number; pending: number; approved: number; suspended: number; rejected: number; closed: number; new_this_week: number }
  products: { total: number; active: number; draft: number; out_of_stock: number; archived: number; low_stock: number }
  orders: { total: number; pending: number; processing: number; completed: number; cancelled: number; total_revenue: number }
  commissions: { total_collected: number; this_month: number; pending_payout: number; platform_rate: number }
  generated_at: string
}

interface ActivityItem {
  id: number
  username?: string
  activity_type: string
  activity_category?: string
  description?: string
  created_at: string
}

export const adminApi = {
  getDashboard: () =>
    apiClient.get('/api/v1/admin/dashboard/').then(r => r.data),

  getStats: () =>
    apiClient.get<PlatformStats>('/api/v1/admin/dashboard/stats').then(r => r.data),

  listPendingSellers: (params?: Record<string, unknown>) =>
    apiClient.get<PendingSellerListResponse>('/api/v1/admin/dashboard/sellers/pending', { params }).then(r => r.data),

  // The atomic action endpoint — approve/reject/suspend in one call,
  // handles both status update AND role elevation server-side.
  actionOnSeller: (sellerId: number, action: 'approved' | 'rejected' | 'suspended', reason?: string) =>
    apiClient
      .post(`/api/v1/admin/dashboard/sellers/${sellerId}/action`, { action, reason })
      .then(r => r.data),

  getActivity: (params?: Record<string, unknown>) =>
    apiClient.get<{ items: ActivityItem[]; total: number }>('/api/v1/admin/dashboard/activity', { params }).then(r => r.data),
}