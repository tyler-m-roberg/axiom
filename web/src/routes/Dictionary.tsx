import { useState } from 'react'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
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
import type { FieldStatus, MetadataField } from '../types/api'

export function Dictionary() {
  const qc = useQueryClient()
  const me = useMe()
  const [statusFilter, setStatusFilter] = useState<FieldStatus | 'all'>('all')
  const [nsFilter, setNsFilter] = useState<string>('all')

  const { data = [] } = useQuery<MetadataField[]>({
    queryKey: ['fields'],
    queryFn: () => api<MetadataField[]>('/api/metadata-fields'),
  })

  const filtered = data.filter((f) => {
    if (statusFilter !== 'all' && f.status !== statusFilter) return false
    if (nsFilter === 'shared' && f.namespace_group_id !== null) return false
    if (nsFilter !== 'all' && nsFilter !== 'shared' && f.namespace_group_id !== nsFilter) return false
    return true
  })

  const promote = useMutation({
    mutationFn: (id: string) =>
      api(`/api/metadata-fields/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'established' }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['fields'] }),
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [key, setKey] = useState('')
  const [label, setLabel] = useState('')
  const [dtype, setDtype] = useState<'string' | 'number' | 'bool' | 'date'>('string')
  const [ns, setNs] = useState('')

  const createField = useMutation({
    mutationFn: () =>
      api<MetadataField>('/api/metadata-fields', {
        method: 'POST',
        body: JSON.stringify({
          key,
          label: label || key,
          data_type: dtype,
          scope: 'event',
          status: 'established',
          namespace_group_id: ns || null,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fields'] })
      setCreateOpen(false)
      setKey('')
      setLabel('')
      setNs('')
    },
  })

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h5">Data dictionary</Typography>
        <Button variant="contained" onClick={() => setCreateOpen(true)}>
          New field
        </Button>
      </Stack>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField
          select
          size="small"
          label="Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as any)}
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="all">All</MenuItem>
          <MenuItem value="established">Established</MenuItem>
          <MenuItem value="on_the_fly">On-the-fly</MenuItem>
        </TextField>
        <TextField
          select
          size="small"
          label="Namespace"
          value={nsFilter}
          onChange={(e) => setNsFilter(e.target.value)}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All</MenuItem>
          <MenuItem value="shared">Shared only</MenuItem>
          {me.groups.map((g) => (
            <MenuItem key={g} value={g}>
              {g}
            </MenuItem>
          ))}
        </TextField>
      </Stack>
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Key</TableCell>
              <TableCell>Label</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Scope</TableCell>
              <TableCell>Namespace</TableCell>
              <TableCell>Status</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((f) => (
              <TableRow key={f.id}>
                <TableCell>{f.key}</TableCell>
                <TableCell>{f.label}</TableCell>
                <TableCell>{f.data_type}</TableCell>
                <TableCell>{f.scope}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={f.namespace_group_id ?? 'shared'}
                    color={f.namespace_group_id ? 'primary' : 'default'}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={f.status}
                    color={f.status === 'established' ? 'success' : 'warning'}
                  />
                </TableCell>
                <TableCell align="right">
                  {f.status === 'on_the_fly' && (
                    <Button size="small" onClick={() => promote.mutate(f.id)}>
                      Promote
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>New metadata field</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Key (slug)" value={key} onChange={(e) => setKey(e.target.value)} />
            <TextField label="Label" value={label} onChange={(e) => setLabel(e.target.value)} />
            <TextField select label="Type" value={dtype} onChange={(e) => setDtype(e.target.value as any)}>
              <MenuItem value="string">String</MenuItem>
              <MenuItem value="number">Number</MenuItem>
              <MenuItem value="bool">Boolean</MenuItem>
              <MenuItem value="date">Date</MenuItem>
            </TextField>
            <TextField
              select
              label="Namespace"
              value={ns}
              onChange={(e) => setNs(e.target.value)}
            >
              <MenuItem value="">Shared</MenuItem>
              {me.groups.map((g) => (
                <MenuItem key={g} value={g}>
                  {g}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={!key} onClick={() => createField.mutate()}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
