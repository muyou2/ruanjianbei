import { describe, expect, it, vi } from 'vitest'
import { api } from './api'

describe('api client', () => {
  it('unwraps the unified response data', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({ success: true, data: { status: 'healthy' } }),
    })))
    await expect(api('/api/health')).resolves.toEqual({ status: 'healthy' })
    vi.unstubAllGlobals()
  })
})
