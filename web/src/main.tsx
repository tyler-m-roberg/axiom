import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeProvider'
import { AuthGate } from './auth/AuthGate'
import { AppShell } from './components/AppShell'
import { TestsList } from './routes/TestsList'
import { TestDetail } from './routes/TestDetail'
import { Dictionary } from './routes/Dictionary'
import { Admin } from './routes/Admin'
import { Audit } from './routes/Audit'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5000, refetchOnWindowFocus: false } },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthGate>
            <AppShell>
              <Routes>
                <Route path="/" element={<Navigate to="/tests" replace />} />
                <Route path="/tests" element={<TestsList />} />
                <Route path="/tests/:testId" element={<TestDetail />} />
                <Route path="/dictionary" element={<Dictionary />} />
                <Route path="/admin" element={<Admin />} />
                <Route path="/audit" element={<Audit />} />
              </Routes>
            </AppShell>
          </AuthGate>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
