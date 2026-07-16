import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

const CONFIG = {
  disconnected: { color: '#334155', emissive: '#0f172a', distort: 0.05, speed: 0.5 },
  idle:         { color: '#3b82f6', emissive: '#1d4ed8', distort: 0.15, speed: 1.0 },
  listening:    { color: '#10b981', emissive: '#059669', distort: 0.35, speed: 2.5 },
  thinking:     { color: '#f59e0b', emissive: '#d97706', distort: 0.45, speed: 3.5 },
  speaking:     { color: '#bae6fd', emissive: '#38bdf8', distort: 0.55, speed: 4.5 },
}

const LERP = 0.06

export default function BlobOrb({ status }) {
  const meshRef = useRef()
  const matRef = useRef()

  const currentColor = useRef(new THREE.Color(CONFIG.idle.color))
  const currentEmissive = useRef(new THREE.Color(CONFIG.idle.emissive))
  const currentDistort = useRef(CONFIG.idle.distort)
  const currentSpeed = useRef(CONFIG.idle.speed)

  useFrame((_, delta) => {
    const cfg = CONFIG[status] ?? CONFIG.idle

    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.2
    }

    if (matRef.current) {
      const targetColor = new THREE.Color(cfg.color)
      const targetEmissive = new THREE.Color(cfg.emissive)

      currentColor.current.lerp(targetColor, LERP)
      currentEmissive.current.lerp(targetEmissive, LERP)
      currentDistort.current = THREE.MathUtils.lerp(currentDistort.current, cfg.distort, LERP)
      currentSpeed.current = THREE.MathUtils.lerp(currentSpeed.current, cfg.speed, LERP)

      matRef.current.color.copy(currentColor.current)
      matRef.current.emissive.copy(currentEmissive.current)
      matRef.current.distort = currentDistort.current
      matRef.current.speed = currentSpeed.current
    }
  })

  const init = CONFIG[status] ?? CONFIG.idle

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1.2, 6]} />
      <MeshDistortMaterial
        ref={matRef}
        color={init.color}
        emissive={init.emissive}
        emissiveIntensity={0.8}
        distort={init.distort}
        speed={init.speed}
        roughness={0.2}
        metalness={0.3}
      />
    </mesh>
  )
}
