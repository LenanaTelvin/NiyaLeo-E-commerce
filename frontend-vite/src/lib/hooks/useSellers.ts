import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'
import { sellersApi } from '@/lib/api/sellers'
import { useAuthStore } from '@/lib/store/authStore'
import type { SellerProfileCreate } from '@/types/seller'



export function useMyApplicationStatus() {
  return useQuery({
    queryKey: ['my-seller-application'],
    queryFn: () => sellersApi.getMyApplicationStatus(),
    staleTime: 10_000,
  })
}

export function useRegisterSeller() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: SellerProfileCreate) => sellersApi.register(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-seller-application'] })
      toast.success('Seller application submitted')
    },
    onError: err => {
      if (isAxiosError(err) && err.response?.status === 409) {
        toast.error('You already have a seller application on file')
        return
      }
      if (isAxiosError(err) && err.response?.status === 422) {
        toast.error('Please check your details and try again')
        return
      }
      toast.error('Something went wrong — please try again')
    },
  })
}

export function useSellerDashboard() {
  const userId = useAuthStore(s => s.user?.id)

  return useQuery({
    queryKey: ['seller-dashboard', userId],
    queryFn: () => sellersApi.getDashboardStats(),
    enabled: !!userId,
    //staleTime: 15_000,
  })
}