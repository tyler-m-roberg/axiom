export interface MeResponse {
  sub: string
  username: string
  email: string | null
  groups: string[]
  roles: string[]
  is_admin: boolean
}

export type FieldDataType = 'string' | 'number' | 'bool' | 'date' | 'enum'
export type FieldScope = 'test' | 'event' | 'both'
export type FieldStatus = 'established' | 'on_the_fly'
export type BindingRequirement = 'required' | 'optional'
export type BindingApplies = 'test' | 'event'
export type AclPermission = 'read' | 'write' | 'admin'

export interface MetadataField {
  id: string
  key: string
  label: string
  description: string | null
  data_type: FieldDataType
  enum_values: string[] | null
  scope: FieldScope
  status: FieldStatus
  namespace_group_id: string | null
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface Test {
  id: string
  name: string
  description: string | null
  metadata: Record<string, unknown>
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface Event {
  id: string
  test_id: string
  name: string | null
  occurred_at: string | null
  metadata: Record<string, unknown>
  on_the_fly_field_ids: string[]
  created_at: string
  created_by: string | null
  updated_at: string
  updated_by: string | null
}

export interface Binding {
  id: string
  test_id: string
  field_id: string
  requirement: BindingRequirement
  applies_to: BindingApplies
  created_at: string
  updated_at: string
}

export interface TestAcl {
  id: string
  test_id: string
  group_id: string
  permission: AclPermission
  created_at: string
}

export interface KeycloakGroup {
  id: string
  name: string
  path: string
  subGroups?: KeycloakGroup[]
}

export interface KeycloakRole {
  id: string
  name: string
  description?: string
}

export interface AuditEntry {
  id: string
  entity_type: string
  entity_id: string
  action: 'create' | 'update' | 'delete' | 'promote'
  actor_sub: string | null
  actor_username: string | null
  at: string
  before: Record<string, unknown> | null
  after: Record<string, unknown> | null
  diff: Record<string, unknown> | null
  context: Record<string, unknown> | null
}
