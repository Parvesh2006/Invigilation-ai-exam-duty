import { useEffect, useMemo, useState } from 'react'
import Header from '../components/Header'
import LiveCamera from '../components/LiveCamera'
import AISummary from '../components/AISummary'
import Timeline from '../components/Timeline'
import StatsCards from '../components/StatsCards'
import AlertsPanel from '../components/AlertsPanel'
import InspectionForm from '../components/InspectionForm'
import { dashboardData } from '../data/dashboardData'

function Dashboard({ theme, toggleTheme }) {
  const [cameraData, setCameraData] = useState(dashboardData.liveCamera)
  const [summaryData, setSummaryData] = useState(dashboardData.aiSummary)
  const [timelineData, setTimelineData] = useState(dashboardData.timeline)
  const [statsData, setStatsData] = useState(dashboardData.stats)
  const [alertsData, setAlertsData] = useState(dashboardData.alerts)
  const [formData, setFormData] = useState({ name: '', hall: '', note: '' })
  const [formStatus, setFormStatus] = useState({ type: '', message: '' })

  const refreshDashboard = () => {
    setCameraData({
      ...cameraData,
      studentsPresent: cameraData.studentsPresent + 1,
      timeRemaining: '01:48:11',
    })
    setSummaryData({
      ...summaryData,
      confidence: '96%',
      suspiciousEvents: summaryData.suspiciousEvents + 1,
    })
    setTimelineData((current) => [
      { time: '10:18', title: 'Refresh Sync Completed', icon: 'Shield' },
      ...current.slice(0, 6),
    ])
    setStatsData((current) => current.map((item, index) => {
      if (index === 0) return { ...item, value: String(Number(item.value) + 1) }
      if (index === 1) return { ...item, value: String(Number(item.value) + 1) }
      if (index === 2) return { ...item, value: '04' }
      return item
    }))
    setAlertsData((current) => [{ title: 'System Refresh Complete', color: 'success' }, ...current.slice(0, 3)])
    setFormStatus({ type: 'success', message: 'Dashboard refreshed with simulated updates.' })
  }

  const summaryItems = useMemo(() => [
    { label: 'Hall', value: summaryData.hall },
    { label: 'Faculty', value: summaryData.faculty },
    { label: 'Students', value: summaryData.students },
  ], [summaryData])

  return (
    <div className={`min-h-screen px-3 py-4 sm:px-4 lg:px-6 lg:py-6 ${theme === 'dark' ? 'bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.2),_transparent_32%),linear-gradient(135deg,_#020617_0%,_#0f172a_100%)] text-slate-100' : 'bg-[radial-gradient(circle_at_top_left,_rgba(108,99,255,0.08),_transparent_32%),linear-gradient(135deg,_#f4f7fe_0%,_#f8faff_100%)] text-slate-900'}`}>
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <Header title={dashboardData.header.title} status={dashboardData.header.status} theme={theme} toggleTheme={toggleTheme} />

        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            type="button"
            onClick={(event) => {
              event.preventDefault()
              refreshDashboard()
            }}
            className="rounded-2xl border border-slate-200/80 bg-white/70 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:scale-105"
          >
            Refresh Data
          </button>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.6fr_0.75fr]">
          <div className="space-y-4">
            <LiveCamera data={cameraData} theme={theme} />

            <AISummary data={summaryData} theme={theme} />
          </div>

          <AlertsPanel alerts={alertsData} theme={theme} />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1fr]">
          <Timeline items={timelineData} theme={theme} />
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <StatsCards items={statsData} theme={theme} />
          <InspectionForm formData={formData} setFormData={setFormData} formStatus={formStatus} setFormStatus={setFormStatus} theme={theme} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard
