import { useEffect, useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import NotFound from './pages/NotFound'

function App() {
  const [theme, setTheme] = useState(() => {
    const storedTheme = window.localStorage.getItem('invigilation-theme')
    return storedTheme || 'light'
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.body.classList.toggle('dark', theme === 'dark')
    window.localStorage.setItem('invigilation-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((current) => (current === 'light' ? 'dark' : 'light'))
  }

  return (
    <Routes>
      <Route path="/" element={<Dashboard theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="/dashboard" element={<Dashboard theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="/camera" element={<Dashboard theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="/alerts" element={<Dashboard theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="/profile" element={<Dashboard theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
