import { apiClient } from './client'
import type { SellerProfile, SellerProfileCreate, SellerDashboardStats } from '@/types/seller'

export interface PublicSellerListItem {
  id: number
  store_name: string
  store_slug: string
  store_description?: string
  store_logo_url?: string
  store_banner_url?: string
  is_verified: boolean
  created_at: string
}

interface PublicSellerListResponse {
  items: PublicSellerListItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export const sellersApi = {
  register: (data: SellerProfileCreate) =>
    apiClient.post<SellerProfile>('/api/v1/sellers/register', data).then(r => r.data),

  // Only works once role === seller (post-approval) — see dependencies.py.
  // Pending applicants can't call this; the frontend caches the register
  // response locally instead of relying on this for status checks.
  getMe: () =>
    apiClient.get<SellerProfile>('/api/v1/sellers/me').then(r => r.data),
  getMyApplicationStatus: () =>
    apiClient.get<SellerProfile | null>('/api/v1/sellers/me/application-status').then(r => r.data),
  getDashboardStats: () =>
    apiClient.get<SellerDashboardStats>('/api/v1/sellers/me/dashboard').then(r => r.data),
  listPublic: (params?: Record<string, unknown>) =>
    apiClient.get<PublicSellerListResponse>('/api/v1/sellers/', { params }).then(r => r.data),
  getPublic: (identifier: string | number) =>
    apiClient.get<PublicSellerListItem>(`/api/v1/sellers/${identifier}`).then(r => r.data),
}

