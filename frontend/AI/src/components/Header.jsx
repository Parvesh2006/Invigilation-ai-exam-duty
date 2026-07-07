import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { FaBell, FaEye, FaCircle, FaMoon, FaSun } from 'react-icons/fa'
import { AnimateDigits } from '@/components/unlumen-ui/animate-digits'
import { notificationItems, profileMenuItems } from '../data/dashboardData'

function Header({ title, status, theme, toggleTheme }) {
  const [dateTime, setDateTime] = useState(new Date())
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const timer = window.setInterval(() => {
      setDateTime(new Date())
    }, 1000)

    return () => window.clearInterval(timer)
  }, [])

  const formattedDate = useMemo(() => dateTime.toLocaleDateString(), [dateTime])
  const formattedTime = useMemo(
    () =>
      dateTime.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      }),
    [dateTime],
  )

  const handleNavigate = (path) => {
    navigate(path)
    setShowNotifications(false)
    setShowProfile(false)
  }

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`rounded-[24px] border px-5 py-4 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl sm:px-6 lg:px-8 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => handleNavigate('/dashboard')}
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6C63FF] via-[#8B5CF6] to-[#3B82F6] shadow-lg shadow-indigo-200"
          >
            <FaEye className="text-xl text-white" />
          </button>
          <div>
            <h1 className={`text-xl font-semibold tracking-tight sm:text-2xl ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>{title}</h1>
            <p className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>AI-powered exam surveillance cockpit</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            className={`rounded-2xl border px-3 py-2 text-sm transition hover:scale-105 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-200' : 'border-slate-200/80 bg-slate-50/70 text-slate-600'}`}
          >
            {theme === 'dark' ? <FaSun /> : <FaMoon />}
          </button>

          <div className={`rounded-2xl border px-3 py-2 text-sm ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-300' : 'border-slate-200/80 bg-slate-50/70 text-slate-600'}`}>
            <div className="flex items-center gap-2">
              <FaCircle className="text-[10px] text-emerald-500" />
              <span className={`font-medium ${theme === 'dark' ? 'text-slate-200' : 'text-slate-700'}`}>{status}</span>
            </div>
          </div>

          <div className={`rounded-2xl border px-3 py-2 text-sm ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-300' : 'border-slate-200/80 bg-slate-50/70 text-slate-600'}`}>
            <div className={`font-medium ${theme === 'dark' ? 'text-slate-200' : 'text-slate-700'}`}>{formattedDate}</div>
          </div>

          <div className={`rounded-2xl border px-3 py-2 text-sm ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-300' : 'border-slate-200/80 bg-slate-50/70 text-slate-600'}`}>
            <AnimateDigits
              value={formattedTime}
              className={`text-lg font-semibold ${theme === 'dark' ? 'text-white' : 'text-black'}`}
            />
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowNotifications((value) => !value)}
              className={`relative flex h-11 w-11 items-center justify-center rounded-2xl border shadow-sm transition hover:scale-105 hover:text-indigo-600 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-200' : 'border-slate-200/80 bg-white/80 text-slate-600'}`}
            >
              <FaBell />
              <span className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-rose-500" />
            </button>
            {showNotifications && (
              <div className={`absolute right-0 z-20 mt-2 w-56 rounded-2xl border p-3 shadow-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/95' : 'border-slate-200/80 bg-white/95'}`}>
                {notificationItems.map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => handleNavigate(item.to)}
                    className={`mb-2 flex w-full items-center rounded-xl px-3 py-2 text-left text-sm transition ${theme === 'dark' ? 'text-slate-200 hover:bg-slate-800' : 'text-slate-700 hover:bg-slate-100'}`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowProfile((value) => !value)}
              className={`flex items-center gap-3 rounded-2xl border px-3 py-2 shadow-sm ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80' : 'border-slate-200/80 bg-slate-50/70'}`}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-[#6C63FF] to-[#3B82F6] font-semibold text-white">
                AK
              </div>
              <div className="text-left">
                <p className={`text-sm font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-800'}`}>A. Kumar</p>
                <p className={`text-xs ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Ops Lead</p>
              </div>
            </button>
            {showProfile && (
              <div className={`absolute right-0 z-20 mt-2 w-48 rounded-2xl border p-3 shadow-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/95' : 'border-slate-200/80 bg-white/95'}`}>
                {profileMenuItems.map((item) => (
                  <Link
                    key={item.label}
                    to={item.to}
                    className={`mb-2 block rounded-xl px-3 py-2 text-left text-sm transition ${theme === 'dark' ? 'text-slate-200 hover:bg-slate-800' : 'text-slate-700 hover:bg-slate-100'}`}
                    onClick={() => setShowProfile(false)}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.header>
  )
}

export default Header
