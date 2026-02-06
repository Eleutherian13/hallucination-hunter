"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import { motion, AnimatePresence } from "framer-motion";
import { Layout } from "@/components/layout";
import {
  ConfidenceMeter,
  StatusBadge,
  ClaimCard,
  StatCard,
} from "@/components/ui";
import type { Claim, SourceDocument, VerificationResult } from "@/types";
import {
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  BookOpen,
  Edit3,
  HelpCircle,
  ChevronRight,
  Download,
  Share2,
  RefreshCw,
  ExternalLink,
  Lightbulb,
  Quote,
  ArrowRight,
} from "lucide-react";

// Demo data for demonstration
const demoSourceDocument: SourceDocument = {
  id: "doc_001",
  name: "ADA Diabetes Guidelines 2024.txt",
  fileType: "txt",
  content: "",
  uploadedAt: new Date().toISOString(),
  paragraphs: [
    {
      idx: 0,
      text: "Type 2 diabetes mellitus is a chronic metabolic disorder characterized by hyperglycemia resulting from defects in insulin secretion, insulin action, or both. Early diagnosis and comprehensive management are essential for preventing complications.",
    },
    {
      idx: 1,
      text: "The patient should be evaluated for diabetes complications at the time of diagnosis and annually thereafter. Key areas include retinopathy screening through dilated eye exam, nephropathy assessment via urine albumin-to-creatinine ratio and eGFR, neuropathy evaluation through comprehensive foot exam, and cardiovascular risk assessment.",
    },
    {
      idx: 2,
      text: "HbA1c target should be individualized. For most non-pregnant adults, a reasonable HbA1c goal is <7.0%. A more stringent goal of <6.5% may be appropriate for selected individuals if achievable without significant hypoglycemia.",
    },
    {
      idx: 3,
      text: "Metformin remains the first-line pharmacological agent unless contraindicated. It should be initiated at the time of diagnosis along with lifestyle modifications including medical nutrition therapy and physical activity.",
    },
    {
      idx: 4,
      text: "GLP-1 receptor agonists and SGLT2 inhibitors have demonstrated cardiovascular and renal protective effects and should be considered for patients with established cardiovascular disease, heart failure, or chronic kidney disease.",
    },
    {
      idx: 5,
      text: "Blood pressure targets for patients with diabetes should be <130/80 mmHg. First-line antihypertensive agents include ACE inhibitors or ARBs, especially for patients with albuminuria.",
    },
    {
      idx: 6,
      text: "Statin therapy is recommended for all adults with diabetes aged 40-75 years. High-intensity statin therapy should be used for patients with established ASCVD.",
    },
    {
      idx: 7,
      text: "All patients should receive diabetes self-management education and support (DSMES) at diagnosis and throughout their care.",
    },
  ],
};

const demoClaims: Claim[] = [
  {
    id: "claim_001",
    text: "For diagnosis, diabetes is confirmed when HbA1c is ≥6.5% or fasting glucose is ≥126 mg/dL.",
    status: "verified",
    confidence: 0.95,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 0,
    sourceSnippet:
      "Type 2 diabetes mellitus is a chronic metabolic disorder characterized by hyperglycemia...",
    explanation:
      "This claim aligns with standard diagnostic criteria mentioned in the source document.",
  },
  {
    id: "claim_002",
    text: "Patients should be screened for complications annually including retinopathy and nephropathy.",
    status: "verified",
    confidence: 0.98,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 1,
    sourceSnippet:
      "The patient should be evaluated for diabetes complications at the time of diagnosis and annually thereafter. Key areas include retinopathy screening...",
    explanation:
      "Direct match with source paragraph 2 which explicitly states annual screening requirements.",
  },
  {
    id: "claim_003",
    text: "The recommended HbA1c target for most adults is <7.0%, though this should be individualized.",
    status: "verified",
    confidence: 0.97,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 2,
    sourceSnippet:
      "For most non-pregnant adults, a reasonable HbA1c goal is <7.0%.",
    explanation:
      "Accurate representation of the glycemic targets from the source document.",
  },
  {
    id: "claim_004",
    text: "Metformin is the recommended first-line medication for Type 2 Diabetes.",
    status: "verified",
    confidence: 0.99,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 3,
    sourceSnippet:
      "Metformin remains the first-line pharmacological agent unless contraindicated.",
    explanation:
      "The claim correctly reflects the source document statement about metformin.",
  },
  {
    id: "claim_005",
    text: "Blood pressure targets for diabetic patients should be <140/90 mmHg according to the guidelines.",
    status: "hallucination",
    confidence: 0.92,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 5,
    sourceSnippet:
      "Blood pressure targets for patients with diabetes should be <130/80 mmHg.",
    explanation:
      "FACTUAL ERROR: The source document clearly states the blood pressure target as <130/80 mmHg, but the claim incorrectly states <140/90 mmHg. This is a significant discrepancy of 10 mmHg on both systolic and diastolic values.",
    correction:
      "Blood pressure targets for patients with diabetes should be <130/80 mmHg, not <140/90 mmHg.",
    reasoning:
      "The LLM appears to have confused the stricter diabetes-specific guidelines with general hypertension guidelines. This type of error could lead to inadequate blood pressure control in diabetic patients.",
  },
  {
    id: "claim_006",
    text: "Sulfonylureas are the preferred second-line agents for all diabetic patients regardless of cardiovascular history.",
    status: "hallucination",
    confidence: 0.89,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 4,
    sourceSnippet:
      "GLP-1 receptor agonists and SGLT2 inhibitors have demonstrated cardiovascular and renal protective effects...",
    explanation:
      "INCORRECT RECOMMENDATION: The source document explicitly recommends GLP-1 receptor agonists and SGLT2 inhibitors (NOT sulfonylureas) for patients with cardiovascular disease. The claim ignores important patient-specific factors.",
    correction:
      "GLP-1 receptor agonists and SGLT2 inhibitors should be considered as second-line agents, especially for patients with established cardiovascular disease or high cardiovascular risk.",
    reasoning:
      "This is a potentially dangerous hallucination as sulfonylureas do not provide the cardiovascular benefits that GLP-1 RAs and SGLT2i offer. Following this incorrect advice could deny patients important cardioprotective benefits.",
  },
  {
    id: "claim_007",
    text: "All patients aged 40-75 should receive statin therapy for cardiovascular protection.",
    status: "verified",
    confidence: 0.94,
    sourceDocId: "doc_001",
    sourceParagraphIdx: 6,
    sourceSnippet:
      "Statin therapy is recommended for all adults with diabetes aged 40-75 years.",
    explanation:
      "Accurate representation of the statin therapy recommendations.",
  },
];

const demoResult: VerificationResult = {
  id: "demo-result-001",
  overallConfidence: 0.71,
  totalClaims: 7,
  verifiedCount: 5,
  hallucinationCount: 2,
  unverifiedCount: 0,
  claims: demoClaims,
  sourceDocuments: [demoSourceDocument],
  llmOutput: "",
  processingTime: 2.34,
  createdAt: new Date().toISOString(),
};

type TabType = "source" | "citations" | "corrections" | "explainability";

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<VerificationResult>(demoResult);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("source");
  const [highlightedParagraph, setHighlightedParagraph] = useState<
    number | null
  >(null);
  const sourceViewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load actual result from sessionStorage
    const resultId = router.query.id as string;
    let storedResult = null;

    if (resultId) {
      storedResult = sessionStorage.getItem(`verification_result_${resultId}`);
    }

    // Fallback to latest result if ID-based lookup fails
    if (!storedResult) {
      storedResult = sessionStorage.getItem("latestVerificationResult");
    }

    if (storedResult) {
      try {
        const parsedResult = JSON.parse(storedResult);
        console.log("Loaded verification result:", parsedResult);
        setResult(parsedResult);
      } catch (error) {
        console.error("Failed to parse stored result:", error);
      }
    } else {
      console.warn("No stored result found, using demo data");
    }
  }, [router.query.id, router.isReady]);

  const sourceDoc = result?.sourceDocuments?.[0] || demoSourceDocument;

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      summary: {
        totalClaims: result.totalClaims,
        verifiedCount: result.verifiedCount,
        hallucinationCount: result.hallucinationCount,
        unverifiedCount: result.unverifiedCount,
        overallConfidence: result.overallConfidence,
      },
      claims: result.claims.map((c) => ({
        text: c.text,
        status: c.status,
        confidence: c.confidence,
        explanation: c.explanation,
        correction: c.correction,
        sourceSnippet: c.sourceSnippet,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `verification-report-${new Date().getTime()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClaimClick = (claim: Claim) => {
    setSelectedClaim(claim);

    if (claim.sourceParagraphIdx !== undefined) {
      setHighlightedParagraph(claim.sourceParagraphIdx);
      setActiveTab("source");

      // Scroll to the paragraph
      setTimeout(() => {
        const element = document.getElementById(
          `para-${claim.sourceParagraphIdx}`,
        );
        if (element && sourceViewerRef.current) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 100);
    }

    // If hallucination, show corrections tab
    if (claim.status === "hallucination") {
      setActiveTab("corrections");
    }
  };

  const tabs = [
    { id: "source", label: "Source Document", icon: BookOpen },
    { id: "citations", label: "Citation Report", icon: Quote },
    {
      id: "corrections",
      label: "Corrections",
      icon: Edit3,
      count: result.hallucinationCount,
    },
    { id: "explainability", label: "Explainability", icon: HelpCircle },
  ] as const;

  return (
    <Layout
      title="Verification Results"
      description={`${result.totalClaims} claims analyzed • ${result.hallucinationCount} hallucinations detected`}
      pageTitle="Results"
    >
      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"
      >
        <StatCard
          value={result.totalClaims}
          label="Total Claims"
          icon={<FileText className="w-5 h-5 text-primary-400" />}
        />
        <StatCard
          value={result.verifiedCount}
          label="Verified"
          colorClass="text-verified"
          icon={<CheckCircle className="w-5 h-5 text-verified" />}
        />
        <StatCard
          value={result.hallucinationCount}
          label="Hallucinations"
          colorClass="text-hallucination"
          icon={<XCircle className="w-5 h-5 text-hallucination" />}
        />
        <StatCard
          value={result.unverifiedCount}
          label="Unverified"
          colorClass="text-unverified"
          icon={<AlertCircle className="w-5 h-5 text-unverified" />}
        />
        <div className="glass-card p-4">
          <ConfidenceMeter confidence={result.overallConfidence} size="md" />
        </div>
      </motion.div>

      {/* Main Split Screen */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Panel: Annotated Claims */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card overflow-hidden"
        >
          <div className="p-4 border-b border-dark-border">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-dark-text flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary-400" />
                Annotated LLM Output
              </h2>
              <p className="text-sm text-dark-muted">Click to view evidence</p>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 mt-3 text-sm">
              <span className="flex items-center gap-1.5 text-verified">
                <span className="w-3 h-3 rounded bg-verified/30 border border-verified" />
                Verified
              </span>
              <span className="flex items-center gap-1.5 text-hallucination">
                <span className="w-3 h-3 rounded bg-hallucination/30 border border-hallucination" />
                Hallucination
              </span>
              <span className="flex items-center gap-1.5 text-unverified">
                <span className="w-3 h-3 rounded bg-unverified/30 border border-unverified" />
                Unverified
              </span>
            </div>
          </div>

          <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
            {result.claims.map((claim) => (
              <ClaimCard
                key={claim.id}
                claim={claim}
                onClick={() => handleClaimClick(claim)}
                isSelected={selectedClaim?.id === claim.id}
              />
            ))}
          </div>
        </motion.div>

        {/* Right Panel: Tabbed View */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card overflow-hidden"
        >
          {/* Tabs */}
          <div className="flex border-b border-dark-border">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? "text-primary-400 border-b-2 border-primary-500 bg-primary-500/5"
                    : "text-dark-muted hover:text-dark-text hover:bg-dark-card/50"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-hallucination/20 text-hallucination">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div
            className="p-4 max-h-[600px] overflow-y-auto"
            ref={sourceViewerRef}
          >
            <AnimatePresence mode="wait">
              {activeTab === "source" && (
                <SourceDocumentView
                  document={sourceDoc}
                  highlightedParagraph={highlightedParagraph}
                />
              )}
              {activeTab === "citations" && (
                <CitationReportView
                  claims={result.claims.filter((c) => c.status === "verified")}
                  sourceDoc={sourceDoc}
                  onClaimClick={handleClaimClick}
                />
              )}
              {activeTab === "corrections" && (
                <CorrectionsView
                  claims={result.claims.filter(
                    (c) => c.status === "hallucination",
                  )}
                />
              )}
              {activeTab === "explainability" && (
                <ExplainabilityView claim={selectedClaim} />
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex flex-wrap gap-4 mt-8"
      >
        <button onClick={handleExport} className="btn-secondary">
          <Download className="w-4 h-4" />
          Export Report
        </button>
        <button className="btn-secondary">
          <Share2 className="w-4 h-4" />
          Share Results
        </button>
        <button
          onClick={() => router.push("/verify")}
          className="btn-secondary"
        >
          <RefreshCw className="w-4 h-4" />
          New Verification
        </button>
      </motion.div>
    </Layout>
  );
}

// Sub-components

function SourceDocumentView({
  document,
  highlightedParagraph,
}: {
  document: SourceDocument;
  highlightedParagraph: number | null;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-5 h-5 text-primary-400" />
        <h3 className="font-semibold text-dark-text">{document.name}</h3>
      </div>

      <div className="space-y-3">
        {document.paragraphs.map((para) => (
          <div
            key={para.idx}
            id={`para-${para.idx}`}
            className={`p-4 rounded-xl transition-all duration-300 ${
              highlightedParagraph === para.idx
                ? "bg-primary-500/20 border border-primary-500/50 ring-2 ring-primary-500/30"
                : "bg-dark-bg/50 border border-dark-border hover:border-dark-muted"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  highlightedParagraph === para.idx
                    ? "bg-primary-500/30 text-primary-400"
                    : "bg-dark-border text-dark-muted"
                }`}
              >
                ¶{para.idx + 1}
              </span>
            </div>
            <p className="text-sm text-dark-text leading-relaxed">
              {para.text}
            </p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function CitationReportView({
  claims,
  sourceDoc,
  onClaimClick,
}: {
  claims: Claim[];
  sourceDoc: SourceDocument;
  onClaimClick: (claim: Claim) => void;
}) {
  if (claims.length === 0) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-dark-muted mx-auto mb-4" />
        <p className="text-dark-muted">
          No verified claims to show citations for.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-4"
    >
      <div className="flex items-center gap-2 mb-4">
        <Quote className="w-5 h-5 text-verified" />
        <h3 className="font-semibold text-dark-text">Direct Citations</h3>
        <span className="text-sm text-dark-muted">
          ({claims.length} verified claims)
        </span>
      </div>

      {claims.map((claim) => (
        <div
          key={claim.id}
          className="p-4 rounded-xl bg-verified/10 border border-verified/30 cursor-pointer hover:bg-verified/15 transition-colors"
          onClick={() => onClaimClick(claim)}
        >
          <p className="text-dark-text text-sm mb-3">"{claim.text}"</p>

          <div className="flex items-start gap-3 p-3 rounded-lg bg-dark-bg/50">
            <Quote className="w-4 h-4 text-verified shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-dark-muted mb-1">
                {sourceDoc.name} • Paragraph{" "}
                {(claim.sourceParagraphIdx || 0) + 1}
              </p>
              <p className="text-sm text-dark-muted italic">
                "{claim.sourceSnippet}"
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 mt-3 text-xs text-verified">
            <CheckCircle className="w-3 h-3" />
            Confidence: {Math.round(claim.confidence * 100)}%
            <ChevronRight className="w-3 h-3 ml-auto" />
          </div>
        </div>
      ))}
    </motion.div>
  );
}

function CorrectionsView({ claims }: { claims: Claim[] }) {
  if (claims.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="w-12 h-12 text-verified mx-auto mb-4" />
        <p className="text-dark-text font-medium mb-2">
          No Corrections Needed!
        </p>
        <p className="text-dark-muted text-sm">
          All claims in this document are verified.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-4"
    >
      <div className="flex items-center gap-2 mb-4">
        <Edit3 className="w-5 h-5 text-hallucination" />
        <h3 className="font-semibold text-dark-text">Suggested Corrections</h3>
        <span className="text-sm text-dark-muted">
          ({claims.length} issues found)
        </span>
      </div>

      {claims.map((claim) => (
        <div
          key={claim.id}
          className="p-4 rounded-xl bg-dark-bg/50 border border-dark-border"
        >
          {/* Original */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-4 h-4 text-hallucination" />
              <span className="text-xs font-medium text-hallucination uppercase">
                Original (Hallucinated)
              </span>
            </div>
            <p className="text-sm text-dark-text line-through opacity-70">
              {claim.text}
            </p>
          </div>

          {/* Arrow */}
          <div className="flex justify-center my-2">
            <ArrowRight className="w-5 h-5 text-dark-muted rotate-90" />
          </div>

          {/* Correction */}
          <div className="p-3 rounded-lg bg-verified/10 border border-verified/30">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="w-4 h-4 text-verified" />
              <span className="text-xs font-medium text-verified uppercase">
                Suggested Correction
              </span>
            </div>
            <p className="text-sm text-dark-text">{claim.correction}</p>
          </div>

          {/* Reasoning */}
          {claim.reasoning && (
            <div className="mt-3 p-3 rounded-lg bg-dark-card border border-dark-border">
              <p className="text-xs text-dark-muted mb-1">Why this matters:</p>
              <p className="text-sm text-dark-muted">{claim.reasoning}</p>
            </div>
          )}
        </div>
      ))}
    </motion.div>
  );
}

function ExplainabilityView({ claim }: { claim: Claim | null }) {
  if (!claim) {
    return (
      <div className="text-center py-12">
        <HelpCircle className="w-12 h-12 text-dark-muted mx-auto mb-4" />
        <p className="text-dark-text font-medium mb-2">Select a Claim</p>
        <p className="text-dark-muted text-sm">
          Click on any claim in the left panel to see detailed explainability
          information.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-6"
    >
      {/* Selected Claim */}
      <div className="p-4 rounded-xl bg-dark-bg/50 border border-dark-border">
        <div className="flex items-center gap-2 mb-2">
          <StatusBadge status={claim.status} size="sm" />
          <span className="text-sm text-dark-muted">
            Confidence: {Math.round(claim.confidence * 100)}%
          </span>
        </div>
        <p className="text-dark-text">{claim.text}</p>
      </div>

      {/* Why is this flagged? */}
      <div className="glass-card p-4 border-l-4 border-primary-500">
        <h4 className="font-semibold text-dark-text flex items-center gap-2 mb-3">
          <HelpCircle className="w-4 h-4 text-primary-400" />
          Why is this flagged?
        </h4>
        <p className="text-sm text-dark-muted leading-relaxed">
          {claim.explanation}
        </p>
      </div>

      {/* Where is the proof? */}
      {claim.sourceSnippet && (
        <div className="glass-card p-4 border-l-4 border-verified">
          <h4 className="font-semibold text-dark-text flex items-center gap-2 mb-3">
            <BookOpen className="w-4 h-4 text-verified" />
            Where is the proof?
          </h4>
          <div className="p-3 rounded-lg bg-dark-bg/50 border border-dark-border">
            <p className="text-xs text-dark-muted mb-1">
              Source: Paragraph {(claim.sourceParagraphIdx || 0) + 1}
            </p>
            <p className="text-sm text-dark-text italic">
              "{claim.sourceSnippet}"
            </p>
          </div>
        </div>
      )}

      {/* How confident? */}
      <div className="glass-card p-4 border-l-4 border-unverified">
        <h4 className="font-semibold text-dark-text flex items-center gap-2 mb-3">
          <AlertCircle className="w-4 h-4 text-unverified" />
          How confident is the model?
        </h4>
        <div className="space-y-3">
          <ConfidenceMeter
            confidence={claim.confidence}
            size="lg"
            showLabel={false}
          />
          <p className="text-sm text-dark-muted">
            {claim.confidence >= 0.9
              ? "🔴 CERTAIN ERROR: High confidence that this is a factual discrepancy."
              : claim.confidence >= 0.7
                ? "🟠 LIKELY ERROR: Strong evidence suggests this claim is problematic."
                : claim.confidence >= 0.5
                  ? "🟡 POSSIBLE ERROR: Some evidence suggests this claim may be incorrect."
                  : "🟢 UNCERTAIN: Limited evidence, requires human review."}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
