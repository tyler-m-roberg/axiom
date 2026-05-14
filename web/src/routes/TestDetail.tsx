import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Box, Tab, Tabs, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Binding, Event, MetadataField, Test } from '../types/api'
import { EventGrid } from './EventGrid'
import { EventForm } from './EventForm'
import { TestSettings } from './TestSettings'

export function TestDetail() {
  const { testId = '' } = useParams<{ testId: string }>()
  const [tab, setTab] = useState(0)

  const testQuery = useQuery<Test>({
    queryKey: ['test', testId],
    queryFn: () => api<Test>(`/api/tests/${testId}`),
  })
  const eventsQuery = useQuery<Event[]>({
    queryKey: ['events', testId],
    queryFn: () => api<Event[]>(`/api/tests/${testId}/events`),
  })
  const bindingsQuery = useQuery<Binding[]>({
    queryKey: ['bindings', testId],
    queryFn: () => api<Binding[]>(`/api/tests/${testId}/bindings`),
  })
  const fieldsQuery = useQuery<MetadataField[]>({
    queryKey: ['fields'],
    queryFn: () => api<MetadataField[]>('/api/metadata-fields'),
  })

  if (testQuery.isLoading) return <Typography>Loading…</Typography>
  if (!testQuery.data) return <Typography>Test not found.</Typography>

  const events = eventsQuery.data ?? []
  const bindings = bindingsQuery.data ?? []
  const fields = fieldsQuery.data ?? []

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {testQuery.data.name}
      </Typography>
      {testQuery.data.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {testQuery.data.description}
        </Typography>
      )}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Grid (spreadsheet)" />
        <Tab label="Form" />
        <Tab label="Settings" />
      </Tabs>
      {tab === 0 && (
        <EventGrid testId={testId} events={events} bindings={bindings} fields={fields} />
      )}
      {tab === 1 && (
        <EventForm testId={testId} events={events} bindings={bindings} fields={fields} />
      )}
      {tab === 2 && <TestSettings testId={testId} bindings={bindings} fields={fields} />}
    </Box>
  )
}
