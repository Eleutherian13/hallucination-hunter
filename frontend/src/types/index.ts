// Type definitions for the Hallucination Hunter application

export interface SourceDocument {
  id: string;
  name: string;
  content: string;
  fileType: string;
  paragraphs: Paragraph[];
  uploadedAt: string;
}

export interface Paragraph {
  idx: number;
  text: string;
  startOffset?: number;
  endOffset?: number;
}

export interface Claim {
  id: string;
  text: string;
  status: 'verified' | 'hallucination' | 'unverified';
  confidence: number;
  sourceDocId?: string;
  sourceParagraphIdx?: number;
  sourceSnippet?: string;
  explanation: string;
  correction?: string;
  reasoning?: string;
}

export interface VerificationResult {
  id: string;
  overallConfidence: number;
  totalClaims: number;
  verifiedCount: number;
  hallucinationCount: number;
  unverifiedCount: number;
  claims: Claim[];
  sourceDocuments: SourceDocument[];
  llmOutput: string;
  processingTime: number;
  createdAt: string;
}

export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  details?: string;
  duration?: number;
}

export interface BenchmarkResult {
  id: string;
  dataset: string;
  totalSamples: number;
  processedSamples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  averageProcessingTime: number;
  results: BenchmarkSample[];
  createdAt: string;
}

export interface BenchmarkSample {
  id: string;
  question?: string;
  context?: string;
  response: string;
  groundTruth: 'hallucinated' | 'not_hallucinated';
  prediction: 'hallucinated' | 'not_hallucinated';
  confidence: number;
  isCorrect: boolean;
}

export interface APIError {
  message: string;
  code: string;
  details?: Record<string, unknown>;
}

// Pipeline configuration
export interface PipelineConfig {
  confidenceThreshold: number;
  enableCorrections: boolean;
  enableSemanticMatching: boolean;
  maxClaimsPerDocument: number;
}

// Upload state
export interface UploadState {
  sourceFiles: File[];
  llmOutput: string;
  isProcessing: boolean;
  progress: number;
  currentStep: string;
  error?: string;
}
