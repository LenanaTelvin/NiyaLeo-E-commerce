export type OrderStatus = 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'refunded'
export type SellerOrderStatus = 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled'

export interface OrderStatusHistoryItem {
  id: number
  from_status?: string
  to_status: string
  note?: string
  changed_by?: number
  created_at: string
}

export interface SellerOrderItem {
  id: number
  product_id?: number
  variant_id?: number
  product_name: string
  product_sku?: string
  variant_name?: string
  unit_price: number
  quantity: number
  subtotal: number
}

export interface SellerOrder {
  id: number
  order_id: number
  seller_id?: number
  subtotal: number
  commission_rate: number
  commission_amount: number
  seller_earnings: number
  status: SellerOrderStatus
  tracking_number?: string
  shipped_at?: string
  delivered_at?: string
  created_at: string
  updated_at?: string
  items: SellerOrderItem[]
  status_history: OrderStatusHistoryItem[]
}

export interface Order {
  id: number
  order_number?: string
  user_id?: number
  cart_id?: number
  subtotal: number
  discount_amount: number
  shipping_amount: number
  total: number
  currency: string
  shipping_address?: Record<string, string>
  notes?: string
  coupon_code?: string
  status: OrderStatus
  created_at: string
  updated_at?: string
  seller_orders: SellerOrder[]
  status_history: OrderStatusHistoryItem[]
}

export interface OrderListItem {
  id: number
  order_number?: string
  status: OrderStatus
  total: number
  currency: string
  item_count: number
  seller_count: number
  created_at: string
}

export interface OrderListResponse {
  items: OrderListItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// Only forward transitions are valid — mirrors backend SELLER_STATUS_TRANSITIONS
export const SELLER_STATUS_TRANSITIONS: Record<SellerOrderStatus, SellerOrderStatus[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['processing', 'cancelled'],
  processing: ['shipped'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
}