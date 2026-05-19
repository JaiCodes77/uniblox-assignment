import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { AdminPanel } from './components/AdminPanel'
import { CartView } from './components/CartView'
import { Catalog } from './components/Catalog'
import './App.css'

type Tab = 'shop' | 'cart' | 'admin'

const USER_KEY = 'store_user_id'

function App() {
  const [tab, setTab] = useState<Tab>('shop')
  const [userId, setUserId] = useState(() => localStorage.getItem(USER_KEY) ?? 'alice')
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const [cartRefresh, setCartRefresh] = useState(0)

  useEffect(() => {
    localStorage.setItem(USER_KEY, userId)
  }, [userId])

  useEffect(() => {
    api
      .health()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false))
  }, [])

  const bumpCart = useCallback(() => setCartRefresh((k) => k + 1), [])

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <div className="brand-mark">S</div>
            <div>
              <h1>Store</h1>
              <p>Ecommerce demo</p>
            </div>
          </div>

          <div className="header-actions">
            <div className="user-field">
              <label htmlFor="user-id">User</label>
              <input
                id="user-id"
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="user id"
                spellCheck={false}
              />
            </div>
            <span
              className={`status-dot ${backendOk === null ? '' : backendOk ? 'ok' : 'err'}`}
              title={
                backendOk === null
                  ? 'Checking backend…'
                  : backendOk
                    ? 'Backend connected'
                    : 'Backend unreachable — start uvicorn on :8000'
              }
            />
          </div>
        </div>
      </header>

      {backendOk === false && (
        <div className="alert alert-error">
          Cannot reach the API. Start the backend with{' '}
          <code>uvicorn app.main:app --reload</code> from the project root.
        </div>
      )}

      <nav className="nav" aria-label="Main">
        <button
          type="button"
          className={tab === 'shop' ? 'active' : ''}
          onClick={() => setTab('shop')}
        >
          Shop
        </button>
        <button
          type="button"
          className={tab === 'cart' ? 'active' : ''}
          onClick={() => setTab('cart')}
        >
          Cart
        </button>
        <button
          type="button"
          className={tab === 'admin' ? 'active' : ''}
          onClick={() => setTab('admin')}
        >
          Admin
        </button>
      </nav>

      {tab === 'shop' && <Catalog userId={userId} onCartChange={bumpCart} />}
      {tab === 'cart' && (
        <CartView userId={userId} refreshKey={cartRefresh} onCheckout={bumpCart} />
      )}
      {tab === 'admin' && <AdminPanel />}
    </div>
  )
}

export default App
