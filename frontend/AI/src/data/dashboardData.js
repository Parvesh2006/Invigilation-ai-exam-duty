export const dashboardData = {
  header: {
    title: 'Invigilation Duty Anomaly Detection',
    status: 'Online',
  },
  liveCamera: {
    hall: 'A-101',
    faculty: 'Dr. Kumar',
    studentsPresent: 48,
    exam: 'Operating Systems',
    timeRemaining: '02:15:34',
    cameraLabel: 'Camera 01',
  },
  aiSummary: {
    hall: 'All Exam Halls',
    faculty: '12 Faculty Active',
    students: 480,
    detectedPersons: 486,
    suspiciousEvents: 0,
    objectsDetected: 'Waiting for backend data',
    confidence: 'Connecting',
    status: 'Monitoring',
  },
  riskMeter: {
    risk: 0,
    label: 'Risk',
    status: 'Safe',
  },
  timeline: [
    { time: '09:00', title: 'Exam Started', icon: 'Shield' },
    { time: '09:15', title: 'Faculty Entered', icon: 'Eye' },
    { time: '09:20', title: 'All Students Seated', icon: 'Users' },
    { time: '09:45', title: 'Student Left Seat', icon: 'AlertTriangle' },
    { time: '09:52', title: 'Mobile Phone Detected', icon: 'Camera' },
    { time: '10:05', title: 'Multiple Faces Detected', icon: 'Brain' },
    { time: '10:10', title: 'AI Warning Generated', icon: 'Shield' },
  ],
  stats: [
    { title: 'Total Students', value: '48', icon: 'Users' },
    { title: 'Active Cameras', value: '12', icon: 'Camera' },
    { title: 'Detected Alerts', value: '00', icon: 'AlertTriangle' },
    { title: 'AI Accuracy', value: 'Live', icon: 'ChartBar' },
  ],
  alerts: [
    { title: 'Waiting for live alerts', color: 'success' },
  ],
}

export const notificationItems = [
  { label: 'Live feed updated', to: '/camera' },
  { label: 'New alert received', to: '/alerts' },
  { label: 'Faculty activity synced', to: '/dashboard' },
]

export const profileMenuItems = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Camera Summary', to: '/camera' },
  { label: 'Alert Centre', to: '/alerts' },
]
