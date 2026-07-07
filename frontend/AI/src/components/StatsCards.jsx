import { motion } from 'framer-motion'
import { FaCamera, FaChartBar, FaExclamationTriangle, FaUsers } from 'react-icons/fa'

const iconMap = {
  Users: FaUsers,
  Camera: FaCamera,
  AlertTriangle: FaExclamationTriangle,
  ChartBar: FaChartBar,
}

function StatsCards({ items, theme }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item, index) => {
        const Icon = iconMap[item.icon]
        return (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.08 * index }}
            whileHover={{ y: -4, scale: 1.01 }}
            className={`rounded-[24px] border p-4 shadow-[0_20px_60px_rgba(108,99,255,0.1)] backdrop-blur-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-semibold ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{item.title}</p>
                <p className={`mt-2 text-3xl font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>{item.value}</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6C63FF] to-[#3B82F6] text-white shadow-lg">
                <Icon />
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}

export default StatsCards
