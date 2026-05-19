import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { Cart, Order } from '../types'

interface CartViewProps {
  userId: string
  refreshKey: number
  onCheckout: () => void
}

export function CartView({ userId, refreshKey, onCheckout }: CartViewProps) {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [discountCode, setDiscountCode] = useState('')
  const [checkingOut, setCheckingOut] = useState(false)
  const [lastOrder, setLastOrder] = useState<Order | null>(null)

  const loadCart = useCallback(() => {
    if (!userId.trim()) {
      setCart(null)
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    api
      .getCart(userId)
      .then(setCart)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [userId])

  useEffect(() => {
    loadCart()
  }, [loadCart, refreshKey])

  const handleCheckout = async () => {
    setCheckingOut(true)
    setError(null)
    setLastOrder(null)
    try {
      const order = await api.checkout(userId, discountCode.trim() || undefined)
      setLastOrder(order)
      setDiscountCode('')
      onCheckout()
      loadCart()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Checkout failed')
    } finally {
      setCheckingOut(false)
    }
  }

  if (!userId.trim()) {
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
      <p className="section-sub">Review items and complete checkout for {userId}.</p>

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
