import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import './App.css'
import Navbar from './components/layout/Navbar'
import Sidebar from './components/layout/Sidebar'
import ChatPage from './pages/ChatPage'
import UploadPage from './pages/UploadPage'
import LibraryPage from './pages/LibraryPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-wrapper d-flex flex-column" style={{ height: '100vh' }}>
        <Navbar />
        <div className="d-flex flex-grow-1 overflow-hidden">
          <Sidebar />
          <main className="flex-grow-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/library" element={<LibraryPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
