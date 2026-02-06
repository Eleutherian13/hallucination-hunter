'use client';

import { useState } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import { Layout } from '@/components/layout';
import { FileUpload, TextInput, ProgressSteps, LoadingSpinner } from '@/components/ui';
import { verifyDocument } from '@/lib/api';
import {
  Upload,
  FileText,
  Play,
  Sparkles,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';

const pipelineSteps = [
  { name: 'Upload', status: 'pending' as const },
  { name: 'Ingest', status: 'pending' as const },
  { name: 'Extract', status: 'pending' as const },
  { name: 'Retrieve', status: 'pending' as const },
  { name: 'Verify', status: 'pending' as const },
  { name: 'Score', status: 'pending' as const },
  { name: 'Complete', status: 'pending' as const },
];

export default function VerifyPage() {
  const router = useRouter();
  const [sourceFiles, setSourceFiles] = useState<File[]>([]);
  const [llmOutput, setLlmOutput] = useState('');
  const [inputMethod, setInputMethod] = useState<'paste' | 'upload'>('paste');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState(pipelineSteps);
  const [error, setError] = useState<string | null>(null);

  const hasSourceFiles = sourceFiles.length > 0;
  const hasLlmOutput = llmOutput.trim().length > 0;
  const canVerify = hasSourceFiles && hasLlmOutput && !isProcessing;

  const handleVerify = async () => {
    if (!canVerify) return;
    
    setIsProcessing(true);
    setError(null);
    setProgress(0);
    setCurrentStep(0);
    
    try {
      // Update progress through pipeline steps
      const stepIntervals = [0, 15, 30, 50, 70, 85, 100];
      const stepNames = ['Uploading files...', 'Ingesting documents...', 'Extracting claims...', 
                         'Retrieving evidence...', 'Verifying claims...', 'Scoring results...', 'Complete!'];
      
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const nextStep = Math.floor((prev / 100) * steps.length);
          if (nextStep < steps.length) {
            setCurrentStep(nextStep);
            setSteps(prevSteps => prevSteps.map((step, idx) => ({
              ...step,
              status: idx < nextStep ? 'completed' : idx === nextStep ? 'processing' : 'pending'
            })));
          }
          return Math.min(prev + 5, 95);
        });
      }, 300);

      // Call the actual backend API
      // Load settings from localStorage
      const storedSettings = localStorage.getItem('verification_settings');
      const settings = storedSettings ? JSON.parse(storedSettings) : {
        confidenceThreshold: 0.7,
        enableCorrections: true,
        enableSemanticMatching: true,
        maxClaimsPerDocument: 50,
      };

      const result = await verifyDocument(
        sourceFiles,
        llmOutput,
        {
          confidence_threshold: settings.confidenceThreshold,
          enable_corrections: settings.enableCorrections,
          enable_semantic_matching: settings.enableSemanticMatching,
          max_claims: settings.maxClaimsPerDocument,
        },
        (prog, step) => {
          setProgress(Math.max(progress, prog));
        }
      );

      clearInterval(progressInterval);
      
      // Mark all steps as completed
      setProgress(100);
      setSteps(prev => prev.map(step => ({ ...step, status: 'completed' as const })));
      
      // Store result with ID-based key for results page
      console.log('Storing verification result:', result);
      sessionStorage.setItem(`verification_result_${result.id}`, JSON.stringify(result));
      sessionStorage.setItem('latestVerificationResult', JSON.stringify(result));
      
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Navigating to results page with ID:', result.id);
      await router.push(`/results?id=${result.id}`);
      
    } catch (err: any) {
      console.error('Verification error:', err);
      setError(err.message || 'Verification failed. Please ensure the backend is running on http://localhost:8000');
      setIsProcessing(false);
      setSteps(pipelineSteps);
      setProgress(0);
    }
  };

  const loadDemoData = () => {
    // Create a demo text file
    const demoText = `Type 2 diabetes mellitus is a chronic metabolic disorder characterized by hyperglycemia resulting from defects in insulin secretion, insulin action, or both.

The patient should be evaluated for diabetes complications at the time of diagnosis and annually thereafter. Key areas include retinopathy screening, nephropathy assessment, and neuropathy evaluation.

For most non-pregnant adults, a reasonable HbA1c goal is <7.0%. A more stringent goal of <6.5% may be appropriate for selected individuals.

Metformin remains the first-line pharmacological agent unless contraindicated. It should be initiated at the time of diagnosis along with lifestyle modifications.

GLP-1 receptor agonists and SGLT2 inhibitors have demonstrated cardiovascular and renal protective effects and should be considered for patients with established cardiovascular disease.

Blood pressure targets for patients with diabetes should be <130/80 mmHg. First-line antihypertensive agents include ACE inhibitors or ARBs.

Statin therapy is recommended for all adults with diabetes aged 40-75 years. High-intensity statin therapy should be used for patients with established ASCVD.`;

    const blob = new Blob([demoText], { type: 'text/plain' });
    const file = new File([blob], 'ADA_Guidelines_2024.txt', { type: 'text/plain' });
    setSourceFiles([file]);
    
    setLlmOutput(`Based on the ADA Guidelines for Type 2 Diabetes Management 2024, here is a summary of the key recommendations:

For diagnosis, diabetes is confirmed when HbA1c is ≥6.5% or fasting glucose is ≥126 mg/dL. Patients should be screened for complications annually including retinopathy and nephropathy.

The recommended HbA1c target for most adults is <7.0%, though this should be individualized based on patient factors.

Metformin is the recommended first-line medication for Type 2 Diabetes unless there are contraindications. It should be started at diagnosis along with lifestyle changes.

Blood pressure targets for diabetic patients should be <140/90 mmHg according to the guidelines. ACE inhibitors or ARBs are preferred for patients with kidney disease.

Sulfonylureas are the preferred second-line agents for all diabetic patients regardless of cardiovascular history.

All patients aged 40-75 should receive statin therapy for cardiovascular protection. Diabetes self-management education should be provided at diagnosis.`);
  };

  return (
    <Layout
      title="Verify Documents"
      description="Upload source documents and LLM output to check for hallucinations"
      pageTitle="Verify"
    >
      {/* Info Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 mb-8 border-l-4 border-primary-500"
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5 text-primary-400" />
          </div>
          <div>
            <h3 className="font-semibold text-dark-text mb-1">How It Works</h3>
            <p className="text-sm text-dark-muted leading-relaxed">
              Upload your source documents (medical guidelines, legal acts, technical manuals) and the 
              LLM-generated summary you want to verify. Our 8-layer pipeline will analyze each claim, 
              highlight hallucinations, and provide citations and corrections.
            </p>
          </div>
        </div>
      </motion.div>

      {isProcessing ? (
        /* Processing View */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12"
        >
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mx-auto mb-6 shadow-glow-md"
              >
                <FileText className="w-10 h-10 text-white" />
              </motion.div>
              <h2 className="text-2xl font-bold text-dark-text mb-2">Processing Your Documents</h2>
              <p className="text-dark-muted">
                Running through our 8-layer verification pipeline...
              </p>
            </div>

            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-dark-muted">Progress</span>
                <span className="text-sm font-medium text-primary-400">{progress}%</span>
              </div>
              <div className="h-2 bg-dark-border rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full"
                />
              </div>
            </div>

            <ProgressSteps steps={steps} />
          </div>
        </motion.div>
      ) : (
        /* Upload View */
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column: Source Documents */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-card p-6"
          >
            <FileUpload
              label="📚 Source Knowledge Base"
              description="Upload PDF/Text documents (medical guidelines, legal acts, etc.)"
              onFilesSelected={setSourceFiles}
              acceptedTypes={['.txt', '.pdf', '.docx']}
              multiple={true}
            />
          </motion.div>

          {/* Right Column: LLM Output */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-card p-6"
          >
            <div className="mb-6">
              <div className="flex items-center gap-4 mb-4">
                <button
                  onClick={() => setInputMethod('paste')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    inputMethod === 'paste'
                      ? 'bg-primary-500 text-white'
                      : 'bg-dark-card text-dark-muted hover:text-dark-text'
                  }`}
                >
                  Paste Text
                </button>
                <button
                  onClick={() => setInputMethod('upload')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    inputMethod === 'upload'
                      ? 'bg-primary-500 text-white'
                      : 'bg-dark-card text-dark-muted hover:text-dark-text'
                  }`}
                >
                  Upload File
                </button>
              </div>
            </div>

            {inputMethod === 'paste' ? (
              <TextInput
                label="🤖 LLM Output"
                description="Paste the AI-generated text you want to verify"
                value={llmOutput}
                onChange={setLlmOutput}
                placeholder="Enter the LLM-generated text here..."
                rows={12}
              />
            ) : (
              <FileUpload
                label="🤖 LLM Output File"
                description="Upload the text file containing LLM output"
                onFilesSelected={(files) => {
                  if (files.length > 0) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                      setLlmOutput(e.target?.result as string || '');
                    };
                    reader.readAsText(files[0]);
                  }
                }}
                acceptedTypes={['.txt', '.md']}
                multiple={false}
              />
            )}

            <button
              onClick={loadDemoData}
              className="mt-4 text-sm text-primary-400 hover:text-primary-300 transition-colors"
            >
              📋 Load demo data for testing
            </button>
          </motion.div>
        </div>
      )}

      {/* Action Buttons */}
      {!isProcessing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8"
        >
          {/* Validation Messages */}
          <div className="flex flex-wrap gap-4 mb-6">
            <div className={`flex items-center gap-2 text-sm ${hasSourceFiles ? 'text-verified' : 'text-dark-muted'}`}>
              {hasSourceFiles ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              {hasSourceFiles ? `${sourceFiles.length} source file(s) uploaded` : 'Upload source documents'}
            </div>
            <div className={`flex items-center gap-2 text-sm ${hasLlmOutput ? 'text-verified' : 'text-dark-muted'}`}>
              {hasLlmOutput ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              {hasLlmOutput ? 'LLM output provided' : 'Provide LLM output'}
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-hallucination/20 border border-hallucination/30 text-hallucination">
              {error}
            </div>
          )}

          <div className="flex gap-4">
            <button
              onClick={handleVerify}
              disabled={!canVerify}
              className="btn-primary"
            >
              <Play className="w-5 h-5" />
              Start Verification
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => router.push('/results?demo=true')}
              className="btn-secondary"
            >
              View Demo Results
            </button>
          </div>
        </motion.div>
      )}
    </Layout>
  );
}
