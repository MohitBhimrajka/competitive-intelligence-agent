import { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import { inSphere } from 'maath/random';
import * as THREE from 'three';

interface ParticleBackgroundProps {
  count?: number;
  radius?: number;
  color?: string | THREE.Color;
  size?: number;
  rotationSpeed?: number;
}

const ParticleBackground3D: React.FC<ParticleBackgroundProps> = ({
  count = 1500,
  radius = 1.5,
  color = '#ffffff',
  size = 0.01,
  rotationSpeed = 0.0005
}) => {
  const pointsRef = useRef<THREE.Points>(null);
  
  // Generate random points within a sphere
  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    inSphere(positions, { radius });
    return positions;
  }, [count, radius]);

  // Rotate the points on each frame
  useFrame((state, delta) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.x += delta * rotationSpeed;
      pointsRef.current.rotation.y += delta * rotationSpeed * 1.5;
    }
  });

  return (
    <Points ref={pointsRef} positions={particles} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color={color}
        size={size}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
};

export default ParticleBackground3D; 