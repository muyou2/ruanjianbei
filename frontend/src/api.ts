const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: options?.body instanceof FormData
      ? options.headers
      : { 'Content-Type': 'application/json', ...(options?.headers || {}) },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || body.message || `请求失败：${response.status}`)
  }
  const body = await response.json()
  return body.data as T
}

export async function consumeSSE(
  path: string,
  body: unknown,
  onEvent: (event: string, data: any) => void,
) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok || !response.body) throw new Error('流式请求启动失败')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      let event = 'message'
      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (data) onEvent(event, JSON.parse(data))
    }
    if (done) break
  }
}
