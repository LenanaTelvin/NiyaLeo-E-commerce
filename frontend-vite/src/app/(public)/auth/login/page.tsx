import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { isAxiosError } from 'axios'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/lib/store/authStore'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type LoginFormValues = z.infer<typeof schema>

function redirectPathForRole(role: 'admin' | 'seller' | 'customer'): string {
  switch (role) {
    case 'admin':
      return '/admin/dashboard'
    case 'seller':
      return '/seller/dashboard'
    default:
      return '/'
  }
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const setAuth = useAuthStore(s => s.setAuth)
  const [showPassword, setShowPassword] = useState(false)

  const from = (location.state as { from?: string } | null)?.from ||
    sessionStorage.getItem('redirect_after_login')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (values: LoginFormValues) => {
    try {
      const data = await authApi.login(values)
      setAuth(data.user, data.access_token, data.refresh_token)
      sessionStorage.removeItem('redirect_after_login')
      navigate(from || redirectPathForRole(data.user.role), { replace: true })
    } catch (err) {
      if (isAxiosError(err)) {
        if (err.response?.status === 401) {
          toast.error('Invalid email or password')
          return
        }
        if (err.response?.status === 422) {
          toast.error('Please check your details and try again')
          return
        }
      }
      toast.error('Something went wrong — please try again')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-2xl shadow-sm p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center mb-4">
            <span className="text-white font-semibold text-sm">FC</span>
          </div>
          <h1 className="text-xl font-semibold text-gray-900">Sign in to Free Commerce</h1>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900"
              {...register('email')}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                className="w-full px-4 py-3 pr-11 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900"
                {...register('password')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(prev => !prev)}
                className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-gray-400 hover:text-gray-600"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gray-900 text-white py-3 rounded-xl font-medium hover:bg-gray-800 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Don&apos;t have an account?{' '}
          <Link to="/auth/register" className="text-gray-900 font-medium hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
