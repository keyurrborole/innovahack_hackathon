import React, { useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Grid, Center, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

interface ModelProps {
  url: string;
}

const Model: React.FC<ModelProps> = ({ url }) => {
  const { scene } = useGLTF(url);

  useEffect(() => {
    return () => {
      useGLTF.clear(url);
    };
  }, [url]);

  return <primitive object={scene} />;
};

interface ModelCanvasProps {
  modelUrl?: string;
  className?: string;
}

export const ModelCanvas: React.FC<ModelCanvasProps> = ({ modelUrl, className = '' }) => {
  return (
    <div className={`w-full h-full bg-zinc-950 rounded-xl overflow-hidden ${className}`}>
      <Canvas camera={{ position: [3, 3, 3], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} castShadow />
        <Environment preset="studio" />
        <OrbitControls enableDamping makeDefault />
        <Grid args={[20, 20]} cellColor="#6f6f6f" sectionColor="#9d4b4b" fadeDistance={30} />
        <React.Suspense fallback={null}>
          {modelUrl ? (
            <Center>
              <Model url={modelUrl} />
            </Center>
          ) : null}
        </React.Suspense>
      </Canvas>
    </div>
  );
};
