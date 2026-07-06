export interface CartItemProductSummary {
  id: number
  name: string
  slug: string
  primary_image_url?: string
  sku?: string
}

export interface CartItemVariantSummary {
  id: number
  name: string
  sku?: string
  attributes?: Record<string, string>
  image_url?: string
}

export interface CartItemSellerSummary {
  id: number
  store_name: string
  store_slug: string
}

export interface CartItem {
  id: number
  cart_id: number
  product_id: number
  variant_id?: number
  quantity: number
  unit_price: number
  original_price?: number
  subtotal: number
  saved_for_later: boolean
  created_at: string
  updated_at?: string
  product?: CartItemProductSummary
  variant?: CartItemVariantSummary
  seller?: CartItemSellerSummary
}

export interface CartSummary {
  item_count: number
  total_quantity: number
  subtotal: number
  discount_amount: number
  total: number
  savings: number
  seller_count: number
}

export interface Cart {
  id: number
  user_id?: number
  session_id?: string
  status: string
  coupon_code?: string
  discount_amount: number
  shipping_address_id?: number
  notes?: string
  expires_at?: string
  created_at: string
  updated_at?: string
  items: CartItem[]
  saved_for_later: CartItem[]
  summary: CartSummary
}

export interface StockIssue {
  product_id: number
  variant_id?: number
  product_name: string
  requested_quantity: number
  available_quantity: number
}

export interface CartValidationResult {
  is_valid: boolean
  stock_issues: StockIssue[]
  removed_items: number[]
}