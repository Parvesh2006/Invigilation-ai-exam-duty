import { useState } from 'react'
import { motion } from 'framer-motion'

function InspectionForm({ formData, setFormData, formStatus, setFormStatus, theme }) {
  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const trimmedName = formData.name.trim()
    const trimmedHall = formData.hall.trim()
    const trimmedNote = formData.note.trim()

    if (!trimmedName || !trimmedHall || !trimmedNote) {
      setFormStatus({ type: 'error', message: 'Please complete every field before sending the report.' })
      return
    }

    setFormStatus({ type: 'success', message: `Report submitted for ${trimmedName} in ${trimmedHall}.` })
    setFormData({ name: '', hall: '', note: '' })
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={`rounded-[24px] border p-5 shadow-[0_20px_60px_rgba(108,99,255,0.12)] backdrop-blur-xl ${theme === 'dark' ? 'border-slate-700/80 bg-slate-900/70' : 'border-white/70 bg-white/70'}`}
    >
      <div className="mb-4">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-indigo-500">Inspection Form</p>
        <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>Submit an anomaly note</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Inspector name"
          className={`w-full rounded-2xl border px-3 py-2 text-sm outline-none ring-0 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-200 placeholder:text-slate-500' : 'border-slate-200/80 bg-slate-50/80 text-slate-700'}`}
        />
        <input
          type="text"
          name="hall"
          value={formData.hall}
          onChange={handleChange}
          placeholder="Hall / Room"
          className={`w-full rounded-2xl border px-3 py-2 text-sm outline-none ring-0 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-200 placeholder:text-slate-500' : 'border-slate-200/80 bg-slate-50/80 text-slate-700'}`}
        />
        <textarea
          name="note"
          value={formData.note}
          onChange={handleChange}
          placeholder="Describe the anomaly"
          rows="3"
          className={`w-full rounded-2xl border px-3 py-2 text-sm outline-none ring-0 ${theme === 'dark' ? 'border-slate-700/80 bg-slate-800/80 text-slate-200 placeholder:text-slate-500' : 'border-slate-200/80 bg-slate-50/80 text-slate-700'}`}
        />
        <button
          type="submit"
          className="rounded-2xl bg-gradient-to-r from-[#6C63FF] to-[#3B82F6] px-4 py-2 text-sm font-semibold text-white transition hover:scale-105"
        >
          Submit Report
        </button>
      </form>

      {formStatus.message ? (
        <div className={`mt-3 rounded-2xl border px-3 py-2 text-sm ${formStatus.type === 'success' ? 'border-emerald-200 bg-emerald-50/80 text-emerald-700' : 'border-rose-200 bg-rose-50/80 text-rose-700'}`}>
          {formStatus.message}
        </div>
      ) : null}
    </motion.section>
  )
}

export default InspectionForm
