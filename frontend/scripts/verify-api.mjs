/**
 * Smoke test for frontend API flows against a running backend.
 * Run: node scripts/verify-api.mjs
 * Requires backend at http://localhost:8000
 */

const BASE = 'http://localhost:8000'

async function request(path, init) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  const text = await res.text()
  let body
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }
  if (!res.ok) {
    throw new Error(`${res.status} ${path}: ${JSON.stringify(body?.detail ?? body)}`)
  }
  return body
}

async function getCart(userId) {
  try {
    return await request(`/cart/${encodeURIComponent(userId)}`)
  } catch (e) {
    if (String(e.message).startsWith('404')) {
      return { user_id: userId, items: [], subtotal: 0 }
    }
    throw e
  }
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg)
}

async function main() {
  const uid = `test-${Date.now()}`

  console.log('1. Health check')
  const health = await request('/health')
  assert(health.status === 'ok', 'health failed')

  console.log('2. List items')
  const items = await request('/items')
  assert(items.length >= 1, 'expected catalog items')

  console.log('3. Empty cart for new user')
  const empty = await getCart(uid)
  assert(empty.items.length === 0, 'expected empty cart')

  console.log('4. Add to cart')
  await request('/cart/add', {
    method: 'POST',
    body: JSON.stringify({ user_id: uid, item_id: items[0].id, quantity: 2 }),
  })
  const cart = await getCart(uid)
  assert(cart.items.length === 1, 'expected one cart line')
  assert(cart.subtotal > 0, 'expected positive subtotal')

  console.log('5. Checkout')
  const order = await request('/checkout', {
    method: 'POST',
    body: JSON.stringify({ user_id: uid }),
  })
  assert(order.total > 0, 'expected order total')
  assert(order.id > 0, 'expected order id')

  console.log('6. Cart cleared after checkout')
  const after = await getCart(uid)
  assert(after.items.length === 0, 'expected empty cart after checkout')

  console.log('7. Admin stats')
  const stats = await request('/admin/stats')
  assert(typeof stats.total_revenue === 'number', 'expected stats')

  console.log('8. Discount generate (may be ineligible)')
  const discount = await request('/admin/discount/generate', { method: 'POST' })
  assert(typeof discount.eligible === 'boolean', 'expected eligible flag')

  console.log('\nAll checks passed.')
}

main().catch((e) => {
  console.error('\nVerification failed:', e.message)
  process.exit(1)
})
