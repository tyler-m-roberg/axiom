import { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Button,
  Divider,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Binding, Event, MetadataField } from '../types/api'

interface Props {
  testId: string
  events: Event[]
  bindings: Binding[]
  fields: MetadataField[]
}

function groupBindingsByNamespace(
  bindings: Binding[],
  fieldsById: Map<string, MetadataField>,
): Map<string, { binding: Binding; field: MetadataField }[]> {
  const groups = new Map<string, { binding: Binding; field: MetadataField }[]>()
  for (const b of bindings) {
    const f = fieldsById.get(b.field_id)
    if (!f) continue
    const key = f.namespace_group_id ?? '__shared__'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push({ binding: b, field: f })
  }
  return groups
}

export function EventForm({ testId, events, bindings, fields }: Props) {
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState(events[0]?.id ?? '')
  const event = events.find((e) => e.id === selectedId)
  const fieldsById = useMemo(() => new Map(fields.map((f) => [f.id, f])), [fields])
  const grouped = useMemo(
    () => groupBindingsByNamespace(bindings.filter((b) => b.applies_to === 'event'), fieldsById),
    [bindings, fieldsById],
  )

  const [draft, setDraft] = useState<Record<string, unknown>>(event?.metadata ?? {})
  const [name, setName] = useState(event?.name ?? '')

  useEffect(() => {
    setDraft(event?.metadata ?? {})
    setName(event?.name ?? '')
  }, [event?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const save = useMutation({
    mutationFn: () =>
      api<Event>(`/api/events/${selectedId}`, {
        method: 'PATCH',
        body: JSON.stringify({ name, metadata: draft, on_the_fly: [] }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events', testId] }),
  })

  if (!event) return <Typography>No events yet. Add one in the Grid tab.</Typography>

  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
      <Paper sx={{ p: 1, minWidth: 200 }}>
        <Typography variant="overline">Events</Typography>
        <Stack>
          {events.map((e) => (
            <Button
              key={e.id}
              variant={e.id === selectedId ? 'contained' : 'text'}
              onClick={() => setSelectedId(e.id)}
              sx={{ justifyContent: 'flex-start' }}
            >
              {e.name || '(unnamed)'}
            </Button>
          ))}
        </Stack>
      </Paper>
      <Paper sx={{ p: 2, flexGrow: 1 }}>
        <TextField
          label="Event name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          sx={{ mb: 2 }}
        />
        {Array.from(grouped.entries()).map(([ns, entries]) => (
          <Box key={ns} sx={{ mb: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              {ns === '__shared__' ? 'Shared' : `Namespace: ${ns}`}
            </Typography>
            <Divider sx={{ mb: 1 }} />
            <Stack spacing={2}>
              {entries.map(({ binding, field }) => (
                <FieldInput
                  key={field.id}
                  field={field}
                  required={binding.requirement === 'required'}
                  value={draft[field.id]}
                  onChange={(v) => setDraft((d) => ({ ...d, [field.id]: v }))}
                />
              ))}
            </Stack>
          </Box>
        ))}
        <Button variant="contained" onClick={() => save.mutate()} disabled={save.isPending}>
          Save
        </Button>
      </Paper>
    </Stack>
  )
}

function FieldInput({
  field,
  required,
  value,
  onChange,
}: {
  field: MetadataField
  required: boolean
  value: unknown
  onChange: (v: unknown) => void
}) {
  const label = `${field.label}${required ? ' *' : ''}`
  if (field.data_type === 'bool') {
    return (
      <TextField
        select
        label={label}
        value={value === true ? 'true' : value === false ? 'false' : ''}
        onChange={(e) => onChange(e.target.value === 'true')}
        fullWidth
      >
        <MenuItem value="">(unset)</MenuItem>
        <MenuItem value="true">true</MenuItem>
        <MenuItem value="false">false</MenuItem>
      </TextField>
    )
  }
  if (field.data_type === 'enum' && field.enum_values) {
    return (
      <TextField
        select
        label={label}
        value={(value as string) ?? ''}
        onChange={(e) => onChange(e.target.value)}
        fullWidth
      >
        {field.enum_values.map((v) => (
          <MenuItem key={v} value={v}>
            {v}
          </MenuItem>
        ))}
      </TextField>
    )
  }
  return (
    <TextField
      label={label}
      type={field.data_type === 'number' ? 'number' : field.data_type === 'date' ? 'date' : 'text'}
      InputLabelProps={field.data_type === 'date' ? { shrink: true } : undefined}
      value={(value as string | number | undefined) ?? ''}
      onChange={(e) =>
        onChange(field.data_type === 'number' ? Number(e.target.value) : e.target.value)
      }
      fullWidth
    />
  )
}
