import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { Item } from '../types'

interface CatalogProps {
  userId: string
  onCartChange: () => void
}

export function Catalog({ userId, onCartChange }: CatalogProps) {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [quantities, setQuantities] = useState<Record<number, number>>({})
  const [adding, setAdding] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .getItems()
      .then((data) => {
        setItems(data)
        setQuantities(Object.fromEntries(data.map((i) => [i.id, 1])))
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const addToCart = useCallback(
    async (item: Item) => {
      const qty = quantities[item.id] ?? 1
      setAdding(item.id)
      setError(null)
      try {
        await api.addToCart(userId, item.id, qty)
        onCartChange()
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to add item')
      } finally {
        setAdding(null)
      }
    },
    [userId, quantities, onCartChange],
  )

  if (loading) return <p className="loading">Loading catalog…</p>

  return (
    <section>
      <h2 className="section-title">Shop</h2>
      <p className="section-sub">Browse items and add them to your cart.</p>

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
                value={quantities[item.id] ?? 1}
                onChange={(e) =>
                  setQuantities((q) => ({
                    ...q,
                    [item.id]: Math.max(1, parseInt(e.target.value, 10) || 1),
                  }))
                }
                aria-label={`Quantity for ${item.name}`}
              />
              <button
                type="button"
                className="btn btn-primary"
                disabled={adding === item.id}
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
