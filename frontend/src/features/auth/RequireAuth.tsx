import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useMe } from '../../api/hooks'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { data, isLoading, isError } = useMe()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-500">
        Loading...
      </div>
    )
  }

  if (isError || !data) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
