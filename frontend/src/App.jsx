import { Canvas } from '@react-three/fiber'
import { useEffect } from 'react'
import BlobOrb from './components/BlobOrb'
import ChatLog from './components/ChatLog'
import MemoryToast from './components/MemoryToast'
import useJarvis from './hooks/useJarvis'
import './App.css'

const STATUS_LABELS = {
  disconnected: 'Sin conexión',
  idle:         'Clic o espacio para hablar',
  listening:    'Escuchando...',
  thinking:     'Procesando...',
  speaking:     'Respondiendo...',
}

export default function App() {
  const { status, messages, transcript, memoryProposal, confirmMemory, toggleListen, clearMessages } = useJarvis()

  useEffect(() => {
    const onKey = (e) => {
      if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault()
        toggleListen()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [toggleListen])

  return (
    <div className="app">
      <div className="orb-wrap" onClick={toggleListen}>
        <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
          <ambientLight intensity={1.2} />
          <pointLight position={[5, 5, 5]} intensity={3} />
          <pointLight position={[-5, -5, -5]} intensity={1} color="#60a5fa" />
          <BlobOrb status={status} />
        </Canvas>
      </div>

      <p className="status-label">{STATUS_LABELS[status]}</p>

      {transcript && (
        <div className="transcript-pill">{transcript}</div>
      )}

      <ChatLog messages={messages} onClear={clearMessages} />
      <MemoryToast proposal={memoryProposal} onConfirm={confirmMemory} />
    </div>
  )
}
