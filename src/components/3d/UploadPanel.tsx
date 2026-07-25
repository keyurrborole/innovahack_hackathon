import React, { useState, useRef, ChangeEvent } from 'react';
import { Upload, FileUp, Loader2, CheckCircle2, XCircle, Box } from 'lucide-react';

interface PipelineStats {
  vertex_count?: number;
  face_count?: number;
  num_nodes?: number;
}

interface UploadPanelProps {
  onFileProcessed: (url: string, stats: PipelineStats) => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
}

const STAGES = ['Upload', 'Normalize', 'GNN Inference', 'Reconstruct', 'Complete'];

export const UploadPanel: React.FC<UploadPanelProps> = ({
  onFileProcessed,
  isProcessing,
  setIsProcessing,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStage, setProcessingStage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    setError(null);
    setStats(null);
    setIsProcessing(true);
    setProcessingStage('Upload');
    
    // Simulate initial progress
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += 5;
      if (progress <= 80) {
        setUploadProgress(progress);
        if (progress > 20) setProcessingStage('Normalize');
        if (progress > 40) setProcessingStage('GNN Inference');
        if (progress > 60) setProcessingStage('Reconstruct');
      }
    }, 200);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/gnn-api/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      setProcessingStage('Complete');

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setStats(data.pipeline_stats || {});
      onFileProcessed(data.processed_url, data.pipeline_stats);
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.message || 'Error processing file');
      setProcessingStage('');
      setUploadProgress(0);
      setIsProcessing(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-700/50 rounded-2xl p-6 text-white w-full shadow-2xl">
      <h2 className="text-xl font-semibold mb-4 text-zinc-100 flex items-center gap-2">
        <Box className="w-5 h-5 text-purple-400" /> Upload 3D Model
      </h2>
      
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all ${
          dragActive ? 'border-purple-500 bg-purple-500/10' : 'border-zinc-600 hover:border-zinc-500 hover:bg-zinc-800/50'
        } ${isProcessing ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isProcessing && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".obj,.glb,.stl,.ply"
          onChange={handleChange}
        />
        
        {isProcessing ? (
          <Loader2 className="w-12 h-12 text-purple-400 animate-spin mb-4" />
        ) : error ? (
          <XCircle className="w-12 h-12 text-red-500 mb-4" />
        ) : (
          <Upload className="w-12 h-12 text-zinc-400 mb-4" />
        )}
        
        <p className="text-zinc-300 font-medium text-center">
          {isProcessing ? 'Processing...' : 'Click or drag and drop to upload'}
        </p>
        <p className="text-zinc-500 text-sm mt-2 text-center">
          Supports .OBJ, .GLB, .STL, .PLY
        </p>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {isProcessing && (
        <div className="mt-6 space-y-4">
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          
          <div className="flex flex-col gap-2 mt-4">
            {STAGES.map((stage, idx) => {
              const isPast = STAGES.indexOf(processingStage) > idx || processingStage === 'Complete';
              const isCurrent = processingStage === stage;
              
              return (
                <div key={stage} className={`flex items-center gap-3 text-sm transition-colors ${isPast || isCurrent ? 'text-zinc-200' : 'text-zinc-600'}`}>
                  {isPast ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-zinc-600" />
                  )}
                  <span className={isCurrent ? 'font-medium' : ''}>{stage}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {stats && processingStage === 'Complete' && (
        <div className="mt-6 p-4 bg-zinc-800/50 rounded-xl border border-zinc-700/50">
          <h3 className="text-sm font-semibold text-zinc-300 mb-3">Model Statistics</h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-zinc-900/50 p-2 rounded-lg border border-zinc-800">
              <p className="text-xs text-zinc-500">Vertices</p>
              <p className="text-sm font-medium text-zinc-200">{stats.vertex_count?.toLocaleString() || '-'}</p>
            </div>
            <div className="bg-zinc-900/50 p-2 rounded-lg border border-zinc-800">
              <p className="text-xs text-zinc-500">Faces</p>
              <p className="text-sm font-medium text-zinc-200">{stats.face_count?.toLocaleString() || '-'}</p>
            </div>
            <div className="bg-zinc-900/50 p-2 rounded-lg border border-zinc-800">
              <p className="text-xs text-zinc-500">Nodes</p>
              <p className="text-sm font-medium text-zinc-200">{stats.num_nodes?.toLocaleString() || '-'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
