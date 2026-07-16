import { useEffect } from 'react'

const CATEGORY_ICON = {
  personas: '👤',
  proyectos: '📁',
  preferencias: '⭐',
  recordatorios: '📅',
  otros: '💡',
}

export default function MemoryToast({ proposal, onConfirm }) {
  // Auto-descartar tras 12 segundos sin respuesta
  useEffect(() => {
    if (!proposal) return
    const t = setTimeout(() => onConfirm(false), 12000)
    return () => clearTimeout(t)
  }, [proposal, onConfirm])

  if (!proposal) return null

  const icon = CATEGORY_ICON[proposal.category] ?? '💡'

  return (
    <div style={{
      position: 'fixed',
      bottom: '2rem',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(15, 23, 42, 0.92)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(99, 102, 241, 0.3)',
      borderRadius: '12px',
      padding: '0.75rem 1rem',
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      maxWidth: '420px',
      width: 'calc(100vw - 2rem)',
      zIndex: 100,
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    }}>
      <span style={{ fontSize: '1.1rem' }}>{icon}</span>
      <span style={{
        flex: 1,
        fontSize: '0.82rem',
        color: '#cbd5e1',
        lineHeight: 1.4,
      }}>
        {proposal.fact}
      </span>
      <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0 }}>
        <button
          onClick={() => onConfirm(true)}
          style={{
            background: 'rgba(99, 102, 241, 0.8)',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '0.3rem 0.7rem',
            fontSize: '0.78rem',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Guardar
        </button>
        <button
          onClick={() => onConfirm(false)}
          style={{
            background: 'rgba(255,255,255,0.06)',
            color: '#94a3b8',
            border: 'none',
            borderRadius: '6px',
            padding: '0.3rem 0.7rem',
            fontSize: '0.78rem',
            cursor: 'pointer',
          }}
        >
          No
        </button>
      </div>
    </div>
  )
}
