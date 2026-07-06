import { apiClient } from './client'
import type { Cart, CartValidationResult } from '@/types/cart'

export const cartApi = {
  get: () => apiClient.get<Cart>('/api/v1/cart/').then(r => r.data),

  addItem: (data: { product_id: number; variant_id?: number; quantity?: number }) =>
    apiClient.post<Cart>('/api/v1/cart/items', data).then(r => r.data),

  updateItem: (itemId: number, data: { quantity?: number; saved_for_later?: boolean }) =>
    apiClient.patch<Cart>(`/api/v1/cart/items/${itemId}`, data).then(r => r.data),

  removeItem: (itemId: number) =>
    apiClient.delete<Cart>(`/api/v1/cart/items/${itemId}`).then(r => r.data),

  clear: () => apiClient.delete<Cart>('/api/v1/cart/').then(r => r.data),

  updateCart: (data: { coupon_code?: string; notes?: string; shipping_address_id?: number }) =>
    apiClient.patch<Cart>('/api/v1/cart/', data).then(r => r.data),

  validate: () => apiClient.post<CartValidationResult>('/api/v1/cart/validate').then(r => r.data),

  saveForLater: (itemId: number) =>
    apiClient.post<Cart>(`/api/v1/cart/items/${itemId}/save-for-later`).then(r => r.data),

  moveToCart: (itemId: number) =>
    apiClient.post<Cart>(`/api/v1/cart/items/${itemId}/move-to-cart`).then(r => r.data),
}