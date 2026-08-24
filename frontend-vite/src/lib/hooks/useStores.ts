import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { storesApi } from '@/lib/api/stores'
import { sellersApi } from '@/lib/api/sellers'

export function usePublicSellers(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['public-sellers', params],
    queryFn: () => sellersApi.listPublic(params),
    staleTime: 30_000,
  })
}

export function useStoreTheme(storeSlug: string | undefined) {
  return useQuery({
    queryKey: ['store-theme', storeSlug],
    queryFn: () => storesApi.getPublicThemeConfig(storeSlug as string),
    enabled: !!storeSlug,
    staleTime: 30_000,
  })
}

export function useStoreThemes() {
  return useQuery({
    queryKey: ['store', 'themes'],
    queryFn: storesApi.listThemes,
  })
}

export function useSellerIdFromSlug(slug: string | undefined) {
  return useQuery({
    queryKey: ['seller-by-slug', slug],
    queryFn: () => sellersApi.getPublic(slug as string),
    enabled: !!slug,
    staleTime: 60_000,
    select: data => data.id,
  })
}

// ── Seller store customization ────────────────────────────────────────

export function useMyStore() {
  return useQuery({
    queryKey: ['store', 'me'],
    queryFn: storesApi.getMyStore,
  })
}

export function useUpdateMyStore() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.updateMyStore,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'me'] }),
  })
}

export function useApplyTheme() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ theme_type }: { theme_type: string; preserve_colors?: boolean }) =>
      storesApi.applyTheme(theme_type),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'me'] }),
  })
}

export function useStorePages() {
  return useQuery({ queryKey: ['store', 'pages'], queryFn: storesApi.getPages })
}

export function useCreatePage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.createPage,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'pages'] }),
  })
}

export function useUpdatePage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => storesApi.updatePage(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'pages'] }),
  })
}

export function useDeletePage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.deletePage,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'pages'] }),
  })
}

export function useStoreSections() {
  return useQuery({ queryKey: ['store', 'sections'], queryFn: storesApi.getSections })
}

export function useCreateSection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.createSection,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'sections'] }),
  })
}

export function useUpdateSection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => storesApi.updateSection(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'sections'] }),
  })
}

export function useDeleteSection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.deleteSection,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'sections'] }),
  })
}

export function useStoreMedia(media_type?: string) {
  return useQuery({
    queryKey: ['store', 'media', media_type ?? 'all'],
    queryFn: () => storesApi.getMedia(media_type),
  })
}

export function useAddMedia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.addMedia,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'media'] }),
  })
}

export function useDeleteMedia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: storesApi.deleteMedia,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['store', 'media'] }),
  })
}