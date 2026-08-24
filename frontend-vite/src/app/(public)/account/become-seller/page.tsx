import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/lib/store/authStore'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Store, Clock, CheckCircle2, XCircle } from 'lucide-react'
import { useRegisterSeller, useMyApplicationStatus } from '@/lib/hooks/useSellers'
import type { BusinessType } from '@/types/seller'

const BUSINESS_TYPES: { value: BusinessType; label: string }[] = [
  { value: 'individual', label: 'Individual' },
  { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
  { value: 'partnership', label: 'Partnership' },
  { value: 'llc', label: 'LLC' },
  { value: 'corporation', label: 'Corporation' },
  { value: 'non_profit', label: 'Non-profit' },
]

const schema = z.object({
  business_name: z.string().min(2, 'Business name is required'),
  business_type: z.enum([
    'individual', 'sole_proprietorship', 'partnership', 'llc', 'corporation', 'non_profit',
  ]),
  phone_number: z.string().optional(),
  city: z.string().optional(),
  country: z.string().optional(),
  store_name: z.string().min(2, 'Store name is required'),
  store_slug: z
    .string()
    .min(3, 'Slug must be at least 3 characters')
    .regex(/^[a-z0-9-]+$/, 'Lowercase letters, numbers, and hyphens only'),
  store_description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

const slugify = (s: string) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')

export default function BecomeSellerPage() {
  const role = useAuthStore(s => s.user?.role)
  const { data: existingApplication, isLoading: checkingStatus } = useMyApplicationStatus()
  const registerSeller = useRegisterSeller()
  const [slugTouched, setSlugTouched] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { business_type: 'individual' },
  })

  const storeName = watch('store_name')

  // Auto-fill the slug from the store name until the person edits it directly
  const handleStoreNameChange = (value: string) => {
    setValue('store_name', value)
    if (!slugTouched) setValue('store_slug', slugify(value))
  }

  const onSubmit = async (values: FormValues) => {
    await registerSeller.mutateAsync(values)
  }


 if (role === 'admin') {
    return <Navigate to="/admin/dashboard" replace />
  }

 if (role === 'seller') {
    return <Navigate to="/seller/dashboard" replace />
  }
   
  // Still checking — avoid a flash of the empty form before we know the real status
  if (checkingStatus) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16">
        <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    )
  }

  // Already applied — real status from the server, not a cache
  if (existingApplication) {
    const profile = existingApplication
    return (
      <div className="max-w-lg mx-auto px-4 py-16">
        <div className="text-center">
          <StatusIcon status={profile.status} />
          <h1 className="text-xl font-semibold text-gray-900 mt-4 mb-1">
            {profile.store_name}
          </h1>
          <p className="text-sm text-gray-400 mb-6">
            Application {profile.status === 'pending' ? 'submitted' : profile.status}
          </p>
        </div>

        <div className="border border-gray-100 rounded-xl p-5 space-y-3 text-sm">
          <Row label="Business name" value={profile.business_name} />
          <Row label="Store slug" value={profile.store_slug} />
          <Row label="Status" value={statusLabel(profile.status)} />
          {profile.suspension_reason && (
            <Row label="Note" value={profile.suspension_reason} />
          )}
        </div>

        {profile.status === 'pending' && (
          <p className="text-xs text-gray-400 text-center mt-5">
            We'll review your application shortly. This page will update once a decision is made —
            check back here, or watch for an email.
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-12">
      <div className="text-center mb-8">
        <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center mx-auto mb-4">
          <Store className="w-5 h-5 text-white" />
        </div>
        <h1 className="text-xl font-semibold text-gray-900">Become a seller</h1>
        <p className="text-sm text-gray-400 mt-1">
          Tell us about your business — an admin will review your application.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        <Field label="Business name" error={errors.business_name?.message}>
          <input
            id="business_name"
            className="input"
            {...register('business_name')}
          />
        </Field>

        <Field label="Business type" error={errors.business_type?.message}>
          <select id="business_type" className="input" {...register('business_type')}>
            {BUSINESS_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Phone number">
            <input id="phone_number" className="input" {...register('phone_number')} />
          </Field>
          <Field label="City">
            <input id="city" className="input" {...register('city')} />
          </Field>
        </div>

        <Field label="Country">
          <input id="country" className="input" {...register('country')} />
        </Field>

        <hr className="border-gray-100" />

        <Field label="Store name" error={errors.store_name?.message}>
          <input
            id="store_name"
            className="input"
            value={storeName ?? ''}
            onChange={e => handleStoreNameChange(e.target.value)}
          />
        </Field>

        <Field
          label="Store URL"
          error={errors.store_slug?.message}
          hint="freecommerce.com/stores/your-slug"
        >
          <input
            id="store_slug"
            className="input"
            {...register('store_slug', {
              onChange: () => setSlugTouched(true),
            })}
          />
        </Field>

        <Field label="Store description">
          <textarea
            id="store_description"
            rows={3}
            className="input resize-none"
            {...register('store_description')}
          />
        </Field>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gray-900 text-white py-3 rounded-xl font-medium hover:bg-gray-800 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          {isSubmitting ? 'Submitting…' : 'Submit application'}
        </button>
      </form>
    </div>
  )
}

function Field({
  label, error, hint, children,
}: { label: string; error?: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      {children}
      {hint && !error && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-900 font-medium">{value}</span>
    </div>
  )
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'approved') return <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto" />
  if (status === 'rejected' || status === 'suspended') return <XCircle className="w-10 h-10 text-red-500 mx-auto" />
  return <Clock className="w-10 h-10 text-amber-500 mx-auto" />
}

function statusLabel(status: string) {
  switch (status) {
    case 'pending': return 'Pending review'
    case 'approved': return 'Approved'
    case 'rejected': return 'Rejected'
    case 'suspended': return 'Suspended'
    case 'closed': return 'Closed'
    default: return status
  }
}