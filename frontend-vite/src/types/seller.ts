export type BusinessType =
  | 'individual'
  | 'sole_proprietorship'
  | 'partnership'
  | 'llc'
  | 'corporation'
  | 'non_profit'

export type StoreStatus = 'pending' | 'approved' | 'suspended' | 'rejected' | 'closed'

export interface SellerProfileCreate {
  business_name: string
  business_type: BusinessType
  business_registration_number?: string
  tax_id?: string
  phone_number?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  store_name: string
  store_slug: string
  store_description?: string
  store_logo_url?: string
  store_banner_url?: string
}

export interface SellerProfile extends SellerProfileCreate {
  id: number
  user_id: number
  status: StoreStatus
  is_active: boolean
  is_verified: boolean
  custom_commission_rate?: number
  created_at: string
  updated_at?: string
  approved_at?: string
  suspended_at?: string
  suspension_reason?: string
}

export interface SellerRecentOrder {
  id: number
  order_number?: string
  status: string
  subtotal: number
  seller_earnings: number
  created_at: string
}

export interface SellerDashboardStats {
  total_products: number
  total_orders: number
  total_revenue: number
  total_commission: number
  pending_orders: number
  total_earnings: number
  average_rating: number
  total_reviews: number
  recent_orders: SellerRecentOrder[]
  sales_chart: {
    labels: string[]
    values: number[]
  }
}