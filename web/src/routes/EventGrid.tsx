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
  Stack,
  TextField,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import ViewColumnIcon from '@mui/icons-material/ViewColumn'
import {
  DataGrid,
  GridColDef,
  GridRowModel,
  GridRowsProp,
} from '@mui/x-data-grid'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useMe } from '../auth/AuthGate'
import type { Binding, Event, MetadataField } from '../types/api'

interface Props {
  testId: string
  events: Event[]
  bindings: Binding[]
  fields: MetadataField[]
}

function namespaceLabel(field: MetadataField | undefined): string {
  if (!field) return 'unknown'
  return field.namespace_group_id ? `ns:${field.namespace_group_id}` : 'shared'
}

export function EventGrid({ testId, events, bindings, fields }: Props) {
  const qc = useQueryClient()
  const me = useMe()
  const fieldsById = useMemo(() => new Map(fields.map((f) => [f.id, f])), [fields])

  const eventBindings = bindings.filter((b) => b.applies_to === 'event')
  const boundFields = eventBindings
    .map((b) => fieldsById.get(b.field_id))
    .filter((f): f is MetadataField => Boolean(f))

  const columns: GridColDef[] = useMemo(() => {
    const cols: GridColDef[] = [
      { field: 'name', headerName: 'Event name', width: 180, editable: true },
    ]
    for (const f of boundFields) {
      const binding = eventBindings.find((b) => b.field_id === f.id)
      const required = binding?.requirement === 'required'
      cols.push({
        field: f.id,
        headerName: `${f.label}${required ? ' *' : ''}`,
        description: `${f.key} · ${namespaceLabel(f)}`,
        width: 160,
        editable: true,
      })
    }
    return cols
  }, [boundFields, eventBindings])

  const rows: GridRowsProp = events.map((ev) => {
    const row: Record<string, unknown> = { id: ev.id, name: ev.name ?? '' }
    for (const [fid, value] of Object.entries(ev.metadata)) {
      row[fid] = value
    }
    return row
  })

  const updateEvent = useMutation({
    mutationFn: ({ id, body }: { id: string; body: any }) =>
      api<Event>(`/api/events/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events', testId] }),
  })

  const createEvent = useMutation({
    mutationFn: () =>
      api<Event>(`/api/tests/${testId}/events`, {
        method: 'POST',
        body: JSON.stringify({ name: 'New event', metadata: {}, on_the_fly: [] }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events', testId] }),
  })

  const processRowUpdate = async (newRow: GridRowModel, oldRow: GridRowModel) => {
    const metadata: Record<string, unknown> = {}
    for (const f of boundFields) {
      if (newRow[f.id] !== undefined) metadata[f.id] = newRow[f.id]
    }
    await updateEvent.mutateAsync({
      id: newRow.id as string,
      body: { name: newRow.name, metadata, on_the_fly: [] },
    })
    return newRow
  }

  const [addColOpen, setAddColOpen] = useState(false)
  const [newKey, setNewKey] = useState('')
  const [newLabel, setNewLabel] = useState('')
  const [newType, setNewType] = useState<'string' | 'number' | 'bool' | 'date'>('string')
  const [newNs, setNewNs] = useState<string>('')

  const addColumn = useMutation({
    mutationFn: async () => {
      const field = await api<MetadataField>('/api/metadata-fields', {
        method: 'POST',
        body: JSON.stringify({
          key: newKey,
          label: newLabel || newKey,
          data_type: newType,
          scope: 'event',
          status: 'on_the_fly',
          namespace_group_id: newNs || null,
        }),
      })
      await api(`/api/tests/${testId}/bindings`, {
        method: 'POST',
        body: JSON.stringify({
          field_id: field.id,
          requirement: 'optional',
          applies_to: 'event',
        }),
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['bindings', testId] })
      qc.invalidateQueries({ queryKey: ['fields'] })
      setAddColOpen(false)
      setNewKey('')
      setNewLabel('')
      setNewNs('')
      setNewType('string')
    },
  })

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
        <Button startIcon={<AddIcon />} onClick={() => createEvent.mutate()} variant="outlined">
          Add row
        </Button>
        <Button startIcon={<ViewColumnIcon />} onClick={() => setAddColOpen(true)} variant="outlined">
          Add column
        </Button>
        <Stack direction="row" spacing={0.5} sx={{ ml: 'auto', alignItems: 'center' }}>
          <Chip label="shared" size="small" />
          {me.groups.map((g) => (
            <Chip key={g} label={`ns:${g}`} size="small" color="primary" variant="outlined" />
          ))}
        </Stack>
      </Stack>
      <DataGrid
        autoHeight
        rows={rows}
        columns={columns}
        processRowUpdate={processRowUpdate}
        disableRowSelectionOnClick
        getRowClassName={() => ''}
      />

      <Dialog open={addColOpen} onClose={() => setAddColOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Add column (on-the-fly field)</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Key (slug)" value={newKey} onChange={(e) => setNewKey(e.target.value)} />
            <TextField label="Label" value={newLabel} onChange={(e) => setNewLabel(e.target.value)} />
            <TextField
              select
              label="Type"
              value={newType}
              onChange={(e) => setNewType(e.target.value as any)}
            >
              <MenuItem value="string">String</MenuItem>
              <MenuItem value="number">Number</MenuItem>
              <MenuItem value="bool">Boolean</MenuItem>
              <MenuItem value="date">Date</MenuItem>
            </TextField>
            <TextField
              select
              label="Namespace"
              value={newNs}
              onChange={(e) => setNewNs(e.target.value)}
              helperText="Shared = visible to everyone with test access. Namespaced = only your group sees the values."
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
          <Button onClick={() => setAddColOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!newKey || addColumn.isPending}
            onClick={() => addColumn.mutate()}
          >
            Add column
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
