import { useMemo, useState } from 'react'
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
import type { Binding, KeycloakGroup, MetadataField, TestAcl } from '../types/api'

interface Props {
  testId: string
  bindings: Binding[]
  fields: MetadataField[]
}

export function TestSettings({ testId, bindings, fields }: Props) {
  const qc = useQueryClient()
  const fieldsById = useMemo(() => new Map(fields.map((f) => [f.id, f])), [fields])

  const groupsQuery = useQuery<KeycloakGroup[]>({
    queryKey: ['groups'],
    queryFn: () => api<KeycloakGroup[]>('/api/groups'),
  })
  const aclsQuery = useQuery<TestAcl[]>({
    queryKey: ['acls', testId],
    queryFn: () => api<TestAcl[]>(`/api/tests/${testId}/acls`),
  })

  const togglePromote = useMutation({
    mutationFn: ({ id, requirement }: { id: string; requirement: 'required' | 'optional' }) =>
      api(`/api/tests/${testId}/bindings/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ requirement }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bindings', testId] }),
  })

  const removeBinding = useMutation({
    mutationFn: (id: string) =>
      api(`/api/tests/${testId}/bindings/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bindings', testId] }),
  })

  const [addBindingOpen, setAddBindingOpen] = useState(false)
  const [pickField, setPickField] = useState('')
  const [pickRequired, setPickRequired] = useState<'required' | 'optional'>('optional')
  const addBinding = useMutation({
    mutationFn: () =>
      api(`/api/tests/${testId}/bindings`, {
        method: 'POST',
        body: JSON.stringify({
          field_id: pickField,
          requirement: pickRequired,
          applies_to: 'event',
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['bindings', testId] })
      setAddBindingOpen(false)
      setPickField('')
    },
  })

  const [aclGroup, setAclGroup] = useState('')
  const [aclPerm, setAclPerm] = useState<'read' | 'write' | 'admin'>('write')
  const addAcl = useMutation({
    mutationFn: () =>
      api(`/api/tests/${testId}/acls`, {
        method: 'POST',
        body: JSON.stringify({ group_id: aclGroup, permission: aclPerm }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acls', testId] })
      setAclGroup('')
    },
  })
  const deleteAcl = useMutation({
    mutationFn: (id: string) =>
      api(`/api/tests/${testId}/acls/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['acls', testId] }),
  })

  return (
    <Stack spacing={3}>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h6">Field bindings</Typography>
          <Button onClick={() => setAddBindingOpen(true)} variant="outlined">
            Bind existing field
          </Button>
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Field</TableCell>
              <TableCell>Namespace</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Requirement</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {bindings.map((b) => {
              const f = fieldsById.get(b.field_id)
              if (!f) return null
              return (
                <TableRow key={b.id}>
                  <TableCell>{f.label} ({f.key})</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={f.namespace_group_id ? f.namespace_group_id : 'shared'}
                      color={f.namespace_group_id ? 'primary' : 'default'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{f.data_type}</TableCell>
                  <TableCell>{f.status}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={() =>
                        togglePromote.mutate({
                          id: b.id,
                          requirement: b.requirement === 'required' ? 'optional' : 'required',
                        })
                      }
                    >
                      {b.requirement} → {b.requirement === 'required' ? 'optional' : 'required'}
                    </Button>
                  </TableCell>
                  <TableCell align="right">
                    <Button size="small" color="error" onClick={() => removeBinding.mutate(b.id)}>
                      Remove
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Access (groups)
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
          <TextField
            select
            label="Group"
            value={aclGroup}
            onChange={(e) => setAclGroup(e.target.value)}
            sx={{ minWidth: 200 }}
          >
            {(groupsQuery.data ?? []).map((g) => (
              <MenuItem key={g.id} value={g.id}>
                {g.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Permission"
            value={aclPerm}
            onChange={(e) => setAclPerm(e.target.value as any)}
          >
            <MenuItem value="read">read</MenuItem>
            <MenuItem value="write">write</MenuItem>
            <MenuItem value="admin">admin</MenuItem>
          </TextField>
          <Button variant="contained" disabled={!aclGroup} onClick={() => addAcl.mutate()}>
            Add ACL
          </Button>
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Group</TableCell>
              <TableCell>Permission</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {(aclsQuery.data ?? []).map((a) => (
              <TableRow key={a.id}>
                <TableCell>{a.group_id}</TableCell>
                <TableCell>{a.permission}</TableCell>
                <TableCell align="right">
                  <Button size="small" color="error" onClick={() => deleteAcl.mutate(a.id)}>
                    Remove
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={addBindingOpen} onClose={() => setAddBindingOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Bind existing field</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              select
              label="Field"
              value={pickField}
              onChange={(e) => setPickField(e.target.value)}
            >
              {fields.map((f) => (
                <MenuItem key={f.id} value={f.id}>
                  {f.label} ({f.key}) — {f.namespace_group_id ?? 'shared'}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Requirement"
              value={pickRequired}
              onChange={(e) => setPickRequired(e.target.value as any)}
            >
              <MenuItem value="optional">Optional</MenuItem>
              <MenuItem value="required">Required</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddBindingOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={!pickField} onClick={() => addBinding.mutate()}>
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
