import { motion } from 'framer-motion'
import { FaExclamationTriangle } from 'react-icons/fa'

function RiskMeter({ data, theme }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (data.risk / 100) * circumference

  const getColor = () => {
    if (data.risk <= 30) return '#22C55E'
    if (data.risk <= 70) return '#F59E0B'
    return '#EF4444'
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.12 }}
      className={`rounded-[24px] border p-5 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-500">Risk Meter</p>
          <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>Threat Level</h2>
        </div>
        <div className={`rounded-2xl p-2 ${theme === 'dark' ? 'bg-slate-800 text-amber-400' : 'bg-slate-100 text-amber-500'}`}>
          <FaExclamationTriangle />
        </div>
      </div>

      <div className={`flex flex-col items-center justify-center rounded-[20px] border p-4 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80' : 'border-slate-200/70 bg-slate-50/80'}`}>
        <div className="relative flex h-36 w-36 items-center justify-center">
          <svg viewBox="0 0 140 140" className="h-36 w-36 -rotate-90">
            <circle cx="70" cy="70" r={radius} stroke="#e5e7eb" strokeWidth="12" fill="none" />
            <motion.circle
              cx="70"
              cy="70"
              r={radius}
              stroke={getColor()}
              strokeWidth="12"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </svg>
          <div className="absolute text-center">
            <p className={`text-xs font-semibold uppercase tracking-[0.25em] ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Risk</p>
            <p className={`text-4xl font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>{data.risk}%</p>
          </div>
        </div>
        <div className={`mt-3 flex items-center gap-2 rounded-full px-3 py-2 text-sm font-semibold shadow-sm ${theme === 'dark' ? 'bg-slate-900/70 text-slate-300' : 'bg-white/70 text-slate-700'}`}>
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: getColor() }} />
          {data.status}
        </div>
      </div>
    </motion.section>
  )
}

export default RiskMeter
