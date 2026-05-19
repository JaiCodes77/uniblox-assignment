import type {
  Cart,
  DiscountGenerateResult,
  Item,
  Order,
  Stats,
} from './types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  getItems: () => request<Item[]>('/items'),

  addToCart: (userId: string, itemId: number, quantity: number) =>
    request<Cart>('/cart/add', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, item_id: itemId, quantity }),
    }),

  getCart: (userId: string) => request<Cart>(`/cart/${encodeURIComponent(userId)}`),

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
