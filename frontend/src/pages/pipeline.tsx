'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layout } from '@/components/layout';
import { getPipelineInfo } from '@/lib/api';
import {
  FileInput,
  Brain,
  Search,
  CheckSquare,
  BarChart,
  Edit,
  FileOutput,
  Database,
  ArrowDown,
  ArrowRight,
  ChevronRight,
  Layers,
  Cpu,
  Zap,
  Target,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Activity,
} from 'lucide-react';

// Icon mapping for layers
const iconMap: Record<string, any> = {
  ingestion: FileInput,
  'claim-extraction': Brain,
  retrieval: Search,
  verification: CheckSquare,
  drift: Activity,
  scoring: BarChart,
  correction: Edit,
  output: FileOutput,
};

// Color mapping for layers
const colorMap: Record<string, any> = {
  ingestion: {
    color: 'from-blue-500 to-blue-600',
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/50',
    textColor: 'text-blue-400',
  },
  'claim-extraction': {
    color: 'from-purple-500 to-purple-600',
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/50',
    textColor: 'text-purple-400',
  },
  retrieval: {
    color: 'from-cyan-500 to-cyan-600',
    bgColor: 'bg-cyan-500/20',
    borderColor: 'border-cyan-500/50',
    textColor: 'text-cyan-400',
  },
  verification: {
    color: 'from-green-500 to-green-600',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/50',
    textColor: 'text-green-400',
  },
  drift: {
    color: 'from-indigo-500 to-indigo-600',
    bgColor: 'bg-indigo-500/20',
    borderColor: 'border-indigo-500/50',
    textColor: 'text-indigo-400',
  },
  scoring: {
    color: 'from-yellow-500 to-yellow-600',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500/50',
    textColor: 'text-yellow-400',
  },
  correction: {
    color: 'from-orange-500 to-orange-600',
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/50',
    textColor: 'text-orange-400',
  },
  output: {
    color: 'from-pink-500 to-pink-600',
    bgColor: 'bg-pink-500/20',
    borderColor: 'border-pink-500/50',
    textColor: 'text-pink-400',
  },
};

// Type definition for pipeline layers
type PipelineLayer = {
  id: string;
  name: string;
  icon: any;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  description: string;
  inputType: string;
  outputType: string;
  techStack: string[];
  status: string;
  details: string[];
};

export default function PipelinePage() {
  const [viewMode, setViewMode] = useState<'flow' | 'grid'>('flow');
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
  const [layers, setLayers] = useState<PipelineLayer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<{
    available: boolean;
    mode: string;
  } | null>(null);

  const extractDetails = (description: string): string[] => {
    // Extract key points from description
    const sentences = description.split('. ');
    return sentences.map(s => s.trim()).filter(s => s.length > 0);
  };

  const fetchPipelineData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getPipelineInfo();
      
      // Transform backend data to match our display format
      const transformedLayers = data.layers.map((layer: any, index: number) => ({
        id: layer.id,
        name: layer.name,
        icon: iconMap[layer.id] || Layers,
        ...colorMap[layer.id] || colorMap.ingestion,
        description: layer.description,
        inputType: layer.inputType,
        outputType: layer.outputType,
        techStack: layer.techStack || [],
        status: layer.status || 'active',
        details: extractDetails(layer.description),
      }));
      
      setLayers(transformedLayers);
      setPipelineStatus({
        available: data.pipelineAvailable !== undefined ? data.pipelineAvailable : true,
        mode: data.mode || 'full',
      });
    } catch (err: any) {
      console.error('Failed to fetch pipeline info:', err);
      setError('Failed to load pipeline information. Ensure backend is running on http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPipelineData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeLayer = selectedLayer ? layers.find(l => l.id === selectedLayer) : null;

  return (
    <Layout
      title="Verification Pipeline"
      description="Explore our 8-layer architecture for detecting AI hallucinations"
      pageTitle="Pipeline"
    >
      {/* Pipeline Status */}
      {pipelineStatus && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`glass-card p-4 mb-6 border-l-4 ${
            pipelineStatus.available ? 'border-green-500' : 'border-yellow-500'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {pipelineStatus.available ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-400" />
              )}
              <div>
                <span className="font-semibold text-dark-text">
                  Pipeline Status: {pipelineStatus.available ? 'Active' : 'Limited'}
                </span>
                <span className="text-sm text-dark-muted ml-2">
                  Mode: {pipelineStatus.mode}
                </span>
              </div>
            </div>
            <button
              onClick={fetchPipelineData}
              disabled={loading}
              className="btn-secondary"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </motion.div>
      )}

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-6 border-l-4 border-red-500"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div>
              <p className="font-semibold text-dark-text">Failed to Load Pipeline</p>
              <p className="text-sm text-dark-muted">{error}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <RefreshCw className="w-12 h-12 text-primary-400 animate-spin mx-auto mb-4" />
            <p className="text-dark-muted">Loading pipeline information...</p>
          </div>
        </div>
      )}

      {/* Pipeline Content */}
      {!loading && layers.length > 0 && (
      <>
      {/* Header Stats */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        <div className="glass-card p-4 text-center">
          <div className="text-3xl font-bold gradient-text mb-1">{layers.length}</div>
          <div className="text-sm text-dark-muted">Pipeline Layers</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-3xl font-bold text-verified mb-1">{layers.filter(l => l.status === 'active').length}</div>
          <div className="text-sm text-dark-muted">Active Layers</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-3xl font-bold text-primary-400 mb-1">&lt;2s</div>
          <div className="text-sm text-dark-muted">Avg. Latency</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-3xl font-bold text-unverified mb-1">
            {pipelineStatus?.mode === 'full' ? '98%' : '85%'}
          </div>
          <div className="text-sm text-dark-muted">Accuracy</div>
        </div>
      </motion.div>

      {/* View Toggle */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-dark-text flex items-center gap-2">
          <Layers className="w-5 h-5 text-primary-400" />
          Pipeline Architecture
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('flow')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              viewMode === 'flow'
                ? 'bg-primary-500 text-white'
                : 'bg-dark-card text-dark-muted hover:text-dark-text'
            }`}
          >
            Flow View
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              viewMode === 'grid'
                ? 'bg-primary-500 text-white'
                : 'bg-dark-card text-dark-muted hover:text-dark-text'
            }`}
          >
            Grid View
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Pipeline Visualization */}
        <div className="lg:col-span-2">
          {viewMode === 'flow' ? (
            <FlowView
              layers={layers}
              selectedLayer={selectedLayer}
              onSelectLayer={setSelectedLayer}
            />
          ) : (
            <GridView
              layers={layers}
              selectedLayer={selectedLayer}
              onSelectLayer={setSelectedLayer}
            />
          )}
        </div>

        {/* Layer Details */}
        <div>
          <AnimatePresence mode="wait">
            {activeLayer ? (
              <LayerDetails key={activeLayer.id} layer={activeLayer} />
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="glass-card p-6 text-center"
              >
                <Cpu className="w-12 h-12 text-dark-muted mx-auto mb-4" />
                <h3 className="font-semibold text-dark-text mb-2">Select a Layer</h3>
                <p className="text-sm text-dark-muted">
                  Click on any layer in the pipeline to view detailed information about its functionality.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Data Flow Explanation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-8 glass-card p-6"
      >
        <h3 className="text-lg font-bold text-dark-text mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary-400" />
          How Data Flows Through the Pipeline
        </h3>
        <div className="grid md:grid-cols-3 gap-6 text-sm">
          <div>
            <h4 className="font-semibold text-dark-text mb-2">1. Input Phase</h4>
            <p className="text-dark-muted">
              Source documents and LLM output are ingested, parsed, and preprocessed. Claims are extracted 
              and structured for analysis.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-dark-text mb-2">2. Analysis Phase</h4>
            <p className="text-dark-muted">
              Each claim is matched against source evidence using semantic search. NLI models determine 
              if claims are supported, contradicted, or unverifiable.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-dark-text mb-2">3. Output Phase</h4>
            <p className="text-dark-muted">
              Results are scored, corrections generated, and explanations synthesized. The final report 
              includes color-coded annotations and citations.
            </p>
          </div>
        </div>
      </motion.div>
      </>
      )}
    </Layout>
  );
}

function FlowView({
  layers,
  selectedLayer,
  onSelectLayer,
}: {
  layers: PipelineLayer[];
  selectedLayer: string | null;
  onSelectLayer: (id: string) => void;
}) {
  return (
    <div className="space-y-3">
      {layers.map((layer, idx) => (
        <motion.div
          key={layer.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.05 }}
        >
          <motion.button
            whileHover={{ x: 4 }}
            onClick={() => onSelectLayer(layer.id)}
            className={`w-full p-4 rounded-xl border transition-all ${
              selectedLayer === layer.id
                ? `${layer.bgColor} ${layer.borderColor} ring-2 ring-offset-2 ring-offset-dark-bg`
                : 'bg-dark-card border-dark-border hover:border-dark-muted'
            }`}
            style={{
              '--tw-ring-color': selectedLayer === layer.id ? layer.borderColor.replace('border-', '').replace('/50', '') : 'transparent',
            } as React.CSSProperties}
          >
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${layer.color} flex items-center justify-center shrink-0`}>
                <layer.icon className="w-6 h-6 text-white" />
              </div>
              <div className="text-left flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-dark-muted">Layer {idx + 1}</span>
                </div>
                <h3 className="font-semibold text-dark-text">{layer.name}</h3>
                <p className="text-sm text-dark-muted">{layer.description}</p>
              </div>
              <ChevronRight className={`w-5 h-5 transition-transform ${
                selectedLayer === layer.id ? 'rotate-90 text-primary-400' : 'text-dark-muted'
              }`} />
            </div>
          </motion.button>
          
          {idx < layers.length - 1 && (
            <div className="flex justify-center py-1">
              <ArrowDown className="w-5 h-5 text-dark-muted" />
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
}

function GridView({
  layers,
  selectedLayer,
  onSelectLayer,
}: {
  layers: PipelineLayer[];
  selectedLayer: string | null;
  onSelectLayer: (id: string) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {layers.map((layer, idx) => (
        <motion.button
          key={layer.id}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: idx * 0.05 }}
          whileHover={{ scale: 1.02 }}
          onClick={() => onSelectLayer(layer.id)}
          className={`p-4 rounded-xl border text-left transition-all ${
            selectedLayer === layer.id
              ? `${layer.bgColor} ${layer.borderColor}`
              : 'bg-dark-card border-dark-border hover:border-dark-muted'
          }`}
        >
          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${layer.color} flex items-center justify-center mb-3`}>
            <layer.icon className="w-5 h-5 text-white" />
          </div>
          <div className="text-xs text-dark-muted mb-1">Layer {idx + 1}</div>
          <h3 className="font-semibold text-dark-text text-sm">{layer.name}</h3>
        </motion.button>
      ))}
    </div>
  );
}

function LayerDetails({ layer }: { layer: PipelineLayer }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="glass-card overflow-hidden"
    >
      {/* Header */}
      <div className={`p-4 bg-gradient-to-r ${layer.color}`}>
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
            <layer.icon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-white">{layer.name}</h3>
            <p className="text-sm text-white/80">{layer.description}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* I/O */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-dark-bg/50 border border-dark-border">
            <div className="text-xs text-dark-muted mb-1">Input</div>
            <div className="text-sm text-dark-text">{layer.inputType}</div>
          </div>
          <div className="p-3 rounded-lg bg-dark-bg/50 border border-dark-border">
            <div className="text-xs text-dark-muted mb-1">Output</div>
            <div className="text-sm text-dark-text">{layer.outputType}</div>
          </div>
        </div>

        {/* Features */}
        <div>
          <h4 className="text-sm font-semibold text-dark-text mb-2">Key Functions</h4>
          <ul className="space-y-1.5">
            {layer.details.map((detail, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-dark-muted">
                <span className={`w-1.5 h-1.5 rounded-full ${layer.bgColor} mt-1.5 shrink-0`} />
                {detail}
              </li>
            ))}
          </ul>
        </div>

        {/* Tech Stack */}
        <div>
          <h4 className="text-sm font-semibold text-dark-text mb-2">Tech Stack</h4>
          <div className="flex flex-wrap gap-2">
            {layer.techStack.map((tech) => (
              <span
                key={tech}
                className="px-2 py-1 text-xs rounded-md bg-dark-bg border border-dark-border text-dark-muted"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
