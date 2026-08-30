import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useLogout, useMe } from '../api/hooks'

export function Layout() {
  const me = useMe()
  const logout = useLogout()
  const navigate = useNavigate()

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-sm font-semibold text-slate-900">
            AymanChat
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
            Demo corpus
          </span>
          {me.data && (
            <button
              onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login') })}
              className="text-sm text-slate-500 hover:text-slate-800"
            >
              Log out
            </button>
          )}
        </div>
      </header>
      <Outlet />
    </div>
  )
}
