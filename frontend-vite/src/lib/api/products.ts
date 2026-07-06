import { apiClient } from './client'
import type { ProductListResponse, ProductResponse } from '@/types/product'

export const productsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient
      .get<ProductListResponse>('/api/v1/products/', { params })
      .then(r => r.data),

    get: (id: number | string) =>
    apiClient
      .get<ProductResponse>(`/api/v1/products/${id}`)
      .then(r => r.data),
}