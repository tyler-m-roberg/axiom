import { createContext, useContext, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Box, CircularProgress, Typography } from '@mui/material'
import { api, ApiError, loginRedirect } from '../api/client'
import type { MeResponse } from '../types/api'

const Ctx = createContext<MeResponse | null>(null)

export function AuthGate({ children }: { children: ReactNode }) {
  const { data, isLoading, error } = useQuery<MeResponse>({
    queryKey: ['me'],
    queryFn: () => api<MeResponse>('/api/auth/me'),
    retry: false,
  })

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }
  if (error) {
    if (error instanceof ApiError && error.status === 401) {
      loginRedirect()
      return null
    }
    return (
      <Box sx={{ p: 4 }}>
        <Typography color="error">Failed to load session: {String(error)}</Typography>
      </Box>
    )
  }
  if (!data) return null
  return <Ctx.Provider value={data}>{children}</Ctx.Provider>
}

export function useMe(): MeResponse {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useMe must be used inside AuthGate')
  return ctx
}
