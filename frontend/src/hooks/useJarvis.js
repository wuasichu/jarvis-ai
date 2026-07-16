import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = 'ws://localhost:8765/ws'

export default function useJarvis() {
  const [status, setStatus] = useState('disconnected')
  const [messages, setMessages] = useState([])
  const [transcript, setTranscript] = useState('')
  const [memoryProposal, setMemoryProposal] = useState(null)
  const wsRef = useRef(null)
  const recognitionRef = useRef(null)
  const statusRef = useRef('disconnected')
  const recognizingRef = useRef(false)
  const wasListeningRef = useRef(false)
  const blockRestartRef = useRef(false)

  useEffect(() => { statusRef.current = status }, [status])

  // WebSocket — reconecta automáticamente
  useEffect(() => {
    let closed = false

    function connect() {
      if (closed) return
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => setStatus(s => s === 'disconnected' ? 'idle' : s)

      ws.onclose = () => {
        setStatus('disconnected')
        setTimeout(connect, 3000)
      }

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)

        if (data.type === 'reply') {
          wasListeningRef.current = statusRef.current === 'listening'
          blockRestartRef.current = true
          recognizingRef.current = false
          recognitionRef.current?.stop()
          setMessages(prev => [...prev, { role: 'jarvis', text: data.text }])
          setStatus('speaking')

        } else if (data.type === 'tts_done') {
          blockRestartRef.current = false
          if (wasListeningRef.current) {
            setStatus('listening')
            setTimeout(() => {
              if (!recognizingRef.current && !blockRestartRef.current) {
                try { recognitionRef.current?.start() } catch (_) {}
              }
            }, 400)
          } else {
            setStatus('idle')
          }

        } else if (data.type === 'memory_proposal') {
          setMemoryProposal({
            fact: data.fact,
            category: data.category,
            note_path: data.note_path,
          })
        }
      }
    }

    connect()
    return () => { closed = true; wsRef.current?.close() }
  }, [])

  // Speech Recognition
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return

    const rec = new SR()
    rec.lang = 'es-ES'
    rec.continuous = true
    rec.interimResults = true
    recognitionRef.current = rec

    rec.onstart = () => { recognizingRef.current = true }

    rec.onresult = (e) => {
      let interim = ''
      let final = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript
        else interim += e.results[i][0].transcript
      }
      setTranscript(interim || final)
      if (final.trim()) sendMessage(final.trim())
    }

    rec.onend = () => {
      recognizingRef.current = false
      if (statusRef.current === 'listening' && !blockRestartRef.current) {
        setTimeout(() => {
          if (statusRef.current === 'listening' && !recognizingRef.current && !blockRestartRef.current) {
            try { rec.start() } catch (_) {}
          }
        }, 100)
      }
    }

    rec.onerror = (e) => {
      if (e.error !== 'aborted') setStatus('idle')
    }
  }, [])

  const sendMessage = useCallback((text) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    setMessages(prev => [...prev, { role: 'user', text }])
    setTranscript('')
    setStatus('thinking')
    wsRef.current.send(text)
  }, [])

  const confirmMemory = useCallback((confirmed) => {
    if (!memoryProposal) return
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'memory_confirm',
        confirmed,
        fact: memoryProposal.fact,
        note_path: memoryProposal.note_path,
      }))
    }
    setMemoryProposal(null)
  }, [memoryProposal])

  const toggleListen = useCallback(() => {
    const s = statusRef.current
    if (s === 'disconnected' || s === 'thinking' || s === 'speaking') return
    if (s === 'listening') {
      recognizingRef.current = false
      recognitionRef.current?.stop()
      setStatus('idle')
    } else {
      if (!recognizingRef.current) {
        try { recognitionRef.current?.start() } catch (_) {}
      }
      setStatus('listening')
    }
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { status, messages, transcript, memoryProposal, confirmMemory, toggleListen, clearMessages }
}
