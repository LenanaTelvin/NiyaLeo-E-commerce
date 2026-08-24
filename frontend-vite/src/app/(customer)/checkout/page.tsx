import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Phone, CheckCircle, XCircle, Loader2, ShoppingBag } from 'lucide-react'
import { useCart } from '@/lib/hooks/useCart'
import { apiClient } from '@/lib/api/client'
import type { CartItem } from '@/types/cart'

// ── Types ─────────────────────────────────────────────────────────────

type CheckoutStep = 'summary' | 'phone' | 'waiting' | 'success' | 'failed'

interface OrderResponse {
  id: number
  order_number: string
  total: number
}

interface PaymentResponse {
  id: number
  status: 'pending' | 'completed' | 'failed' | 'timeout'
  checkout_request_id: string
  mpesa_receipt_number: string | null
  result_desc: string | null
}

// ── Helpers ───────────────────────────────────────────────────────────

const formatPrice = (n: number) =>
  new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES' }).format(n)

function normalizePhone(raw: string): string {
  const digits = raw.replace(/\D/g, '')
  if (digits.startsWith('0') && digits.length === 10) return '254' + digits.slice(1)
  if (digits.startsWith('254') && digits.length === 12) return digits
  if (digits.startsWith('7') && digits.length === 9) return '254' + digits
  return digits
}

function isValidPhone(raw: string): boolean {
  const n = normalizePhone(raw)
  return /^2547\d{8}$/.test(n)
}

// ── Main component ────────────────────────────────────────────────────

export default function CheckoutPage() {
  const { data: cart, isLoading } = useCart()

  const [step, setStep] = useState<CheckoutStep>('summary')
  const [phone, setPhone] = useState('')
  const [phoneError, setPhoneError] = useState('')
  const [notes, setNotes] = useState('')
  const [isPlacingOrder, setIsPlacingOrder] = useState(false)
  const [order, setOrder] = useState<OrderResponse | null>(null)
  const [payment, setPayment] = useState<PaymentResponse | null>(null)
  const [error, setError] = useState('')

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollCount = useRef(0)
  const MAX_POLLS = 24 // 2 min at 5s intervals

  // ── Polling ──────────────────────────────────────────────────────────

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  async function pollStatus(checkoutRequestId: string) {
    try {
      const res = await apiClient.get<PaymentResponse>(
        `/api/v1/payments/mpesa/status/${checkoutRequestId}`
      )
      const p = res.data
      setPayment(p)

      if (p.status === 'completed') {
        stopPolling()
        setStep('success')
      } else if (p.status === 'failed' || p.status === 'timeout') {
        stopPolling()
        setError(p.result_desc ?? 'Payment failed. Please try again.')
        setStep('failed')
      } else {
        pollCount.current += 1
        if (pollCount.current >= MAX_POLLS) {
          stopPolling()
          setError('Payment timed out. Check your M-Pesa messages and try again.')
          setStep('failed')
        }
      }
    } catch {
      // Network hiccup — keep polling
    }
  }

  useEffect(() => {
    return () => stopPolling()
  }, [])

  // ── Handlers ─────────────────────────────────────────────────────────

  async function handlePlaceOrder() {
    if (!cart) return
    if (!isValidPhone(phone)) {
      setPhoneError('Enter a valid Safaricom number e.g. 0712 345 678')
      return
    }
    setPhoneError('')
    setIsPlacingOrder(true)
    setError('')

    try {
      // 1. Create order
      const orderRes = await apiClient.post<OrderResponse>('/api/v1/orders/', {
        cart_id: cart.id,
        notes: notes || null,
      })
      const newOrder = orderRes.data
      setOrder(newOrder)

      // 2. Initiate M-Pesa STK push
      const payRes = await apiClient.post<PaymentResponse>('/api/v1/payments/mpesa/initiate', {
        order_id: newOrder.id,
        phone_number: normalizePhone(phone),
      })
      const newPayment = payRes.data
      setPayment(newPayment)
      setStep('waiting')

      // 3. Start polling
      pollCount.current = 0
      pollRef.current = setInterval(() => {
        pollStatus(newPayment.checkout_request_id)
      }, 5000)

    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Something went wrong. Please try again.'
      setError(msg)
      setStep('failed')
    } finally {
      setIsPlacingOrder(false)
    }
  }

  // ── Loading ───────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="max-w-lg mx-auto px-6 py-12 space-y-4 animate-pulse">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 rounded-xl" />
        ))}
      </div>
    )
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-lg mx-auto px-6 py-20 text-center">
        <ShoppingBag className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-900 font-medium mb-1">Your cart is empty</p>
        <Link to="/products" className="text-sm text-gray-500 underline">Browse products</Link>
      </div>
    )
  }

  // ── Steps ─────────────────────────────────────────────────────────────

  // SUCCESS
  if (step === 'success') {
    return (
      <div className="max-w-lg mx-auto px-6 py-20 text-center">
        <CheckCircle className="w-14 h-14 text-green-500 mx-auto mb-4" />
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Payment confirmed!</h1>
        <p className="text-sm text-gray-500 mb-1">
          Order <span className="font-medium text-gray-900">{order?.order_number}</span> is being processed.
        </p>
        {payment?.mpesa_receipt_number && (
          <p className="text-xs text-gray-400 mb-6">
            M-Pesa receipt: {payment.mpesa_receipt_number}
          </p>
        )}
        <div className="flex flex-col gap-3">
          <Link
            to="/orders"
            className="block bg-gray-900 text-white text-sm font-medium py-2.5 rounded-xl hover:bg-gray-700"
          >
            View my orders
          </Link>
          <Link
            to="/products"
            className="block border border-gray-200 text-gray-700 text-sm font-medium py-2.5 rounded-xl hover:border-gray-400"
          >
            Continue shopping
          </Link>
        </div>
      </div>
    )
  }

  // FAILED
  if (step === 'failed') {
    return (
      <div className="max-w-lg mx-auto px-6 py-20 text-center">
        <XCircle className="w-14 h-14 text-red-400 mx-auto mb-4" />
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Payment failed</h1>
        <p className="text-sm text-gray-500 mb-6">{error || 'Something went wrong.'}</p>
        <div className="flex flex-col gap-3">
          <button
            onClick={() => { setStep('phone'); setError('') }}
            className="block bg-gray-900 text-white text-sm font-medium py-2.5 rounded-xl hover:bg-gray-700"
          >
            Try again
          </button>
          <Link
            to="/cart"
            className="block border border-gray-200 text-gray-700 text-sm font-medium py-2.5 rounded-xl hover:border-gray-400"
          >
            Back to cart
          </Link>
        </div>
      </div>
    )
  }

  // WAITING
  if (step === 'waiting') {
    return (
      <div className="max-w-lg mx-auto px-6 py-20 text-center">
        <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Phone className="w-7 h-7 text-green-600" />
        </div>
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Check your phone</h1>
        <p className="text-sm text-gray-500 mb-1">
          An M-Pesa prompt has been sent to <span className="font-medium text-gray-900">{phone}</span>
        </p>
        <p className="text-sm text-gray-400 mb-8">
          Enter your M-Pesa PIN to complete payment of{' '}
          <span className="font-medium text-gray-900">{formatPrice(cart.summary.total)}</span>
        </p>

        <div className="flex items-center justify-center gap-2 text-sm text-gray-400 mb-8">
          <Loader2 className="w-4 h-4 animate-spin" />
          Waiting for payment confirmation…
        </div>

        <button
          onClick={() => { stopPolling(); setStep('phone') }}
          className="text-sm text-gray-400 underline underline-offset-2 hover:text-gray-700"
        >
          Cancel and go back
        </button>
      </div>
    )
  }

  // SUMMARY + PHONE (main checkout UI)
  return (
    <div className="max-w-lg mx-auto px-6 py-8">
      <Link to="/cart" className="inline-flex items-center gap-1 text-sm text-gray-400 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to cart
      </Link>

      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Checkout</h1>

      {/* Order summary */}
      <div className="border border-gray-100 rounded-xl overflow-hidden mb-5">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
          <p className="text-xs font-medium text-gray-500">Order summary</p>
        </div>
        <div className="divide-y divide-gray-100">
          {cart.items.map((item: CartItem) => (
            <div key={item.id} className="flex items-center gap-3 px-4 py-3">
              <div className="w-10 h-10 bg-gray-100 rounded-lg overflow-hidden shrink-0">
                {item.product?.primary_image_url ? (
                  <img
                    src={item.product.primary_image_url}
                    alt={item.product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gray-200" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 truncate">{item.product?.name ?? 'Product'}</p>
                <p className="text-xs text-gray-400">Qty: {item.quantity}</p>
              </div>
              <p className="text-sm font-medium text-gray-900 shrink-0">
                {formatPrice(item.subtotal)}
              </p>
            </div>
          ))}
        </div>

        {/* Totals */}
        <div className="px-4 py-3 border-t border-gray-100 space-y-1.5 text-sm">
          <div className="flex justify-between text-gray-500">
            <span>Subtotal</span>
            <span>{formatPrice(cart.summary.subtotal)}</span>
          </div>
          {cart.summary.savings > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Savings</span>
              <span>-{formatPrice(cart.summary.savings)}</span>
            </div>
          )}
          {cart.summary.discount_amount > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount</span>
              <span>-{formatPrice(cart.summary.discount_amount)}</span>
            </div>
          )}
          <div className="flex justify-between font-semibold text-gray-900 pt-1.5 border-t border-gray-100">
            <span>Total</span>
            <span>{formatPrice(cart.summary.total)}</span>
          </div>
        </div>
      </div>

      {/* Notes */}
      <div className="mb-5">
        <label className="text-xs text-gray-500 mb-1 block">Order notes (optional)</label>
        <textarea
          className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:border-gray-400"
          rows={2}
          placeholder="Special instructions for your order…"
          value={notes}
          onChange={e => setNotes(e.target.value)}
        />
      </div>

      {/* M-Pesa phone */}
      <div className="mb-6">
        <label className="text-xs text-gray-500 mb-1 block">M-Pesa phone number</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">+254</span>
          <input
            type="tel"
            className={`w-full border rounded-xl pl-12 pr-3 py-2.5 text-sm focus:outline-none ${
              phoneError ? 'border-red-300 focus:border-red-400' : 'border-gray-200 focus:border-gray-400'
            }`}
            placeholder="712 345 678"
            value={phone}
            onChange={e => { setPhone(e.target.value); setPhoneError('') }}
          />
        </div>
        {phoneError && <p className="text-xs text-red-500 mt-1">{phoneError}</p>}
        <p className="text-xs text-gray-400 mt-1">
          You'll receive an M-Pesa prompt to complete payment.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Pay button */}
      <button
        onClick={handlePlaceOrder}
        disabled={isPlacingOrder || !phone}
        className="w-full bg-green-600 text-white text-sm font-semibold py-3 rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
      >
        {isPlacingOrder ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Processing…
          </>
        ) : (
          <>
            <Phone className="w-4 h-4" />
            Pay {formatPrice(cart.summary.total)} via M-Pesa
          </>
        )}
      </button>

      <p className="text-xs text-gray-400 text-center mt-3">
        Secure payment powered by Safaricom M-Pesa
      </p>
    </div>
  )
}
