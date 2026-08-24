import { apiClient } from './client'
import type { StoreTheme } from '@/types/store'


export interface StoreCustomization {
  id: number
  seller_id: number
  theme: string
  theme_type: string
  primary_color: string
  secondary_color: string
  accent_color: string
  background_color: string
  text_color: string
  font_family: string
  heading_font: string
  font_size: string
  meta_title: string | null
  meta_description: string | null
  social_links: Record<string, string | null>
  contact_info: Record<string, string | null>
  custom_css: string | null
}

export interface StoreCustomizationUpdate {
  theme_type?: string
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  background_color?: string
  text_color?: string
  font_family?: string
  font_size?: string
  meta_title?: string
  meta_description?: string
  social_links?: Record<string, string | null>
  contact_info?: Record<string, string | null>
}

export interface StoreThemeConfig {
  store_name: string
  store_slug: string
  store_logo?: string
  store_banner?: string
  store_description?: string

  theme: string
  primary_color: string
  secondary_color: string
  accent_color: string
  background_color: string
  text_color: string
  font_family: string
  heading_font: string
  font_size: string

  layout: Record<string, unknown>
  header_config: Record<string, unknown>
  footer_config: Record<string, unknown>
  product_page_config: Record<string, unknown>

  custom_css?: string
  custom_js?: string

  meta: Record<string, string | null>
  social_links: Record<string, string | null>
  contact_info: Record<string, string | null>
}

export const storesApi = {
  // Get available theme presets
  listThemes: () =>
    apiClient
      .get<{ themes: StoreTheme[] }>('/api/v1/stores-themes')
      .then(r => r.data.themes),

  // Get current seller's customization
  getMyStore: () =>
    apiClient
      .get<StoreCustomization>('/api/v1/stores/me')
      .then(r => r.data),

  // Apply a theme preset (fills colors/fonts from the preset)
  applyTheme: (themeType: string) =>
    apiClient
      .post(`/api/v1/stores/me/apply-theme?theme_type=${themeType}`)
      .then(r => r.data),

  // Save customization changes
  updateMyStore: (data: StoreCustomizationUpdate) =>
    apiClient
      .put<StoreCustomization>('/api/v1/stores/me', data)
      .then(r => r.data),

  // Get the full rendered theme config (what the public storefront reads)
  getThemeConfig: () =>
    apiClient
      .get('/api/v1/stores/me/theme-config')
      .then(r => r.data),

  // Public — theme config for a specific seller's storefront, by slug
  getPublicThemeConfig: (storeSlug: string) =>
    apiClient
      .get<StoreThemeConfig>(`/api/v1/stores/${storeSlug}/theme`)
      .then(r => r.data),

  getPages: () =>
    apiClient.get('/api/v1/stores/me/pages').then(r => r.data),

  createPage: (data: any) =>
    apiClient.post('/api/v1/stores/me/pages', data).then(r => r.data),

  updatePage: (id: number, data: any) =>
    apiClient.put(`/api/v1/stores/me/pages/${id}`, data).then(r => r.data),

  deletePage: (id: number) =>
    apiClient.delete(`/api/v1/stores/me/pages/${id}`),

  // ── Sections ──────────────────────────────────────────────
  getSections: () =>
    apiClient.get('/api/v1/stores/me/sections').then(r => r.data),

  createSection: (data: any) =>
    apiClient.post('/api/v1/stores/me/sections', data).then(r => r.data),

  updateSection: (id: number, data: any) =>
    apiClient.put(`/api/v1/stores/me/sections/${id}`, data).then(r => r.data),

  deleteSection: (id: number) =>
    apiClient.delete(`/api/v1/stores/me/sections/${id}`),

  // ── Media ─────────────────────────────────────────────────
  getMedia: (media_type?: string) =>
    apiClient
      .get('/api/v1/stores/me/media', { params: media_type ? { media_type } : undefined })
      .then(r => r.data),

  addMedia: (data: any) =>
    apiClient.post('/api/v1/stores/me/media', data).then(r => r.data),

  deleteMedia: (id: number) =>
    apiClient.delete(`/api/v1/stores/me/media/${id}`),
}