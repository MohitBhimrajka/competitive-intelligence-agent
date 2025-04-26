import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Suspense } from 'react';
import { CompetitorNode } from './CompetitorNode';

export function Dashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="col-span-1 md:col-span-2 bg-card rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold mb-4">Competitive Landscape</h2>
        <div className="h-[500px] bg-muted/20 rounded-lg overflow-hidden">
          <Canvas camera={{ position: [0, 0, 10], fov: 50 }}>
            <Suspense fallback={null}>
              <ambientLight intensity={0.5} />
              <pointLight position={[10, 10, 10]} />
              <CompetitorNode position={[0, 0, 0]} />
              <OrbitControls enablePan={false} />
            </Suspense>
          </Canvas>
        </div>
      </div>

      <div className="bg-card rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-bold mb-4">Recent Updates</h2>
        <div className="space-y-4">
          {/* Add recent updates here */}
        </div>
      </div>

      <div className="bg-card rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-bold mb-4">Key Metrics</h2>
        <div className="space-y-4">
          {/* Add key metrics here */}
        </div>
      </div>
    </div>
  );
} 