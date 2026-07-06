import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { cartApi } from '@/lib/api/cart'
import { useCartStore } from '@/lib/store/cartStore'
import type { Cart } from '@/types/cart'

const CART_KEY = ['cart']

export function useCart() {
  const setItemCount = useCartStore(s => s.setItemCount)

  const query = useQuery<Cart>({
    queryKey: CART_KEY,
    queryFn: cartApi.get,
    staleTime: 10_000,
  })

  // Keep the header's cart badge in sync with the server's real total_quantity,
  // rather than relying on the increment()/decrement() calls scattered around the app
  useEffect(() => {
    if (query.data) setItemCount(query.data.summary.total_quantity)
  }, [query.data, setItemCount])

  return query
}

export function useAddCartItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { product_id: number; variant_id?: number; quantity?: number }) =>
      cartApi.addItem(data),
    onSuccess: cart => {
      qc.setQueryData(CART_KEY, cart)
      toast.success('Added to cart')
    },
    onError: () => toast.error('Could not add to cart — sign in first'),
  })
}

export function useUpdateCartItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: { quantity?: number; saved_for_later?: boolean } }) =>
      cartApi.updateItem(itemId, data),
    onSuccess: cart => qc.setQueryData(CART_KEY, cart),
    onError: () => toast.error('Could not update item'),
  })
}

export function useRemoveCartItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: number) => cartApi.removeItem(itemId),
    onSuccess: cart => {
      qc.setQueryData(CART_KEY, cart)
      toast.success('Removed from cart')
    },
    onError: () => toast.error('Could not remove item'),
  })
}

export function useClearCart() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => cartApi.clear(),
    onSuccess: cart => qc.setQueryData(CART_KEY, cart),
  })
}

export function useSaveForLater() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: number) => cartApi.saveForLater(itemId),
    onSuccess: cart => qc.setQueryData(CART_KEY, cart),
  })
}

export function useMoveToCart() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: number) => cartApi.moveToCart(itemId),
    onSuccess: cart => {
      qc.setQueryData(CART_KEY, cart)
      toast.success('Moved to cart')
    },
  })
}