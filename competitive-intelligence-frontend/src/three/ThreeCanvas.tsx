import React, { Suspense, ReactNode } from 'react';
import { Canvas } from '@react-three/fiber';
import { Html } from '@react-three/drei';

interface ThreeCanvasProps {
  children: ReactNode;
}

const ThreeCanvas: React.FC<ThreeCanvasProps> = ({ children }) => {
  return (
    <Canvas shadows dpr={[1, 2]} frameloop="demand">
      <Suspense fallback={<Html center>Loading…</Html>}>
        {children}
      </Suspense>
    </Canvas>
  );
};

export default ThreeCanvas; 