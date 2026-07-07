import { motion } from 'framer-motion'
import { FaCamera, FaEye, FaShieldAlt, FaUsers, FaExclamationTriangle, FaBrain } from 'react-icons/fa'

const iconMap = {
  Shield: FaShieldAlt,
  Eye: FaEye,
  Users: FaUsers,
  Camera: FaCamera,
  AlertTriangle: FaExclamationTriangle,
  Brain: FaBrain,
}

function Timeline({ items, theme }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.16 }}
      className={`rounded-[24px] border p-5 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-500">Timeline</p>
          <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>Event Stream</h2>
        </div>
        <div className={`rounded-2xl px-3 py-2 text-sm font-semibold ${theme === 'dark' ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>Live</div>
      </div>

      <div className="max-h-[320px] space-y-3 overflow-y-auto pr-2">
        {items.map((item, index) => {
          const Icon = iconMap[item.icon]
          return (
            <motion.div
              key={`${item.time}-${item.title}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.05 * index }}
              className={`flex items-start gap-3 rounded-2xl border p-3 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80' : 'border-slate-200/70 bg-slate-50/80'}`}
            >
              <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6C63FF] to-[#3B82F6] text-white shadow-sm">
                <Icon />
              </div>
              <div>
                <p className={`text-sm font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-800'}`}>{item.title}</p>
                <p className={`text-xs ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{item.time}</p>
              </div>
            </motion.div>
          )
        })}
      </div>
    </motion.section>
  )
}

export default Timeline
