import { useState } from 'react'
import { motion } from 'framer-motion'
import { FaCamera, FaClock, FaTimes, FaUsers } from 'react-icons/fa'

function LiveCamera({ data, theme }) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [selectedCamera, setSelectedCamera] = useState(null)

  const cameras = [
    { id: 1, label: 'Camera 01', hall: 'Hall A-101', badge: 'Live' },
    { id: 2, label: 'Camera 02', hall: 'Hall A-102', badge: 'Live' },
    { id: 3, label: 'Camera 03', hall: 'Hall A-103', badge: 'Live' },
    { id: 4, label: 'Camera 04', hall: 'Hall A-104', badge: 'Live' },
  ]

  const openAllCameras = () => {
    setSelectedCamera(null)
    setIsFullscreen(true)
  }

  const openCamera = (cameraId) => {
    setSelectedCamera(cameraId)
    setIsFullscreen(true)
  }

  const closeFullscreen = () => {
    setSelectedCamera(null)
    setIsFullscreen(false)
  }

  const activeCamera = cameras.find((camera) => camera.id === selectedCamera) || cameras[0]

  return (
    <>
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className={`relative overflow-hidden rounded-[24px] border p-4 shadow-[0_20px_60px_rgba(59,130,246,0.14)] backdrop-blur-xl sm:p-5 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
      >
        <div className="relative overflow-hidden rounded-[20px] border border-indigo-200/70 bg-slate-950 p-3 shadow-inner">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(108,99,255,0.25),_transparent_50%),radial-gradient(circle_at_bottom_right,_rgba(59,130,246,0.25),_transparent_40%)]" />
          <button
            type="button"
            onClick={openAllCameras}
            className="relative grid min-h-[320px] w-full gap-3 rounded-[18px] border border-white/10 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-4 text-left sm:min-h-[380px] sm:grid-cols-2"
          >
            <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:28px_28px]" />
            {cameras.map((camera) => (
              <div
                key={camera.id}
                role="button"
                tabIndex={0}
                onClick={(event) => {
                  event.stopPropagation()
                  openCamera(camera.id)
                }}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    event.stopPropagation()
                    openCamera(camera.id)
                  }
                }}
                className="relative overflow-hidden rounded-[16px] border border-white/10 bg-slate-900/60 backdrop-blur-md"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-slate-800/80 via-slate-900 to-indigo-950" />
                <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-white backdrop-blur-md">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-rose-500" />
                  {camera.label}
                </div>
                <div className="absolute bottom-3 left-3 rounded-xl border border-white/10 bg-slate-950/70 px-2.5 py-1.5 text-[11px] text-slate-200">
                  {camera.hall}
                </div>
                <div className="absolute inset-0 flex items-center justify-center text-sm font-medium text-slate-300">
                  Placeholder feed • AI overlay active
                </div>
              </div>
            ))}
          </button>
          <div className="absolute inset-x-0 bottom-0 flex justify-center pb-8">
            <div className="rounded-2xl border border-white/20 bg-slate-900/70 px-4 py-3 text-sm text-slate-200 backdrop-blur-md">
              Click any camera tile to view it full screen
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className={`text-sm font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-800'}`}>{data.exam}</p>
            <p className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Across all exam halls</p>
          </div>
          <div className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${theme === 'dark' ? 'border-indigo-500/30 bg-indigo-500/10 text-indigo-200' : 'border-indigo-100 bg-indigo-50/80 text-indigo-700'}`}>
            <FaClock />
            <span>{data.timeRemaining}</span>
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200/70 bg-slate-50/80 p-3">
            <div className="mb-1 flex items-center gap-2 text-slate-500">
              <FaUsers className="text-indigo-500" />
              <span className={`text-xs font-semibold uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Students</span>
            </div>
            <p className={`text-xl font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>480</p>
          </div>
          <div className="rounded-2xl border border-slate-200/70 bg-slate-50/80 p-3">
            <div className="mb-1 flex items-center gap-2 text-slate-500">
              <FaCamera className="text-fuchsia-500" />
              <span className={`text-xs font-semibold uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Faculty</span>
            </div>
            <p className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>12 faculty</p>
          </div>
          <div className="rounded-2xl border border-slate-200/70 bg-slate-50/80 p-3">
            <div className="mb-1 flex items-center gap-2 text-slate-500">
              <FaClock className="text-emerald-500" />
              <span className={`text-xs font-semibold uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>Exam</span>
            </div>
            <p className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>486 detected</p>
          </div>
        </div>
      </motion.section>

      {isFullscreen ? (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/90 p-3 sm:p-6">
          <div className="flex h-full w-full max-w-7xl flex-col overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/95 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 sm:px-6">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-400">Camera View</p>
                <h3 className="text-base font-semibold text-white">{selectedCamera ? activeCamera.hall : 'All Cameras'}</h3>
              </div>
              <button
                type="button"
                onClick={closeFullscreen}
                className="flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/20"
              >
                <FaTimes />
                Close
              </button>
            </div>

            <div className="flex-1 overflow-auto p-4 sm:p-6">
              {selectedCamera ? (
                <div className="grid gap-4 lg:grid-cols-[1.4fr_0.6fr]">
                  <div className="relative min-h-[60vh] overflow-hidden rounded-[24px] border border-white/10 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
                    <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:28px_28px]" />
                    <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-white backdrop-blur-md">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-rose-500" />
                      {activeCamera.label}
                    </div>
                    <div className="absolute bottom-4 left-4 rounded-2xl border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-slate-200">
                      {activeCamera.hall}
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center text-center text-sm font-medium text-slate-300">
                      Full-screen placeholder view • AI monitoring active
                    </div>
                  </div>

                  <div className="space-y-3 rounded-[24px] border border-white/10 bg-slate-900/70 p-4">
                    <button
                      type="button"
                      onClick={() => setSelectedCamera(null)}
                      className="w-full rounded-2xl border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-sm font-semibold text-indigo-200 transition hover:bg-indigo-500/20"
                    >
                      View all cameras
                    </button>
                    {cameras.map((camera) => (
                      <button
                        key={camera.id}
                        type="button"
                        onClick={() => openCamera(camera.id)}
                        className={`w-full rounded-2xl border px-3 py-3 text-left text-sm transition ${selectedCamera === camera.id ? 'border-indigo-400 bg-indigo-500/20 text-white' : 'border-white/10 bg-slate-950/50 text-slate-200 hover:bg-slate-800/80'}`}
                      >
                        <div className="font-semibold">{camera.label}</div>
                        <div className="text-xs text-slate-400">{camera.hall}</div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {cameras.map((camera) => (
                    <button
                      key={camera.id}
                      type="button"
                      onClick={() => openCamera(camera.id)}
                      className="relative min-h-[240px] overflow-hidden rounded-[24px] border border-white/10 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-left"
                    >
                      <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:28px_28px]" />
                      <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-white backdrop-blur-md">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-rose-500" />
                        {camera.label}
                      </div>
                      <div className="absolute bottom-4 left-4 rounded-2xl border border-white/10 bg-slate-950/70 px-3 py-2 text-sm text-slate-200">
                        {camera.hall}
                      </div>
                      <div className="absolute inset-0 flex items-center justify-center text-sm font-medium text-slate-300">
                        Click to open full screen
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}

export default LiveCamera
