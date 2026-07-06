export type ProductStatus = 'draft' | 'active' | 'inactive' | 'out_of_stock' | 'archived'

export interface Category {
  id: number
  name: string
  slug: string
  parent_id?: number
  children: Category[]
}

export interface Tag {
  id: number
  name: string
  slug: string
}

export interface ProductMedia {
  id: number
  product_id: number
  url: string
  media_type: 'image' | 'video'
  alt_text?: string
  is_primary: boolean
  sort_order: number
}

export interface ProductVariant {
  id: number
  product_id: number
  name: string
  sku?: string
  price_override?: number
  stock_quantity: number
  is_active: boolean
  attributes?: Record<string, string> // e.g. { color: "red", size: "L" }
  image_url?: string
}

export type ProductCondition = 'new' | 'used' | 'refurbished'

export interface ProductResponse {
  id: number
  seller_id: number
  name: string
  slug: string
  description?: string
  short_description?: string

  price: number
  compare_price?: number

  sku?: string
  stock_quantity: number
  track_inventory: boolean
  allow_backorder: boolean

  condition: ProductCondition
  is_digital: boolean
  is_featured: boolean

  status: ProductStatus
  is_published: boolean

  category?: Category
  tags: Tag[]
  images: ProductMedia[]
  variants: ProductVariant[]
  primary_image_url?: string

  created_at: string
  updated_at?: string
}

export interface ProductListItem {
  id: number
  seller_id: number
  name: string
  slug: string
  short_description?: string
  price: number
  compare_price?: number
  stock_quantity: number
  status: ProductStatus
  is_published: boolean
  is_featured: boolean
  primary_image_url?: string
  category?: Category
  tags: Tag[]
  created_at: string
}

export interface ProductListResponse {
  items: ProductListItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
}