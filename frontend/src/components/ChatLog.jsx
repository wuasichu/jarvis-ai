import { useEffect, useRef } from 'react'
import './ChatLog.css'

export default function ChatLog({ messages, onClear }) {
  const endRef = useRef()

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!messages.length) return null

  return (
    <div className="chat-log">
      <button className="clear-btn" onClick={onClear}>Limpiar</button>
      {messages.map((m, i) => (
        <div key={i} className={`msg msg--${m.role}`}>
          {m.text}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}
