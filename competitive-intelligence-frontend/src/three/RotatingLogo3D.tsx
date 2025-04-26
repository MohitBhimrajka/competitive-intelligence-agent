import { useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { Group } from 'three';

interface RotatingLogo3DProps {
  rotationSpeed?: number;
  position?: [number, number, number];
  scale?: number;
}

const RotatingLogo3D: React.FC<RotatingLogo3DProps> = ({
  rotationSpeed = 0.01,
  position = [0, 0, 0],
  scale = 1
}) => {
  const groupRef = useRef<Group>(null);
  
  // Load the 3D model
  const { scene } = useGLTF('/assets/logo.glb');
  
  // Clone the scene to avoid shared material issues
  const clonedScene = scene.clone();
  
  // Apply rotation on each frame
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * rotationSpeed;
    }
  });

  return (
    <group ref={groupRef} position={position} scale={scale}>
      <primitive object={clonedScene} />
    </group>
  );
};

// Pre-load the model to avoid loading delay during component render
useGLTF.preload('/assets/logo.glb');

export default RotatingLogo3D; 