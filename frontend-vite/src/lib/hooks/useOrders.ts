import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'
import { ordersApi } from '@/lib/api/orders'

// ── Customer ──

export function useMyOrders(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['my-orders', params],
    queryFn: () => ordersApi.list(params),
    staleTime: 10_000,
  })
}

export function useOrder(id: number | undefined) {
  return useQuery({
    queryKey: ['order', id],
    queryFn: () => ordersApi.get(id as number),
    enabled: id !== undefined,
  })
}

export function useCreateOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ cartId, notes }: { cartId: number; notes?: string }) =>
      ordersApi.create(cartId, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-orders'] })
      qc.invalidateQueries({ queryKey: ['cart'] })
    },
    onError: err => {
      if (isAxiosError(err) && err.response?.status === 409) {
        toast.error('Your cart is no longer active')
        return
      }
      if (isAxiosError(err) && err.response?.status === 400) {
        toast.error(err.response.data?.detail || 'Could not place order')
        return
      }
      toast.error('Could not place order — please try again')
    },
  })
}

export function useCancelOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => ordersApi.cancel(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['my-orders'] })
      qc.invalidateQueries({ queryKey: ['order', id] })
      toast.success('Order cancelled')
    },
    onError: err => {
      if (isAxiosError(err) && err.response?.status === 400) {
        toast.error(err.response.data?.detail || 'This order can no longer be cancelled')
        return
      }
      toast.error('Could not cancel order')
    },
  })
}

// ── Seller ──

export function useIncomingOrders(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['seller-orders', params],
    queryFn: () => ordersApi.listIncoming(params),
    staleTime: 10_000,
  })
}

export function useUpdateSellerOrderStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sellerOrderId, data }: {
      sellerOrderId: number
      data: { status: string; tracking_number?: string; note?: string }
    }) => ordersApi.updateSellerOrderStatus(sellerOrderId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['seller-orders'] })
      toast.success('Order status updated')
    },
    onError: err => {
      if (isAxiosError(err) && err.response?.status === 400) {
        toast.error(err.response.data?.detail || 'Invalid status transition')
        return
      }
      toast.error('Could not update order status')
    },
  })
}