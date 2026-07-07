import { motion } from 'framer-motion'
import { FaBrain, FaShieldAlt } from 'react-icons/fa'

function AISummary({ data, theme }) {
  const items = [
    { label: 'Hall', value: data.hall },
    { label: 'Faculty', value: data.faculty },
    { label: 'Students', value: data.students },
    { label: 'Detected Persons', value: data.detectedPersons },
    { label: 'Suspicious Events', value: data.suspiciousEvents },
    { label: 'Objects Detected', value: data.objectsDetected },
  ]

  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.08 }}
      className={`rounded-[24px] border p-5 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-500">AI Summary</p>
          <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>All Exam Halls Overview</h2>
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6C63FF] to-[#3B82F6] text-white shadow-lg">
          <FaBrain />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.label} className={`rounded-2xl border p-3 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80' : 'border-slate-200/70 bg-slate-50/80'}`}>
            <p className={`text-xs font-semibold uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{item.label}</p>
            <p className={`mt-1 text-sm font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-800'}`}>{item.value}</p>
          </div>
        ))}
      </div>

      <div className={`mt-4 rounded-2xl border p-4 ${theme === 'dark' ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-emerald-100 bg-emerald-50/80'}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`text-sm font-semibold ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>Confidence</p>
            <p className={`text-2xl font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>{data.confidence}</p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-white/70 px-3 py-2 text-sm font-semibold text-emerald-600">
            <FaShieldAlt />
            {data.status}
          </div>
        </div>
      </div>
    </motion.section>
  )
}

export default AISummary
