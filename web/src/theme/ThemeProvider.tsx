import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { createTheme, CssBaseline, ThemeProvider as MuiThemeProvider } from '@mui/material'

type Mode = 'light' | 'dark'

interface ThemeCtx {
  mode: Mode
  toggle: () => void
  setMode: (m: Mode) => void
}

const STORAGE_KEY = 'axiom.themeMode'
const Ctx = createContext<ThemeCtx | null>(null)

function resolveInitialMode(): Mode {
  if (typeof window === 'undefined') return 'dark'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>(resolveInitialMode)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: mode === 'dark' ? '#7aa7ff' : '#1f4dde' },
          secondary: { main: '#b16cea' },
        },
        shape: { borderRadius: 8 },
      }),
    [mode],
  )

  const value = useMemo<ThemeCtx>(
    () => ({ mode, toggle: () => setMode((m) => (m === 'dark' ? 'light' : 'dark')), setMode }),
    [mode],
  )

  return (
    <Ctx.Provider value={value}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline enableColorScheme />
        {children}
      </MuiThemeProvider>
    </Ctx.Provider>
  )
}

export function useThemeMode(): ThemeCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useThemeMode must be used inside ThemeProvider')
  return ctx
}
