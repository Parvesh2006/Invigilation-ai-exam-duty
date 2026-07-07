import { motion } from 'framer-motion'

function Heatmap({ theme }) {
  const blocks = [
    ['from-indigo-500/80 to-blue-500/80', 'from-fuchsia-500/80 to-indigo-500/80', 'from-emerald-500/80 to-cyan-500/80'],
    ['from-amber-400/80 to-rose-500/80', 'from-sky-500/80 to-indigo-500/80', 'from-violet-500/80 to-fuchsia-500/80'],
    ['from-emerald-500/80 to-cyan-500/80', 'from-blue-500/80 to-indigo-500/80', 'from-amber-400/80 to-orange-500/80'],
  ]

  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.2 }}
      className={`rounded-[24px] border p-5 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-500">Heatmap</p>
          <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>AI Movement Density</h2>
        </div>
      </div>

      <div className={`rounded-[20px] border p-4 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80' : 'border-slate-200/70 bg-slate-50/80'}`}>
        <div className="grid grid-cols-3 gap-3">
          {blocks.flat().map((gradient, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.35, delay: 0.04 * index }}
              className={`h-18 rounded-2xl bg-gradient-to-br ${gradient}`}
            />
          ))}
        </div>
        <p className={`mt-4 text-sm leading-6 ${theme === 'dark' ? 'text-slate-300' : 'text-slate-600'}`}>
          Future AI Heatmap Visualization
        </p>
        <p className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>
          This section will visualize movement density and suspicious activity detected using computer vision.
        </p>
      </div>
    </motion.section>
  )
}

export default Heatmap
