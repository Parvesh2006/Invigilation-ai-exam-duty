import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FaExclamationTriangle, FaShieldAlt, FaUserAlt, FaCheckCircle, FaChevronDown } from 'react-icons/fa'

const iconMap = {
  danger: FaExclamationTriangle,
  warning: FaShieldAlt,
  success: FaCheckCircle,
}

function AlertsPanel({ alerts, theme }) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <motion.aside
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45, delay: 0.24 }}
      className={`rounded-[24px] border p-4 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl lg:sticky lg:top-6 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-500">Alerts</p>
          <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>Recent Activity</h2>
        </div>
        <button
          type="button"
          onClick={() => setIsCollapsed((value) => !value)}
          className={`rounded-full border p-2 transition hover:text-indigo-600 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-300' : 'border-slate-200/80 bg-slate-50/80 text-slate-600'}`}
        >
          <FaChevronDown className={isCollapsed ? 'rotate-180 transition-transform' : 'transition-transform'} />
        </button>
      </div>

      <AnimatePresence initial={false}>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="space-y-3 overflow-hidden"
          >
            {alerts.map((alert) => {
              const Icon = iconMap[alert.color] || FaUserAlt
              const colorClasses = {
                danger: 'border-rose-200 bg-rose-50/80 text-rose-600',
                warning: 'border-amber-200 bg-amber-50/80 text-amber-600',
                success: 'border-emerald-200 bg-emerald-50/80 text-emerald-600',
              }

              return (
                <div key={alert.title} className={`flex items-center gap-3 rounded-2xl border p-3 ${colorClasses[alert.color]}`}>
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/70 shadow-sm">
                    <Icon />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{alert.title}</p>
                    <p className="text-xs text-slate-500">Detected moments ago</p>
                  </div>
                </div>
              )
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.aside>
  )
}

export default AlertsPanel
