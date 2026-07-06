import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/lib/store/authStore'

interface Props {
  children: ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    // Preserve where the user was trying to go, so login can send them back
    return <Navigate to="/auth/login" state={{ from: location.pathname }} replace />
  }

  return <>{children}</>
}