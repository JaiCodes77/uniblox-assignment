import { useCallback, useEffect, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  enabled = true,
): AsyncState<T> & { reload: () => void } {
  const [reloadToken, setReloadToken] = useState(0)
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: enabled,
    error: null,
  })

  const reload = useCallback(() => setReloadToken((n) => n + 1), [])

  useEffect(() => {
    if (!enabled) {
      return
    }

    let active = true

    void (async () => {
      try {
        const data = await fetcher()
        if (active) {
          setState({ data, loading: false, error: null })
        }
      } catch (e) {
        if (active) {
          setState({
            data: null,
            loading: false,
            error: e instanceof Error ? e.message : 'Request failed',
          })
        }
      }
    })()

    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetcher identity is intentionally excluded
  }, [enabled, reloadToken, ...deps])

  if (!enabled) {
    return { data: null, loading: false, error: null, reload }
  }

  return { ...state, reload }
}
