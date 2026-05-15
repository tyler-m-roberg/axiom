const API_BASE = ''

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly body: unknown) {
    super(typeof body === 'object' && body && 'detail' in body ? String((body as any).detail) : `HTTP ${status}`)
  }
}

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
    ...init,
  })
  if (resp.status === 204) return undefined as T
  const text = await resp.text()
  const body = text ? JSON.parse(text) : undefined
  if (!resp.ok) throw new ApiError(resp.status, body)
  return body as T
}

export function loginRedirect(returnTo?: string): void {
  const to = returnTo || window.location.pathname + window.location.search
  window.location.href = `/api/auth/login?return_to=${encodeURIComponent(window.location.origin + to)}`
}

export async function logout(): Promise<void> {
  const resp = await api<{ logout_url: string }>('/api/auth/logout', { method: 'POST' })
  if (resp?.logout_url) window.location.href = resp.logout_url
  else window.location.href = '/'
}
