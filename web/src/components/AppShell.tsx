import { type ReactNode } from 'react'
import {
  AppBar,
  Box,
  Button,
  Container,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material'
import DarkModeIcon from '@mui/icons-material/DarkMode'
import LightModeIcon from '@mui/icons-material/LightMode'
import LogoutIcon from '@mui/icons-material/Logout'
import { Link as RouterLink, NavLink } from 'react-router-dom'
import { useThemeMode } from '../theme/ThemeProvider'
import { useMe } from '../auth/AuthGate'
import { logout } from '../api/client'

const navItems = [
  { to: '/tests', label: 'Tests' },
  { to: '/dictionary', label: 'Dictionary' },
  { to: '/admin', label: 'Admin' },
  { to: '/audit', label: 'Audit' },
]

export function AppShell({ children }: { children: ReactNode }) {
  const { mode, toggle } = useThemeMode()
  const me = useMe()
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="sticky" color="default" elevation={1}>
        <Toolbar>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/tests"
            sx={{ color: 'inherit', textDecoration: 'none', fontWeight: 700, mr: 4 }}
          >
            axiom
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexGrow: 1 }}>
            {navItems.map((n) => (
              <Button
                key={n.to}
                component={NavLink}
                to={n.to}
                color="inherit"
                sx={{ '&.active': { fontWeight: 700 } }}
              >
                {n.label}
              </Button>
            ))}
          </Stack>
          <Typography variant="body2" sx={{ mr: 2, opacity: 0.7 }}>
            {me.username}
            {me.is_admin ? ' (admin)' : ''}
          </Typography>
          <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
            <IconButton onClick={toggle} color="inherit">
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Log out">
            <IconButton onClick={() => logout()} color="inherit">
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Container maxWidth={false} sx={{ py: 3, flexGrow: 1 }}>
        {children}
      </Container>
    </Box>
  )
}
