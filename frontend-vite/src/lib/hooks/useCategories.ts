import { useQuery } from '@tanstack/react-query'
import { categoriesApi } from '@/lib/api/categories'

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.list,
    staleTime: 5 * 60_000, // categories change rarely
  })
}