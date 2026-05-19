import { useState } from 'react'
import { api } from '../api'
import { useAsyncData } from '../hooks/useAsyncData'
import type { DiscountGenerateResult } from '../types'

export function AdminPanel() {
  const { data: stats, loading, error: loadError, reload } = useAsyncData(
    () => api.getStats(),
    [],
  )

  const [actionError, setActionError] = useState<string | null>(null)
  const [discountResult, setDiscountResult] = useState<DiscountGenerateResult | null>(null)
  const [generating, setGenerating] = useState(false)

  const error = actionError ?? loadError

  const handleGenerate = async () => {
    setGenerating(true)
    setActionError(null)
    setDiscountResult(null)
    try {
      const result = await api.generateDiscount()
      setDiscountResult(result)
      reload()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Failed to generate code')
    } finally {
      setGenerating(false)
    }
  }

  const formatMoney = (n: number) =>
    n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <section>
      <h2 className="section-title">Admin</h2>
      <p className="section-sub">
        Generate discount codes on every Nth order and view store statistics.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="admin-actions">
        <button
          type="button"
          className="btn btn-primary"
          disabled={generating}
          onClick={handleGenerate}
        >
          {generating ? 'Generating…' : 'Generate discount code'}
        </button>
        <button type="button" className="btn btn-secondary" onClick={reload}>
          Refresh stats
        </button>
      </div>

      {discountResult && (
        <div
          className={`alert ${discountResult.eligible ? 'alert-success' : 'alert-info'}`}
        >
          {discountResult.eligible ? (
            <>
              Code minted:{' '}
              <span className="discount-code">{discountResult.code}</span> ({discountResult.percent}
              % off)
            </>
          ) : (
            <>Not eligible: {discountResult.reason}</>
          )}
        </div>
      )}

      {loading ? (
        <p className="loading">Loading stats…</p>
      ) : stats ? (
        <div className="stats-grid">
          <div className="stat-card">
            <p>Items purchased</p>
            <strong>{stats.items_purchased}</strong>
          </div>
          <div className="stat-card">
            <p>Total revenue</p>
            <strong>${formatMoney(stats.total_revenue)}</strong>
          </div>
          <div className="stat-card">
            <p>Codes issued</p>
            <strong>{stats.discount_codes_issued}</strong>
          </div>
          <div className="stat-card">
            <p>Total discounts</p>
            <strong>${formatMoney(stats.total_discount_amount)}</strong>
          </div>
        </div>
      ) : null}
    </section>
  )
}
