import React, { useRef } from 'react';
import { Group } from 'three';
import { useFrame } from '@react-three/fiber';

interface SceneSetup3DProps {
  children?: React.ReactNode;
}

const SceneSetup3D: React.FC<SceneSetup3DProps> = ({ children }) => {
  const groupRef = useRef<Group>(null);

  return (
    <group ref={groupRef}>
      {/* Basic lighting setup */}
      <ambientLight intensity={0.4} />
      <directionalLight 
        position={[10, 10, 5]} 
        intensity={1.2} 
        castShadow 
        shadow-mapSize-width={1024} 
        shadow-mapSize-height={1024}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
      />
      
      {/* Pass through any children */}
      {children}
    </group>
  );
};

// Export the component as default
export default SceneSetup3D;

// Also export a standalone version of just the lights
export const SceneLights = () => (
  <>
    <ambientLight intensity={0.4} />
    <directionalLight 
      position={[10, 10, 5]} 
      intensity={1.2} 
      castShadow 
      shadow-mapSize-width={1024} 
      shadow-mapSize-height={1024}
      shadow-camera-far={50}
      shadow-camera-left={-10}
      shadow-camera-right={10}
      shadow-camera-top={10}
      shadow-camera-bottom={-10}
    />
  </>
); 