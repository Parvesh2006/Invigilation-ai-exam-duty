import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,_rgba(108,99,255,0.08),_transparent_32%),linear-gradient(135deg,_#f4f7fe_0%,_#f8faff_100%)] px-4">
      <div className="rounded-[24px] border border-white/70 bg-white/70 p-8 text-center shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl">
        <h1 className="text-3xl font-semibold text-slate-900">Page not found</h1>
        <p className="mt-2 text-slate-600">The route you requested does not exist.</p>
        <Link to="/" className="mt-5 inline-flex rounded-2xl bg-gradient-to-r from-[#6C63FF] to-[#3B82F6] px-4 py-2 font-semibold text-white transition hover:scale-105">
          Return to dashboard
        </Link>
      </div>
    </div>
  )
}

export default NotFound
