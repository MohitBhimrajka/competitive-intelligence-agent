import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, MeshWobbleMaterial, Text, RoundedBox } from '@react-three/drei';
import { Vector3, Mesh, Group, MathUtils } from 'three';
import { useSpring, animated, config } from '@react-spring/three';

type HeroSceneProps = {
  isLoading: boolean;
};

export function HeroScene({ isLoading }: HeroSceneProps) {
  const sphereRef = useRef<Mesh>(null);
  const groupRef = useRef<Group>(null);
  const boxesRef = useRef<Group>(null);
  
  // Create animated boxes for the data visualization effect
  const count = 50;
  const boxes = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      position: [
        MathUtils.randFloatSpread(20),
        MathUtils.randFloatSpread(20),
        MathUtils.randFloatSpread(20)
      ] as [number, number, number],
      scale: Math.random() * 0.4 + 0.1,
      rotation: [0, 0, 0] as [number, number, number],
      color: i % 2 === 0 ? '#4c72b0' : '#8a3ffc'
    }));
  }, []);

  // Spring animation for the main sphere
  const { distort, scale } = useSpring({
    distort: isLoading ? 1 : 0.4,
    scale: isLoading ? 1.5 : 1,
    config: config.molasses
  });

  // Animation loop
  useFrame((state, delta) => {
    if (sphereRef.current) {
      sphereRef.current.rotation.x += delta * 0.1;
      sphereRef.current.rotation.y += delta * 0.15;
    }

    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.05;
    }
    
    if (boxesRef.current && boxesRef.current.children.length > 0) {
      boxesRef.current.children.forEach((box, i) => {
        if (isLoading) {
          // When loading, move boxes towards the center in a spiral pattern
          const time = state.clock.getElapsedTime();
          const distance = isLoading ? 5 : 20;
          const speed = 0.5 + i * 0.01;
          
          const targetPosition = new Vector3(
            Math.sin(time * speed + i) * distance,
            Math.cos(time * speed + i) * distance * 0.5,
            Math.sin(time * 0.5 + i) * distance
          );
          
          box.position.lerp(targetPosition, delta);
          box.rotation.x += delta * (i % 3 === 0 ? 1 : -1);
          box.rotation.z += delta * (i % 2 === 0 ? 0.5 : -0.5);
        } else {
          // When not loading, slowly drift back to original positions
          box.position.x += Math.sin(state.clock.getElapsedTime() * 0.2 + i) * delta * 0.2;
          box.position.y += Math.cos(state.clock.getElapsedTime() * 0.2 + i) * delta * 0.2;
          box.position.z += Math.sin(state.clock.getElapsedTime() * 0.2 + i + Math.PI/2) * delta * 0.2;
        }
      });
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Main animated sphere */}
      <animated.mesh ref={sphereRef} scale={scale}>
        <sphereGeometry args={[1.2, 64, 64]} />
        <animated.meshDistortMaterial
          color="#4c00b0"
          attach="material"
          distort={distort}
          speed={3}
          metalness={0.6}
          roughness={0.2}
        />
      </animated.mesh>
      
      {/* Outer ring */}
      <group ref={groupRef}>
        <Sphere args={[3, 24, 24]} position={[0, 0, 0]}>
          <MeshWobbleMaterial
            color="#1a237e"
            factor={0.2}
            speed={1}
            transparent
            opacity={0.1}
            wireframe
          />
        </Sphere>
      </group>
      
      {/* Data visualization boxes */}
      <group ref={boxesRef}>
        {boxes.map((box, i) => (
          <RoundedBox 
            key={i}
            args={[box.scale, box.scale, box.scale]}
            radius={0.1}
            position={box.position}
            rotation={box.rotation}
          >
            <meshStandardMaterial
              color={box.color}
              metalness={0.6}
              roughness={0.2}
              transparent
              opacity={0.8}
            />
          </RoundedBox>
        ))}
      </group>

      {/* Text that appears during loading */}
      {isLoading && (
        <Text
          position={[0, -2.5, 0]}
          fontSize={0.5}
          color="#4fc3f7"
          font="https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2"
          anchorX="center"
          anchorY="middle"
          material-metalness={0.8}
          material-roughness={0.2}
        >
          Analyzing...
        </Text>
      )}
    </group>
  );
} 