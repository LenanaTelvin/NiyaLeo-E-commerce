import { apiClient } from './client'

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: number
    email: string
    username: string
    role: 'admin' | 'seller' | 'customer'
  }
}

export const authApi = {
  register: (data: {
    email: string
    username: string
    password: string
    full_name?: string
  }) => apiClient.post<AuthTokens>('/auth/register', data).then(r => r.data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<AuthTokens>('/auth/login', data).then(r => r.data),

  logout: () =>
    apiClient.post('/auth/logout').then(r => r.data),

  refresh: (refresh_token: string) =>
    apiClient
      .post<{ access_token: string; token_type: string }>('/auth/refresh', { refresh_token })
      .then(r => r.data),
}