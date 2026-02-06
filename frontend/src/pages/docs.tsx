'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Layout } from '@/components/layout';
import {
  BookOpen,
  Code,
  Zap,
  FileText,
  GitBranch,
  Shield,
  ChevronRight,
  ExternalLink,
  Copy,
  Check,
  Terminal,
  Layers,
  Target,
  Search,
} from 'lucide-react';

const sections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: Zap,
    content: `
## Quick Start Guide

Hallucination Hunter v2.0 is an AI-powered fact-checking system designed to detect and correct hallucinations in LLM-generated content.

### Prerequisites
- Python 3.10+
- Node.js 18+
- 8GB RAM minimum

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/your-org/hallucination-hunter.git
cd hallucination-hunter

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install

# Start the backend
python -m uvicorn src.api.main:app --reload

# Start the frontend
npm run dev
\`\`\`

### First Verification

1. Navigate to the **Verify** page
2. Upload your source documents (PDF, TXT, or DOCX)
3. Paste or upload the LLM-generated text
4. Click **Start Verification**
5. View results with color-coded annotations
    `,
  },
  {
    id: 'features',
    title: 'Features',
    icon: Target,
    content: `
## Core Features

### 🔍 Annotated Document View
Your LLM output is displayed with color-coded highlighting:
- **Green**: Factually supported by source documents
- **Red**: Hallucination (contradicts source)
- **Yellow**: Unverifiable / Insufficient evidence

### 📋 Citation Report
For every verified claim, you get:
- Direct link to the source paragraph
- Exact quote from the source
- Confidence score

### ✏️ Correction Engine
For hallucinated content:
- AI-generated corrections based on source text
- Explanation of why the original was wrong
- Suggested rewording

### 📊 Confidence Meter
Visual representation of document reliability:
- Overall verification score
- Per-claim confidence levels
- Certainty classification (Certain vs. Likely error)

### ❓ Explainability
Every flag comes with:
- **Why**: Root cause analysis
- **Where**: Exact source passage
- **How Confident**: Certainty level
    `,
  },
  {
    id: 'pipeline',
    title: 'Pipeline Architecture',
    icon: GitBranch,
    content: `
## 8-Layer Verification Pipeline

Our system uses a sophisticated multi-layer architecture:

### Layer 1: Ingestion
Document parsing and preprocessing
- Multi-format support (PDF, TXT, DOCX)
- Paragraph segmentation
- Metadata extraction

### Layer 2: Claim Intelligence
NLP-powered claim extraction
- Sentence boundary detection
- Named entity recognition
- Claim classification

### Layer 3: Retrieval
Semantic evidence search
- Dense passage retrieval
- FAISS vector search
- BM25 fallback

### Layer 4: Verification
Fact-checking analysis
- Natural Language Inference (NLI)
- Entailment detection
- Contradiction identification

### Layer 5: Scoring
Confidence computation
- Multi-signal fusion
- Calibrated probabilities
- Evidence weighting

### Layer 6: Correction
Fix generation
- Source-grounded synthesis
- Minimal edit corrections
- Context preservation

### Layer 7: Explanation
Reasoning output
- Decision path explanation
- Attention visualization
- Human-readable format

### Layer 8: Output
Result formatting
- Annotated documents
- Export options (PDF, JSON, HTML)
    `,
  },
  {
    id: 'api',
    title: 'API Reference',
    icon: Code,
    content: `
## REST API

### Verification Endpoint

\`\`\`http
POST /api/verify
Content-Type: multipart/form-data
\`\`\`

**Request Body:**
- \`source_files\`: Source document files (multiple)
- \`llm_output\`: LLM-generated text string
- \`config\`: Optional JSON configuration

**Response:**
\`\`\`json
{
  "id": "ver_123abc",
  "overallConfidence": 0.85,
  "totalClaims": 10,
  "verifiedCount": 7,
  "hallucinationCount": 2,
  "unverifiedCount": 1,
  "claims": [...],
  "processingTime": 2.34
}
\`\`\`

### Benchmark Endpoint

\`\`\`http
POST /api/benchmark/run
Content-Type: application/json

{
  "dataset": "halueval",
  "sample_count": 100
}
\`\`\`

### Health Check

\`\`\`http
GET /api/health

Response: { "status": "ok", "version": "2.0.0" }
\`\`\`
    `,
  },
  {
    id: 'benchmarks',
    title: 'Benchmarks',
    icon: Layers,
    content: `
## Performance Metrics

### HaluEval Dataset Results

| Metric | Score |
|--------|-------|
| Accuracy | 89.2% |
| Precision | 87.8% |
| Recall | 91.2% |
| F1 Score | 89.5% |

### By Category

| Category | Accuracy | Samples |
|----------|----------|---------|
| QA | 91.0% | 150 |
| Summarization | 87.0% | 180 |
| Dialogue | 89.0% | 170 |

### Version History

| Version | Accuracy | Key Changes |
|---------|----------|-------------|
| v1.0 | 72% | Initial release |
| v1.5 | 83% | Added NLI models |
| v2.0 | 89% | DeBERTa-v3, FAISS |

### Running Benchmarks

Navigate to the **Benchmarks** page and click "Run Benchmark" to test against the HaluEval dataset.
    `,
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting',
    icon: Shield,
    content: `
## Common Issues

### "No claims extracted"
**Cause**: LLM output too short or non-factual
**Solution**: Ensure the text contains factual statements (not just opinions)

### "Low confidence scores"
**Cause**: Source documents don't cover the topic
**Solution**: Upload more comprehensive source materials

### "Processing timeout"
**Cause**: Very large documents
**Solution**: Split documents or increase timeout in settings

### "PDF extraction failed"
**Cause**: Scanned PDF or complex layout
**Solution**: Convert to text file or use OCR

### Backend Connection Error
\`\`\`bash
# Check if backend is running
curl http://localhost:8000/api/health

# Restart backend
python -m uvicorn src.api.main:app --reload
\`\`\`

### Memory Issues
\`\`\`bash
# Reduce batch size in config
export MAX_BATCH_SIZE=16
export MAX_CLAIMS=25
\`\`\`

## Getting Help

- GitHub Issues: [Report a bug](https://github.com/your-org/hallucination-hunter/issues)
- Documentation: [Full docs](https://docs.hallucination-hunter.dev)
- Email: support@hallucination-hunter.dev
    `,
  },
];

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState('getting-started');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const currentSection = sections.find(s => s.id === activeSection);

  return (
    <Layout
      title="Documentation"
      description="Learn how to use Hallucination Hunter effectively"
      pageTitle="Docs"
    >
      <div className="grid lg:grid-cols-4 gap-8">
        {/* Sidebar Navigation */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-1"
        >
          <div className="glass-card p-4 sticky top-24">
            <h3 className="font-semibold text-dark-text mb-4 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-primary-400" />
              Contents
            </h3>
            <nav className="space-y-1">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-all ${
                    activeSection === section.id
                      ? 'bg-primary-500/20 text-primary-400'
                      : 'text-dark-muted hover:text-dark-text hover:bg-dark-card'
                  }`}
                >
                  <section.icon className="w-4 h-4" />
                  {section.title}
                  {activeSection === section.id && (
                    <ChevronRight className="w-4 h-4 ml-auto" />
                  )}
                </button>
              ))}
            </nav>

            <div className="mt-6 pt-6 border-t border-dark-border">
              <a
                href="https://github.com/your-org/hallucination-hunter"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-dark-muted hover:text-dark-text transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                View on GitHub
              </a>
            </div>
          </div>
        </motion.div>

        {/* Content */}
        <motion.div
          key={activeSection}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-3"
        >
          <div className="glass-card p-8">
            <div className="flex items-center gap-3 mb-6">
              {currentSection && (
                <>
                  <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center">
                    <currentSection.icon className="w-5 h-5 text-primary-400" />
                  </div>
                  <h1 className="text-2xl font-bold text-dark-text">
                    {currentSection.title}
                  </h1>
                </>
              )}
            </div>

            {/* Markdown-like content rendering */}
            <div className="prose prose-invert max-w-none">
              {currentSection?.content.split('\n').map((line, idx) => {
                // Code blocks
                if (line.trim().startsWith('```')) {
                  return null; // Handle separately
                }
                
                // Headers
                if (line.startsWith('## ')) {
                  return (
                    <h2 key={idx} className="text-xl font-bold text-dark-text mt-8 mb-4">
                      {line.replace('## ', '')}
                    </h2>
                  );
                }
                if (line.startsWith('### ')) {
                  return (
                    <h3 key={idx} className="text-lg font-semibold text-dark-text mt-6 mb-3">
                      {line.replace('### ', '')}
                    </h3>
                  );
                }
                
                // List items
                if (line.trim().startsWith('- ')) {
                  return (
                    <li key={idx} className="text-dark-muted ml-4 list-disc">
                      {line.replace(/^-\s+/, '')}
                    </li>
                  );
                }
                
                // Numbered lists
                if (/^\d+\.\s/.test(line.trim())) {
                  return (
                    <li key={idx} className="text-dark-muted ml-4 list-decimal">
                      {line.replace(/^\d+\.\s/, '')}
                    </li>
                  );
                }
                
                // Bold text and inline code
                if (line.trim()) {
                  const formatted = line
                    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-dark-text">$1</strong>')
                    .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-dark-bg text-primary-400 text-sm">$1</code>');
                  
                  return (
                    <p
                      key={idx}
                      className="text-dark-muted leading-relaxed my-2"
                      dangerouslySetInnerHTML={{ __html: formatted }}
                    />
                  );
                }
                
                return <div key={idx} className="h-2" />;
              })}

              {/* Render code blocks */}
              {currentSection?.content.match(/```[\s\S]*?```/g)?.map((block, idx) => {
                const lines = block.split('\n');
                const lang = lines[0].replace('```', '');
                const code = lines.slice(1, -1).join('\n');
                
                return (
                  <div key={`code-${idx}`} className="relative my-4 rounded-xl overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-2 bg-dark-bg border-b border-dark-border">
                      <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-dark-muted" />
                        <span className="text-xs text-dark-muted uppercase">{lang || 'code'}</span>
                      </div>
                      <button
                        onClick={() => copyCode(code)}
                        className="flex items-center gap-1 text-xs text-dark-muted hover:text-dark-text transition-colors"
                      >
                        {copiedCode === code ? (
                          <>
                            <Check className="w-3 h-3 text-verified" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="p-4 bg-dark-bg overflow-x-auto">
                      <code className="text-sm text-dark-text font-mono">{code}</code>
                    </pre>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
}
