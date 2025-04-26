import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Box } from '@react-three/drei';
import { a, useSpring } from '@react-spring/three';
import * as THREE from 'three';
import ThreeCanvas from '../../three/ThreeCanvas';
import SceneSetup3D from '../../three/SceneSetup3D';
import usePrefersReducedMotion from '../../hooks/usePrefersReducedMotion';

interface DataPoint {
  id: string;
  label: string;
  value: number;
  color?: string;
}

interface DataVisualization3DProps {
  data: DataPoint[];
  title?: string;
  maxBarHeight?: number;
  spacing?: number;
}

// Animated bar component
const AnimatedBar = ({ 
  x, 
  value, 
  label, 
  color, 
  maxHeight,
  animated = true
}: { 
  x: number; 
  value: number; 
  label: string; 
  color: string;
  maxHeight: number;
  animated?: boolean;
}) => {
  // Scale the height based on value and maxHeight
  const height = value * maxHeight;
  
  // Create the spring animation for the bar's scale
  const { scaleY } = useSpring({
    from: { scaleY: 0 },
    to: { scaleY: 1 },
    delay: x * 100, // Stagger the animations
    config: { mass: 1, tension: 280, friction: 60 },
    immediate: !animated
  });
  
  // Use animated mesh from react-spring
  const AnimatedBox = a(Box);
  
  return (
    <group position={[x, 0, 0]}>
      <AnimatedBox 
        args={[0.8, height, 0.8]} 
        position={[0, height / 2, 0]}
        scale-y={scaleY}
      >
        <meshStandardMaterial color={color} />
      </AnimatedBox>
      
      <Text
        position={[0, -0.5, 0]}
        color="white"
        fontSize={0.3}
        anchorX="center"
        anchorY="top"
      >
        {label}
      </Text>
      
      <Text
        position={[0, height + 0.5, 0]}
        color="white"
        fontSize={0.3}
        anchorX="center"
        anchorY="bottom"
      >
        {value.toFixed(1)}
      </Text>
    </group>
  );
};

// Main visualization component
const BarChart3D: React.FC<DataVisualization3DProps> = ({ 
  data, 
  title = "Data Visualization",
  maxBarHeight = 5,
  spacing = 1.5
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  
  // Add a subtle group rotation for visual interest
  useFrame(({ clock }) => {
    if (groupRef.current && !prefersReducedMotion) {
      groupRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.2) * 0.1;
    }
  });
  
  // Calculate the total width for centering
  const totalWidth = (data.length - 1) * spacing;
  const startX = -totalWidth / 2;
  
  return (
    <group ref={groupRef}>
      {/* Title */}
      <Text
        position={[0, maxBarHeight + 1.5, 0]}
        color="white"
        fontSize={0.5}
        anchorX="center"
        anchorY="bottom"
      >
        {title}
      </Text>
      
      {/* Data bars */}
      {data.map((item, index) => (
        <AnimatedBar
          key={item.id}
          x={startX + index * spacing}
          value={item.value}
          label={item.label}
          color={item.color || getColorForIndex(index)}
          maxHeight={maxBarHeight}
          animated={!prefersReducedMotion}
        />
      ))}
      
      {/* Floor plane for reference */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[totalWidth + 5, totalWidth + 5]} />
        <meshStandardMaterial color="#1A202C" transparent opacity={0.5} />
      </mesh>
    </group>
  );
};

// Helper function to get colors for bars
const getColorForIndex = (index: number): string => {
  const colors = [
    "#4FD1C5", // teal
    "#3182CE", // blue
    "#E53E3E", // red
    "#38A169", // green
    "#805AD5", // purple
    "#DD6B20", // orange
    "#D53F8C", // pink
    "#718096", // gray
  ];
  
  return colors[index % colors.length];
};

// Full component with canvas wrapper
const DataVisualization3D: React.FC<DataVisualization3DProps> = (props) => {
  const defaultData = [
    { id: '1', label: 'A', value: 5 },
    { id: '2', label: 'B', value: 3 },
    { id: '3', label: 'C', value: 7 },
    { id: '4', label: 'D', value: 2 },
    { id: '5', label: 'E', value: 4 }
  ];

  const data = props.data || defaultData;
  const otherProps = { ...props, data };
  
  const prefersReducedMotion = usePrefersReducedMotion();
  
  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ThreeCanvas>
        <SceneSetup3D>
          <BarChart3D {...otherProps} />
        </SceneSetup3D>
      </ThreeCanvas>
      
      {prefersReducedMotion && (
        <div 
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'rgba(0,0,0,0.7)',
            color: 'white',
            padding: '8px',
            textAlign: 'center',
            fontSize: '12px'
          }}
        >
          3D animations disabled due to reduced motion preference
        </div>
      )}
    </div>
  );
};

export default DataVisualization3D; 