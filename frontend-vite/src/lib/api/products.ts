import { apiClient } from './client'
import type {
  ProductListResponse, ProductResponse, ProductCreate, ProductUpdate,
} from '@/types/product'

export const productsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<ProductListResponse>('/api/v1/products/', { params }).then(r => r.data),

  get: (id: number | string) =>
    apiClient.get<ProductResponse>(`/api/v1/products/${id}`).then(r => r.data),

  // ── Seller-facing ──
  listMine: (params?: Record<string, unknown>) =>
    apiClient.get<ProductListResponse>('/api/v1/seller/products/', { params }).then(r => r.data),

  getMine: (id: number) =>
    apiClient.get<ProductResponse>(`/api/v1/seller/products/${id}`).then(r => r.data),

  create: (data: ProductCreate) =>
    apiClient.post<ProductResponse>('/api/v1/seller/products/', data).then(r => r.data),

  update: (id: number, data: ProductUpdate) =>
    apiClient.put<ProductResponse>(`/api/v1/seller/products/${id}`, data).then(r => r.data),

  delete: (id: number) =>
    apiClient.delete(`/api/v1/seller/products/${id}`),

  togglePublish: (id: number, is_published: boolean) =>
    apiClient.patch<ProductResponse>(`/api/v1/seller/products/${id}/publish`, { is_published }).then(r => r.data),
}