import { useCallback, useState } from 'react'
import { api } from '../api'
import { useAsyncData } from '../hooks/useAsyncData'
import type { Item } from '../types'

interface CatalogProps {
  userId: string
  onCartChange: () => void
}

export function Catalog({ userId, onCartChange }: CatalogProps) {
  const { data: items, loading, error: loadError } = useAsyncData(
    () => api.getItems(),
    [],
  )
  const [actionError, setActionError] = useState<string | null>(null)
  const [quantities, setQuantities] = useState<Record<number, string>>({})
  const [adding, setAdding] = useState<number | null>(null)

  const trimmedUser = userId.trim()
  const error = actionError ?? loadError

  const getQty = (itemId: number) => quantities[itemId] ?? '1'

  const addToCart = useCallback(
    async (item: Item) => {
      if (!trimmedUser) {
        setActionError('Enter a user ID in the header before adding items.')
        return
      }

      const parsed = parseInt(quantities[item.id] ?? '1', 10)
      if (!Number.isFinite(parsed) || parsed < 1) {
        setActionError('Quantity must be at least 1.')
        return
      }

      setAdding(item.id)
      setActionError(null)
      try {
        await api.addToCart(trimmedUser, item.id, parsed)
        onCartChange()
      } catch (e) {
        setActionError(e instanceof Error ? e.message : 'Failed to add item')
      } finally {
        setAdding(null)
      }
    },
    [trimmedUser, quantities, onCartChange],
  )

  if (loading) return <p className="loading">Loading catalog…</p>

  if (!items?.length) {
    return (
      <section>
        <h2 className="section-title">Shop</h2>
        <div className="empty">
          <p>No items available.</p>
        </div>
      </section>
    )
  }

  return (
    <section>
      <h2 className="section-title">Shop</h2>
      <p className="section-sub">Browse items and add them to your cart.</p>

      {!trimmedUser && (
        <div className="alert alert-info">Enter a user ID in the header to add items.</div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      <div className="grid">
        {items.map((item) => (
          <article key={item.id} className="card">
            <h3>{item.name}</h3>
            <p className="price">${item.price.toFixed(2)}</p>
            <div className="card-actions">
              <input
                type="number"
                min={1}
                className="qty-input"
                value={getQty(item.id)}
                onChange={(e) =>
                  setQuantities((q) => ({ ...q, [item.id]: e.target.value }))
                }
                onBlur={() =>
                  setQuantities((q) => {
                    const parsed = parseInt(q[item.id] ?? '1', 10)
                    return {
                      ...q,
                      [item.id]: String(Number.isFinite(parsed) && parsed >= 1 ? parsed : 1),
                    }
                  })
                }
                aria-label={`Quantity for ${item.name}`}
              />
              <button
                type="button"
                className="btn btn-primary"
                disabled={adding === item.id || !trimmedUser}
                onClick={() => addToCart(item)}
              >
                {adding === item.id ? 'Adding…' : 'Add'}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
