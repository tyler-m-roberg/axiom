import { useState } from 'react'
import {
  Box,
  Chip,
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
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { AuditEntry } from '../types/api'

const entityTypes = [
  'all',
  'test',
  'event',
  'metadata_field',
  'test_field_binding',
  'test_acl',
] as const

export function Audit() {
  const [entityType, setEntityType] = useState<string>('all')
  const [actor, setActor] = useState('')

  const params = new URLSearchParams()
  if (entityType !== 'all') params.set('entity_type', entityType)
  if (actor) params.set('actor', actor)

  const { data = [], isLoading } = useQuery<AuditEntry[]>({
    queryKey: ['audit', entityType, actor],
    queryFn: () => api<AuditEntry[]>(`/api/audit?${params.toString()}`),
  })

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Audit log
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField
          select
          size="small"
          label="Entity"
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          sx={{ minWidth: 200 }}
        >
          {entityTypes.map((t) => (
            <MenuItem key={t} value={t}>
              {t}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          size="small"
          label="Actor (username)"
          value={actor}
          onChange={(e) => setActor(e.target.value)}
        />
      </Stack>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>When</TableCell>
              <TableCell>Actor</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Entity</TableCell>
              <TableCell>Diff</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5}>Loading…</TableCell>
              </TableRow>
            ) : (
              data.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{new Date(row.at).toLocaleString()}</TableCell>
                  <TableCell>{row.actor_username ?? row.actor_sub}</TableCell>
                  <TableCell>
                    <Chip size="small" label={row.action} />
                  </TableCell>
                  <TableCell>
                    {row.entity_type} · <code>{row.entity_id.slice(0, 8)}…</code>
                  </TableCell>
                  <TableCell sx={{ maxWidth: 480 }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12 }}>
                      {JSON.stringify(row.diff ?? row.after ?? row.before ?? {}, null, 2)}
                    </pre>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  )
}
