import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';

interface CompetitorNodeProps {
  position: [number, number, number];
}

export function CompetitorNode({ position }: CompetitorNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
    }
  });

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <icosahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          color={hovered ? '#ff4081' : '#3f51b5'}
          metalness={0.5}
          roughness={0.2}
        />
      </mesh>
      <Text
        position={[0, 1.5, 0]}
        fontSize={0.5}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        Competitor
      </Text>
    </group>
  );
} 