export type StoreThemeType = 'modern' | 'minimalist' | 'vibrant' | 'elegant' | 'bold' | 'custom'
export type StorePageType = 'home' | 'about' | 'contact' | 'faq' | 'policy' | 'custom'

export interface StoreCustomization {
  id: number
  seller_id: number
  theme: string
  theme_type: StoreThemeType
  primary_color: string
  secondary_color: string
  accent_color: string
  background_color: string
  text_color: string
  font_family: string
  heading_font?: string
  font_size: string
  layout: Record<string, unknown>
  header_config: Record<string, unknown>
  footer_config: Record<string, unknown>
  product_page_config: Record<string, unknown>
  custom_css: string | null
  custom_js: string | null
  custom_head_html: string | null
  custom_body_html: string | null
  meta_title: string | null
  meta_description: string | null
  meta_keywords: string | null
  og_image: string | null
  social_links: Record<string, string | null>
  contact_info: Record<string, string | null>
  created_at: string
  updated_at: string
}

export interface StoreCustomizationUpdate {
  theme_type?: StoreThemeType
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  background_color?: string
  text_color?: string
  font_family?: string
  heading_font?: string 
  font_size?: string
  layout?: Record<string, unknown>
  header_config?: Record<string, unknown>
  footer_config?: Record<string, unknown>
  product_page_config?: Record<string, unknown>
  custom_css?: string
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  social_links?: Record<string, string | null>
  contact_info?: Record<string, string | null>
}

export interface StoreTheme {
  id: StoreThemeType
  name: string
  description: string
  preview_image: string
  features: string[]
}

export interface StorePage {
  id: number
  store_id: number
  title: string
  slug: string
  page_type: StorePageType
  content: string | null
  content_json: Record<string, unknown> | null
  meta_title: string | null
  meta_description: string | null
  is_published: boolean
  is_featured: boolean
  show_in_nav: boolean
  nav_order: number
  created_at: string
  updated_at: string
}

export interface StorePageCreate {
  title: string
  slug: string
  page_type: StorePageType
  content?: string
  is_published: boolean
  show_in_nav: boolean
  nav_order: number
  store_id: number
}

export interface StorePageUpdate {
  title?: string
  slug?: string
  content?: string
  is_published?: boolean
  show_in_nav?: boolean
  nav_order?: number
}

export interface StoreSection {
  id: number
  store_id: number
  title: string | null
  section_type: string
  section_key: string | null
  content: Record<string, unknown>
  layout: Record<string, unknown>
  is_active: boolean
  is_featured: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface StoreSectionCreate {
  title?: string
  section_type: string
  section_key?: string
  content?: Record<string, unknown>
  layout?: Record<string, unknown>
  is_active: boolean
  order: number
  store_id: number
}

export interface StoreMedia {
  id: number
  seller_id: number
  media_type: string
  title: string | null
  url: string
  alt_text: string | null
  order: number
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface StoreMediaCreate {
  media_type: string
  title?: string
  url: string
  alt_text?: string
  is_default: boolean
  seller_id: number
}