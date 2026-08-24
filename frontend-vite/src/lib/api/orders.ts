import { apiClient } from './client'
import type { Order, OrderListResponse, SellerOrder } from '@/types/order'

export const ordersApi = {
  // Customer
  create: (cart_id: number, notes?: string) =>
    apiClient.post<Order>('/api/v1/orders/', { cart_id, notes }).then(r => r.data),

  list: (params?: Record<string, unknown>) =>
    apiClient.get<OrderListResponse>('/api/v1/orders/', { params }).then(r => r.data),

  get: (id: number) =>
    apiClient.get<Order>(`/api/v1/orders/${id}`).then(r => r.data),

  cancel: (id: number) =>
    apiClient.delete<Order>(`/api/v1/orders/${id}/cancel`).then(r => r.data),

  // Seller
  listIncoming: (params?: Record<string, unknown>) =>
    apiClient.get<OrderListResponse>('/api/v1/seller/orders/', { params }).then(r => r.data),

  getSellerOrder: (sellerOrderId: number) =>
    apiClient.get<SellerOrder>(`/api/v1/seller/orders/${sellerOrderId}`).then(r => r.data),

  updateSellerOrderStatus: (
    sellerOrderId: number,
    data: { status: string; tracking_number?: string; note?: string }
  ) =>
    apiClient.patch<SellerOrder>(`/api/v1/seller/orders/${sellerOrderId}/status`, data).then(r => r.data),
}