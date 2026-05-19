import type {
  Cart,
  DiscountGenerateResult,
  Item,
  Order,
  Stats,
} from './types'

const BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function formatDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((entry) => {
        if (typeof entry === 'object' && entry !== null && 'msg' in entry) {
          const loc = 'loc' in entry && Array.isArray(entry.loc) ? entry.loc.join('.') : ''
          return loc ? `${loc}: ${String(entry.msg)}` : String(entry.msg)
        }
        return JSON.stringify(entry)
      })
      .join('; ')
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return 'Request failed'
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })

  if (!res.ok) {
    let detail: unknown = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      /* ignore */
    }
    throw new ApiError(formatDetail(detail), res.status)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const emptyCart = (userId: string): Cart => ({
  user_id: userId,
  items: [],
  subtotal: 0,
})

export const api = {
  health: () => request<{ status: string }>('/health'),

  getItems: () => request<Item[]>('/items'),

  addToCart: (userId: string, itemId: number, quantity: number) =>
    request<Cart>('/cart/add', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, item_id: itemId, quantity }),
    }),

  getCart: async (userId: string): Promise<Cart> => {
    try {
      return await request<Cart>(`/cart/${encodeURIComponent(userId)}`)
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        return emptyCart(userId)
      }
      throw e
    }
  },

  checkout: (userId: string, discountCode?: string) =>
    request<Order>('/checkout', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        discount_code: discountCode || null,
      }),
    }),

  generateDiscount: () =>
    request<DiscountGenerateResult>('/admin/discount/generate', {
      method: 'POST',
    }),

  getStats: () => request<Stats>('/admin/stats'),
}
