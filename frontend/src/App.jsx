import React, { useState } from 'react';
import LoginPage from './pages/LoginPage';
import InstructorDashboard from './pages/instructor/InstructorDashboard';
import TADashboard from './pages/ta/TADashboard';

function App() {
  const [role, setRole] = useState(null);

  if (!role) return <LoginPage onLogin={setRole} />;
  if (role === 'instructor') return <InstructorDashboard onLogout={() => setRole(null)} />;
  return <TADashboard onLogout={() => setRole(null)} />;
}

export default App;
