import { useState } from 'react'
import { api } from '../api'
import { useAsyncData } from '../hooks/useAsyncData'
import type { Order } from '../types'

interface CartViewProps {
  userId: string
  refreshKey: number
  onCheckout: () => void
}

export function CartView({ userId, refreshKey, onCheckout }: CartViewProps) {
  const trimmedUser = userId.trim()
  const enabled = trimmedUser.length > 0

  const { data: cart, loading, error: loadError, reload } = useAsyncData(
    () => api.getCart(trimmedUser),
    [trimmedUser, refreshKey],
    enabled,
  )

  const [actionError, setActionError] = useState<string | null>(null)
  const [discountCode, setDiscountCode] = useState('')
  const [checkingOut, setCheckingOut] = useState(false)
  const [lastOrder, setLastOrder] = useState<Order | null>(null)

  const error = actionError ?? loadError

  const handleCheckout = async () => {
    if (!cart?.items.length) {
      setActionError('Your cart is empty.')
      return
    }

    setCheckingOut(true)
    setActionError(null)
    setLastOrder(null)
    try {
      const order = await api.checkout(trimmedUser, discountCode.trim() || undefined)
      setLastOrder(order)
      setDiscountCode('')
      onCheckout()
      reload()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Checkout failed')
    } finally {
      setCheckingOut(false)
    }
  }

  if (!enabled) {
    return (
      <section>
        <h2 className="section-title">Cart</h2>
        <div className="empty">
          <p>Enter a user ID in the header to view your cart.</p>
        </div>
      </section>
    )
  }

  if (loading) return <p className="loading">Loading cart…</p>

  const isEmpty = !cart?.items.length

  return (
    <section>
      <h2 className="section-title">Cart</h2>
      <p className="section-sub">Review items and complete checkout for {trimmedUser}.</p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="panel">
        {isEmpty ? (
          <div className="empty">
            <p>Your cart is empty.</p>
            <p>Head to the shop to add items.</p>
          </div>
        ) : (
          <>
            <div className="cart-lines">
              {cart!.items.map((line) => (
                <div key={line.item_id} className="cart-line">
                  <div className="cart-line-info">
                    <h4>{line.name}</h4>
                    <p>
                      {line.quantity} × ${line.unit_price.toFixed(2)}
                    </p>
                  </div>
                  <span className="cart-line-total">${line.line_total.toFixed(2)}</span>
                </div>
              ))}
            </div>

            <div className="cart-footer">
              <div className="subtotal-row">
                <span>Subtotal</span>
                <span>${cart!.subtotal.toFixed(2)}</span>
              </div>

              <div className="checkout-form">
                <label htmlFor="discount">Discount code (optional)</label>
                <input
                  id="discount"
                  type="text"
                  placeholder="Enter code"
                  value={discountCode}
                  onChange={(e) => setDiscountCode(e.target.value.toUpperCase())}
                />
                <button
                  type="button"
                  className="btn btn-primary btn-full"
                  disabled={checkingOut}
                  onClick={handleCheckout}
                >
                  {checkingOut ? 'Processing…' : 'Checkout'}
                </button>
              </div>
            </div>
          </>
        )}

        {lastOrder && (
          <div className="order-success">
            <h4>Order #{lastOrder.id} placed</h4>
            <dl>
              <dt>Subtotal</dt>
              <dd>${lastOrder.subtotal.toFixed(2)}</dd>
              {lastOrder.discount_amount > 0 && (
                <>
                  <dt>Discount ({lastOrder.discount_code})</dt>
                  <dd>−${lastOrder.discount_amount.toFixed(2)}</dd>
                </>
              )}
              <dt>Total</dt>
              <dd>${lastOrder.total.toFixed(2)}</dd>
            </dl>
          </div>
        )}
      </div>
    </section>
  )
}
