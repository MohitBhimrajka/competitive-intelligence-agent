import { useState, useRef, useEffect, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { Canvas } from '@react-three/fiber';
import { Stars, useTexture, Float, OrbitControls } from '@react-three/drei';
import { motion } from 'framer-motion';
import { HeroScene } from './HeroScene';

export function LandingPage() {
  const [companyName, setCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim()) return;
    
    setIsLoading(true);
    // Simulate API call/loading
    setTimeout(() => {
      setIsLoading(false);
      navigate('/dashboard');
    }, 3000);
  };

  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  return (
    <div className="relative h-screen w-full bg-black overflow-hidden">
      {/* 3D Background */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
          <Suspense fallback={null}>
            <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
            <HeroScene isLoading={isLoading} />
            <ambientLight intensity={0.1} />
            <directionalLight position={[0, 10, 5]} intensity={1} />
          </Suspense>
        </Canvas>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center h-full px-4 text-white">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-8"
        >
          <h1 className="text-5xl md:text-7xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
            Competitive Intelligence Agent
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto">
            Unveil strategic insights from competitor activities, market trends, and hidden data patterns in real-time.
          </p>
        </motion.div>

        <motion.form
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          onSubmit={handleSubmit}
          className="w-full max-w-md relative"
        >
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-600 to-purple-600 rounded-lg blur opacity-75 group-hover:opacity-100 transition duration-1000 group-hover:duration-200 animate-pulse"></div>
            <div className="relative flex items-center">
              <input
                ref={searchInputRef}
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Enter your company name..."
                className="w-full px-6 py-4 bg-black border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !companyName.trim()}
                className="absolute right-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-md text-white font-medium disabled:opacity-50"
              >
                {isLoading ? 'Loading...' : 'Analyze'}
              </button>
            </div>
          </div>
        </motion.form>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-8 text-center"
          >
            <div className="text-xl text-blue-400 font-medium mb-2">Analyzing Competitive Landscape</div>
            <div className="text-sm text-gray-400">Discovering insights for {companyName}</div>
          </motion.div>
        )}
      </div>
    </div>
  );
} 