import React, { useState } from 'react';
import { ModelCanvas } from '../components/3d/ModelCanvas';
import { UploadPanel } from '../components/3d/UploadPanel';

export const GnnViewer: React.FC = () => {
  const [processedModelUrl, setProcessedModelUrl] = useState<string | undefined>();
  const [pipelineStats, setPipelineStats] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileProcessed = (url: string, stats: any) => {
    // Route through Vite proxy: /processed/xxx.glb → /gnn-api/processed/xxx.glb
    const proxyUrl = url.startsWith('/gnn-api') ? url : `/gnn-api${url.startsWith('/') ? '' : '/'}${url}`;
    setProcessedModelUrl(proxyUrl);
    setPipelineStats(stats);
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-black text-zinc-100 flex flex-col lg:flex-row font-sans">
      {/* Left Panel */}
      <div className="w-full lg:w-[420px] flex flex-col border-b lg:border-b-0 lg:border-r border-zinc-800/50 bg-zinc-950/80 backdrop-blur-3xl z-10 p-6 overflow-y-auto shadow-[4px_0_24px_rgba(0,0,0,0.5)]">
        <div className="mb-8">
          <div className="inline-block px-2 py-1 bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold rounded-md mb-3 tracking-wider">
            MVP
          </div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-500 mb-2">
            Model X — GNN 3D Pipeline
          </h1>
          <p className="text-zinc-400 text-sm leading-relaxed">
            Phase M0/M1 MVP — Topological Normalization & Graph Neural Network Processing
          </p>
        </div>

        <UploadPanel 
          onFileProcessed={handleFileProcessed} 
          isProcessing={isProcessing} 
          setIsProcessing={setIsProcessing} 
        />

        <div className="mt-8 p-5 bg-zinc-900/40 rounded-2xl border border-zinc-800/50 text-sm text-zinc-400">
          <h3 className="text-zinc-200 font-semibold mb-3">Pipeline Architecture</h3>
          <p className="mb-4 text-xs leading-relaxed">
            This tool processes raw 3D geometry through our specialized Graph Neural Network pipeline to extract topological features and normalize mesh structures.
          </p>
          <div className="space-y-2 text-xs font-mono bg-black/50 p-3 rounded-xl border border-zinc-800">
            <div className="text-purple-400">1. Upload</div>
            <div className="pl-4 text-zinc-500">↓ Raw Geometry (.obj, .glb)</div>
            <div className="text-blue-400">2. Normalize</div>
            <div className="pl-4 text-zinc-500">↓ Graph Construction</div>
            <div className="text-indigo-400">3. GNN Inference</div>
            <div className="pl-4 text-zinc-500">↓ Feature Extraction</div>
            <div className="text-teal-400">4. Reconstruct</div>
            <div className="pl-4 text-zinc-500">↓ Formatted Output</div>
            <div className="text-green-400">5. Render</div>
          </div>
        </div>
      </div>

      {/* Right Panel - 3D View */}
      <div className="flex-1 relative bg-zinc-950 min-h-[500px] lg:min-h-0">
        {/* Subtle mesh background pattern */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '32px 32px' }}></div>
        
        <ModelCanvas modelUrl={processedModelUrl} className="absolute inset-0" />
        
        {!processedModelUrl && !isProcessing && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
            <p className="text-zinc-500 font-medium tracking-wide">Upload a model to visualize</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GnnViewer;
