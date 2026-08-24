import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useMyProduct, useUpdateProduct } from '@/lib/hooks/useProducts'
import { useCategories } from '@/lib/hooks/useCategories'

const schema = z.object({
  name: z.string().min(2, 'Product name is required'),
  short_description: z.string().optional(),
  description: z.string().optional(),
  price: z.coerce.number().positive('Price must be greater than 0'),
  compare_price: z.coerce.number().optional(),
  stock_quantity: z.coerce.number().int().min(0),
  category_id: z.coerce.number().optional(),
  is_featured: z.boolean().optional(),
})

type FormInput = z.input<typeof schema>
type FormValues = z.output<typeof schema>

export default function EditProductPage() {
  const { id } = useParams<{ id: string }>()
  const productId = id ? Number(id) : undefined
  const navigate = useNavigate()

  const { data: product, isLoading } = useMyProduct(productId)
  const { data: categories } = useCategories()
  const updateProduct = useUpdateProduct()

  const {
    register, handleSubmit, reset,
    formState: { errors, isSubmitting },
  } = useForm<FormInput, unknown, FormValues>({ resolver: zodResolver(schema) })

  // Populate the form once the product data arrives
  useEffect(() => {
    if (product) {
      reset({
        name: product.name,
        short_description: product.short_description ?? '',
        description: product.description ?? '',
        price: product.price,
        compare_price: product.compare_price ?? undefined,
        stock_quantity: product.stock_quantity,
        category_id: product.category?.id,
        is_featured: product.is_featured,
      })
    }
  }, [product, reset])

  const onSubmit = async (values: FormValues) => {
    if (!productId) return
    await updateProduct.mutateAsync({
      id: productId,
      data: {
        name: values.name,
        short_description: values.short_description,
        description: values.description,
        price: values.price,
        compare_price: values.compare_price || undefined,
        stock_quantity: values.stock_quantity,
        category_id: values.category_id || undefined,
        is_featured: values.is_featured,
      },
    })
    navigate('/seller/products')
  }

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="h-96 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <p className="text-gray-900 font-medium">Product not found</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Edit product</h1>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        <Field label="Product name" error={errors.name?.message}>
          <input className="input" {...register('name')} />
        </Field>

        <Field label="Short description">
          <input className="input" {...register('short_description')} />
        </Field>

        <Field label="Description">
          <textarea rows={4} className="input resize-none" {...register('description')} />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Price (KES)" error={errors.price?.message}>
            <input type="number" step="0.01" className="input" {...register('price')} />
          </Field>
          <Field label="Compare-at price" error={errors.compare_price?.message}>
            <input type="number" step="0.01" className="input" {...register('compare_price')} />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Stock quantity" error={errors.stock_quantity?.message}>
            <input type="number" className="input" {...register('stock_quantity')} />
          </Field>
          <Field label="Category">
            <select className="input" {...register('category_id')}>
              <option value="">None</option>
              {categories?.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </Field>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" {...register('is_featured')} />
          Feature this product
        </label>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gray-900 text-white py-3 rounded-xl font-medium hover:bg-gray-800 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          {isSubmitting ? 'Saving…' : 'Save changes'}
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