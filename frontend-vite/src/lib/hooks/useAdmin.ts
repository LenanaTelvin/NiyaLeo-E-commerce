import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { adminApi } from '@/lib/api/admin'

export function useAdminDashboard() {
  return useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: adminApi.getDashboard,
    staleTime: 0,
  })
}

export function usePendingSellers(page = 1) {
  return useQuery({
    queryKey: ['admin-pending-sellers', page],
    queryFn: () => adminApi.listPendingSellers({ page, per_page: 20 }),
    staleTime: 5_000,
  })
}

export function useSellerAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sellerId, action, reason }: {
      sellerId: number
      action: 'approved' | 'rejected' | 'suspended'
      reason?: string
    }) => adminApi.actionOnSeller(sellerId, action, reason),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ['admin-pending-sellers'] })
      qc.invalidateQueries({ queryKey: ['admin-dashboard'] })
      const messages = {
        approved: 'Seller approved',
        rejected: 'Application rejected',
        suspended: 'Seller suspended',
      }
      toast.success(messages[variables.action])
    },
    onError: () => toast.error('Action failed — please try again'),
  })
}

export function useRecentActivity(limit = 20) {
  return useQuery({
    queryKey: ['admin-activity', limit],
    queryFn: () => adminApi.getActivity({ limit }),
    staleTime: 15_000,
  })
}