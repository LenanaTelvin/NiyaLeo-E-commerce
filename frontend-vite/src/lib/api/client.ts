import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh']
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to every request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 — refresh once then redirect to login
apiClient.interceptors.response.use(
  res => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const isAuthEndpoint = AUTH_ENDPOINTS.some(path => original.url?.includes(path))
    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true
      try {
        const refresh_token = localStorage.getItem('refresh_token')
        if (!refresh_token) throw new Error('No refresh token')
        const { data } = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token })
        localStorage.setItem('access_token', data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(original)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        sessionStorage.setItem('redirect_after_login', window.location.pathname)
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(error)
  }
)