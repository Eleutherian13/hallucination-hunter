'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Layout } from '@/components/layout';
import { StatCard } from '@/components/ui';
import {
  Search,
  CheckCircle,
  XCircle,
  AlertCircle,
  Zap,
  Shield,
  Target,
  GitBranch,
  ArrowRight,
  Play,
  FileText,
  BarChart3,
} from 'lucide-react';

const features = [
  {
    icon: Shield,
    title: 'Multi-Layer Verification',
    description: 'Eight specialized layers working in concert to detect hallucinations with high accuracy.',
  },
  {
    icon: Target,
    title: 'Precise Citations',
    description: 'Direct links to exact paragraphs in source documents that validate each claim.',
  },
  {
    icon: Zap,
    title: 'Intelligent Corrections',
    description: 'AI-powered suggestions to fix hallucinated content based on actual source material.',
  },
  {
    icon: GitBranch,
    title: 'Full Explainability',
    description: 'Clear explanations for every flag: why, where, and how confident.',
  },
];

const stats = [
  { value: '98.2%', label: 'Detection Accuracy', color: 'text-verified' },
  { value: '8', label: 'Pipeline Layers', color: 'text-primary-400' },
  { value: '<2s', label: 'Avg. Processing', color: 'text-unverified' },
  { value: '50K+', label: 'Claims Verified', color: 'text-dark-text' },
];

const stagger = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

export default function HomePage() {
  return (
    <Layout
      title="Welcome to Hallucination Hunter"
      description="AI-Powered Fact-Checking System for LLM Outputs"
      pageTitle="Home"
    >
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="relative mb-12"
      >
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-transparent to-transparent rounded-3xl" />
        
        <div className="relative glass-card p-8 md:p-12">
          <div className="max-w-3xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/20 text-primary-400 text-sm font-medium mb-6">
                <Zap className="w-4 h-4" />
                E-Summit '26 DataForge Track 1
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-4xl md:text-5xl font-bold text-dark-text mb-4 leading-tight"
            >
              Hallucination Hunter v2.0
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-lg text-dark-muted mb-8 max-w-2xl"
            >
              Verify LLM outputs against source documents with our 8-layer AI verification pipeline.
              Detect hallucinations, get citations, and ensure factual accuracy.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex flex-wrap gap-4"
            >
              <Link href="/verify" className="btn-primary flex items-center gap-2">
                <Play className="w-5 h-5" />
                Start Verification
              </Link>
              <Link href="/pipeline" className="btn-secondary flex items-center gap-2">
                <GitBranch className="w-5 h-5" />
                View Pipeline
              </Link>
              <Link href="/benchmarks" className="btn-secondary flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Benchmarks
              </Link>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12"
      >
        {stats.map((stat, idx) => (
          <StatCard key={idx} value={stat.value} label={stat.label} valueClassName={stat.color} />
        ))}
      </motion.div>

      {/* Features Grid */}
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="text-2xl font-bold text-dark-text mb-6"
      >
        Key Features
      </motion.h2>

      <motion.div
        variants={stagger}
        initial="initial"
        animate="animate"
        className="grid md:grid-cols-2 gap-6 mb-12"
      >
        {features.map((feature, idx) => (
          <motion.div
            key={feature.title}
            variants={fadeInUp}
            className="glass-card p-6 group hover:border-primary-500/50 transition-all"
          >
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.icon === Shield ? 'from-blue-500 to-blue-600' : feature.icon === Target ? 'from-purple-500 to-purple-600' : feature.icon === Zap ? 'from-green-500 to-green-600' : 'from-orange-500 to-orange-600'} flex items-center justify-center mb-4`}>
              <feature.icon className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-dark-text mb-2 group-hover:text-primary-400 transition-colors">
              {feature.title}
            </h3>
            <p className="text-dark-muted text-sm">
              {feature.description}
            </p>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
      >
        <h2 className="text-2xl font-bold text-dark-text mb-6">Quick Actions</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <Link href="/verify">
            <div className="glass-card-hover p-6 h-full">
              <div className="w-12 h-12 rounded-xl bg-verified/20 flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-verified" />
              </div>
              <h3 className="text-lg font-semibold text-dark-text mb-2">Upload & Verify</h3>
              <p className="text-dark-muted text-sm">
                Upload source documents and LLM output to start verification.
              </p>
            </div>
          </Link>
          
          <Link href="/pipeline">
            <div className="glass-card-hover p-6 h-full">
              <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center mb-4">
                <GitBranch className="w-6 h-6 text-primary-400" />
              </div>
              <h3 className="text-lg font-semibold text-dark-text mb-2">Explore Pipeline</h3>
              <p className="text-dark-muted text-sm">
                Understand our 8-layer verification architecture in detail.
              </p>
            </div>
          </Link>
          
          <Link href="/benchmarks">
            <div className="glass-card-hover p-6 h-full">
              <div className="w-12 h-12 rounded-xl bg-unverified/20 flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-unverified" />
              </div>
              <h3 className="text-lg font-semibold text-dark-text mb-2">Run Benchmarks</h3>
              <p className="text-dark-muted text-sm">
                Test against HaluEval dataset and view performance metrics.
              </p>
            </div>
          </Link>
        </div>
      </motion.div>
    </Layout>
  );
}
