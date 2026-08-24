import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/lib/store/authStore'

interface Props {
  children: ReactNode
}

export default function RequireSeller({ children }: Props) {
  const { isAuthenticated, user } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location.pathname }} replace />
  }

  if (user?.role !== 'seller' && user?.role !== 'admin') {
    return <Navigate to="/account/become-seller" replace />
  }

  return <>{children}</>
}