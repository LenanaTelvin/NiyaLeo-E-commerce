import { useQuery, keepPreviousData, useQueryClient, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { productsApi } from '@/lib/api/products'
import type { ProductListResponse, ProductResponse, ProductCreate, ProductUpdate, MyProductListParams } from '@/types/product'

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

export function useMyProducts(params: MyProductListParams = {}) {
  return useQuery({
    queryKey: ['seller-products', params],
    queryFn: () => productsApi.listMine(params as Record<string, unknown>),
    staleTime: 10_000,
  })
}

export function useCreateProduct() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProductCreate) => productsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['seller-products'] })
      toast.success('Product created')
    },
    onError: () => toast.error('Could not create product'),
  })
}

export function useUpdateProduct() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProductUpdate }) => productsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['seller-products'] })
      toast.success('Product updated')
    },
    onError: () => toast.error('Could not update product'),
  })
}

export function useMyProduct(id: number | undefined) {
  return useQuery({
    queryKey: ['seller-product', id],
    queryFn: () => productsApi.getMine(id as number),
    enabled: id !== undefined,
  })
}

export function useDeleteProduct() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => productsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['seller-products'] })
      toast.success('Product archived')
    },
    onError: () => toast.error('Could not delete product'),
  })
}

export function useTogglePublish() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, is_published }: { id: number; is_published: boolean }) =>
      productsApi.togglePublish(id, is_published),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['seller-products'] }),
    onError: () => toast.error('Could not update publish status'),
  })
}