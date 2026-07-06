import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { productsApi } from '@/lib/api/products'
import type { ProductListResponse, ProductResponse } from '@/types/product'

export type SortBy = 'created_at' | 'price' | 'name'
export type SortDir = 'asc' | 'desc'

export interface ProductFilters {
  page?: number
  per_page?: number
  search?: string
  category_id?: number
  tag_ids?: number[]
  min_price?: number
  max_price?: number
  is_featured?: boolean
  sort_by?: SortBy
  sort_dir?: SortDir
}

export function useProducts(filters: ProductFilters = {}) {
  return useQuery<ProductListResponse>({
    queryKey: ['products', filters],
    queryFn: () => productsApi.list(filters as Record<string, unknown>),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  })
}

export function useProduct(id: number | string | undefined) {
  return useQuery<ProductResponse>({
    queryKey: ['product', id],
    queryFn: () => productsApi.get(id as number | string),
    enabled: id !== undefined,
    staleTime: 30_000,
  })
}