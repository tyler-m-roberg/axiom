import { useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useMe } from '../auth/AuthGate'
import type { KeycloakGroup, KeycloakRole } from '../types/api'

export function Admin() {
  const me = useMe()
  const qc = useQueryClient()

  const groups = useQuery<KeycloakGroup[]>({
    queryKey: ['groups'],
    queryFn: () => api<KeycloakGroup[]>('/api/groups'),
  })
  const roles = useQuery<KeycloakRole[]>({
    queryKey: ['roles'],
    queryFn: () => api<KeycloakRole[]>('/api/roles'),
  })

  const [groupOpen, setGroupOpen] = useState(false)
  const [groupName, setGroupName] = useState('')
  const createGroup = useMutation({
    mutationFn: () =>
      api<KeycloakGroup>('/api/groups', {
        method: 'POST',
        body: JSON.stringify({ name: groupName }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['groups'] })
      setGroupOpen(false)
      setGroupName('')
    },
  })
  const deleteGroup = useMutation({
    mutationFn: (id: string) => api(`/api/groups/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['groups'] }),
  })

  const [roleOpen, setRoleOpen] = useState(false)
  const [roleName, setRoleName] = useState('')
  const [roleDesc, setRoleDesc] = useState('')
  const createRole = useMutation({
    mutationFn: () =>
      api<KeycloakRole>('/api/roles', {
        method: 'POST',
        body: JSON.stringify({ name: roleName, description: roleDesc }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['roles'] })
      setRoleOpen(false)
      setRoleName('')
      setRoleDesc('')
    },
  })
  const deleteRole = useMutation({
    mutationFn: (name: string) => api(`/api/roles/${encodeURIComponent(name)}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['roles'] }),
  })

  if (!me.is_admin) {
    return <Typography>Admin role required.</Typography>
  }

  return (
    <Stack spacing={3}>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h6">Groups</Typography>
          <Button variant="contained" onClick={() => setGroupOpen(true)}>
            New group
          </Button>
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Path</TableCell>
              <TableCell>ID</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {(groups.data ?? []).map((g) => (
              <TableRow key={g.id}>
                <TableCell>{g.name}</TableCell>
                <TableCell>{g.path}</TableCell>
                <TableCell><code>{g.id}</code></TableCell>
                <TableCell align="right">
                  <Button size="small" color="error" onClick={() => deleteGroup.mutate(g.id)}>
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h6">Realm roles</Typography>
          <Button variant="contained" onClick={() => setRoleOpen(true)}>
            New role
          </Button>
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {(roles.data ?? []).map((r) => (
              <TableRow key={r.id ?? r.name}>
                <TableCell>{r.name}</TableCell>
                <TableCell>{r.description}</TableCell>
                <TableCell align="right">
                  <Button size="small" color="error" onClick={() => deleteRole.mutate(r.name)}>
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={groupOpen} onClose={() => setGroupOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>New group</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            label="Name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            fullWidth
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGroupOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={!groupName} onClick={() => createGroup.mutate()}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={roleOpen} onClose={() => setRoleOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>New role</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Name" value={roleName} onChange={(e) => setRoleName(e.target.value)} />
            <TextField
              label="Description"
              value={roleDesc}
              onChange={(e) => setRoleDesc(e.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRoleOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={!roleName} onClick={() => createRole.mutate()}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
