import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState("Checking System...");

  // دالة لفحص اتصال الـ Backend
  const checkSystem = async () => {
    try {
      // سنستخدم /api للتحدث مع الباكيند عبر Nginx
      const response = await fetch('/api/health');
      if (response.ok) {
        setStatus("System Online 🟢");
      } else {
        setStatus("System Error 🔴");
      }
    } catch (error) {
      setStatus("Backend Unreachable ⚠️");
    }
  };

  useEffect(() => {
    checkSystem();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial', textAlign: 'center' }}>
      <h1>🏢 Smart Office Controller</h1>
      <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc', borderRadius: '10px' }}>
        <h2>System Status</h2>
        <h3>{status}</h3>
        <button onClick={checkSystem} style={{ padding: '10px 20px', cursor: 'pointer' }}>
          Refresh Status
        </button>
      </div>
    </div>
  )
}

export default App