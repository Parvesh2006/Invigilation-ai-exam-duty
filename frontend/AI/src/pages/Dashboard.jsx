import { useEffect, useState } from 'react'
import Header from '../components/Header'
import LiveCamera from '../components/LiveCamera'
import AISummary from '../components/AISummary'
import Timeline from '../components/Timeline'
import StatsCards from '../components/StatsCards'
import AlertsPanel from '../components/AlertsPanel'
import InspectionForm from '../components/InspectionForm'
import RiskMeter from '../components/RiskMeter'
import { dashboardData } from '../data/dashboardData'

const API = 'http://127.0.0.1:8000'

const colorForLevel = (riskLevel) => {
  if (riskLevel === 'Critical') return 'danger'
  if (riskLevel === 'High') return 'danger'
  if (riskLevel === 'Medium') return 'warning'
  return 'success'
}

function Dashboard({ theme, toggleTheme }) {
  const [cameraData, setCameraData] = useState(dashboardData.liveCamera)
  const [summaryData, setSummaryData] = useState(dashboardData.aiSummary)
  const [timelineData, setTimelineData] = useState(dashboardData.timeline)
  const [statsData, setStatsData] = useState(dashboardData.stats)
  const [alertsData, setAlertsData] = useState(dashboardData.alerts)
  const [riskData, setRiskData] = useState(dashboardData.riskMeter)
  const [formData, setFormData] = useState({ name: '', hall: '', note: '' })
  const [formStatus, setFormStatus] = useState({ type: '', message: '' })
  const [loading, setLoading] = useState(true)
  const [apiStatus, setApiStatus] = useState('Connecting')

  const applyBackendData = (alertsPayload, riskPayload) => {
    const alerts = alertsPayload?.alerts || []
    const totalAlerts = alertsPayload?.total_alerts ?? alerts.length
    const risk = riskPayload?.risk_score ?? 0
    const status = riskPayload?.status || 'Safe'

    setAlertsData(
      alerts.slice(0, 6).map((alert) => ({
        title: alert.message || alert.alert_type,
        color: colorForLevel(alert.risk_level),
      })),
    )

    setRiskData({
      risk,
      label: 'Risk',
      status,
    })

    setSummaryData((current) => ({
      ...current,
      suspiciousEvents: totalAlerts,
      status,
      confidence: totalAlerts > 0 ? 'Backend Live' : 'Monitoring',
    }))

    setStatsData([
      { title: 'Total Students', value: '48', icon: 'Users' },
      { title: 'Active Cameras', value: '12', icon: 'Camera' },
      { title: 'Detected Alerts', value: String(totalAlerts).padStart(2, '0'), icon: 'AlertTriangle' },
      { title: 'Risk Score', value: String(risk), icon: 'ChartBar' },
    ])

    setTimelineData(
      alerts.slice(0, 6).map((alert) => ({
        time: alert.timestamp?.slice(11, 16) || '--:--',
        title: alert.message || alert.alert_type,
        icon: 'Shield',
      })),
    )

    setApiStatus('Connected')
    setLoading(false)
  }

  const fetchBackendData = async () => {
    setLoading(true)
    try {
      const [alertsResponse, riskResponse] = await Promise.all([
        fetch(`${API}/alerts`),
        fetch(`${API}/risk-score`),
      ])

      const alertsPayload = await alertsResponse.json()
      const riskPayload = await riskResponse.json()
      applyBackendData(alertsPayload, riskPayload)
    } catch (error) {
      setApiStatus('Offline')
      setLoading(false)
      setFormStatus({
        type: 'error',
        message: 'Could not reach the backend. Start FastAPI on http://127.0.0.1:8000.',
      })
    }
  }

  useEffect(() => {
    fetchBackendData()
  }, [])

  const refreshDashboard = async () => {
    await fetchBackendData()
    setFormStatus({ type: 'success', message: 'Dashboard refreshed from live backend data.' })
  }

  const downloadReport = () => {
    window.open(`${API}/report`, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className={`min-h-screen px-3 py-4 sm:px-4 lg:px-6 lg:py-6 ${theme === 'dark' ? 'bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.2),_transparent_32%),linear-gradient(135deg,_#020617_0%,_#0f172a_100%)] text-slate-100' : 'bg-[radial-gradient(circle_at_top_left,_rgba(108,99,255,0.08),_transparent_32%),linear-gradient(135deg,_#f4f7fe_0%,_#f8faff_100%)] text-slate-900'}`}>
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <Header title={dashboardData.header.title} status={apiStatus} theme={theme} toggleTheme={toggleTheme} />

        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            type="button"
            className="rounded-2xl border border-slate-200/80 bg-white/70 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:scale-105 dark:border-slate-700/80 dark:bg-slate-900/80 dark:text-slate-100"
            onClick={refreshDashboard}
          >
            Refresh Data
          </button>
          <button
            type="button"
            onClick={downloadReport}
            className="rounded-2xl bg-gradient-to-r from-[#6C63FF] to-[#3B82F6] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:scale-105"
          >
            Download PDF
          </button>
        </div>

        {loading ? (
          <div className={`rounded-[24px] border px-5 py-4 text-sm ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70 text-slate-300' : 'border-white/70 bg-white/70 text-slate-700'}`}>
            Loading live backend data...
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[1.6fr_0.75fr]">
          <div className="space-y-4">
            <LiveCamera data={cameraData} theme={theme} />
            <AISummary data={summaryData} theme={theme} />
          </div>
          <div className="space-y-4">
            <RiskMeter data={riskData} theme={theme} />
            <AlertsPanel alerts={alertsData} theme={theme} />
          </div>
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
