'use client';

import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import type { Claim } from '@/types';

interface ConfidenceMeterProps {
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ConfidenceMeter({ confidence, size = 'md', showLabel = true }: ConfidenceMeterProps) {
  const percentage = Math.round(confidence * 100);
  
  const getColor = () => {
    if (confidence >= 0.7) return { bg: 'bg-verified', text: 'text-verified', label: 'HIGH CONFIDENCE' };
    if (confidence >= 0.4) return { bg: 'bg-unverified', text: 'text-unverified', label: 'MEDIUM CONFIDENCE' };
    return { bg: 'bg-hallucination', text: 'text-hallucination', label: 'LOW CONFIDENCE' };
  };
  
  const color = getColor();
  
  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-dark-muted">Verification Score</span>
          <span className={`text-2xl font-bold ${color.text}`}>{percentage}%</span>
        </div>
      )}
      <div className={`w-full ${sizeClasses[size]} bg-dark-border rounded-full overflow-hidden`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full ${color.bg} rounded-full`}
        />
      </div>
      {showLabel && (
        <p className={`text-xs ${color.text} mt-1 text-right`}>{color.label}</p>
      )}
    </div>
  );
}

interface StatusBadgeProps {
  status: 'verified' | 'hallucination' | 'unverified';
  size?: 'sm' | 'md';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const configs = {
    verified: {
      icon: CheckCircle,
      text: 'Verified',
      className: 'badge-verified',
    },
    hallucination: {
      icon: XCircle,
      text: 'Hallucination',
      className: 'badge-hallucination',
    },
    unverified: {
      icon: AlertCircle,
      text: 'Unverified',
      className: 'badge-unverified',
    },
  };
  
  const config = configs[status];
  const Icon = config.icon;
  
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : '';

  return (
    <span className={`${config.className} ${sizeClasses}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
      {config.text}
    </span>
  );
}

interface StatCardProps {
  value: number | string;
  label: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  colorClass?: string;
}

export function StatCard({ value, label, icon, trend, colorClass = 'text-primary-400' }: StatCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="glass-card-hover p-6"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className={`stat-value ${colorClass}`}>{value}</p>
          <p className="stat-label">{label}</p>
          {trend && (
            <p className={`text-xs mt-2 ${trend.isPositive ? 'text-verified' : 'text-hallucination'}`}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}% from last run
            </p>
          )}
        </div>
        {icon && (
          <div className="p-3 rounded-xl bg-dark-bg/50">
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  );
}

interface ClaimCardProps {
  claim: Claim;
  onClick?: () => void;
  isSelected?: boolean;
}

export function ClaimCard({ claim, onClick, isSelected }: ClaimCardProps) {
  const highlightClass = {
    verified: 'highlight-verified',
    hallucination: 'highlight-hallucination',
    unverified: 'highlight-unverified',
  }[claim.status];

  return (
    <motion.div
      whileHover={{ x: 4 }}
      onClick={onClick}
      className={`
        ${highlightClass} cursor-pointer transition-all duration-200
        ${isSelected ? 'ring-2 ring-primary-500' : ''}
      `}
    >
      <div className="flex items-start justify-between gap-4 mb-2">
        <p className="text-dark-text leading-relaxed">{claim.text}</p>
        <StatusBadge status={claim.status} size="sm" />
      </div>
      <div className="flex items-center gap-4 text-sm text-dark-muted">
        <span>Confidence: {Math.round(claim.confidence * 100)}%</span>
        {claim.sourceParagraphIdx !== undefined && (
          <span>Source: ¶{claim.sourceParagraphIdx + 1}</span>
        )}
      </div>
    </motion.div>
  );
}

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div className={`${sizeClasses[size]} border-dark-border border-t-primary-500 rounded-full animate-spin`} />
      {text && <p className="text-sm text-dark-muted">{text}</p>}
    </div>
  );
}

interface ProgressStepsProps {
  steps: { name: string; status: 'pending' | 'processing' | 'completed' | 'error' }[];
}

export function ProgressSteps({ steps }: ProgressStepsProps) {
  return (
    <div className="flex items-center justify-between">
      {steps.map((step, idx) => (
        <div key={step.name} className="flex items-center">
          <div className="flex flex-col items-center">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm
              ${step.status === 'completed' ? 'bg-verified text-white' : ''}
              ${step.status === 'processing' ? 'bg-primary-500 text-white animate-pulse' : ''}
              ${step.status === 'pending' ? 'bg-dark-border text-dark-muted' : ''}
              ${step.status === 'error' ? 'bg-hallucination text-white' : ''}
            `}>
              {step.status === 'completed' ? '✓' : idx + 1}
            </div>
            <p className="text-xs text-dark-muted mt-2 text-center w-20">{step.name}</p>
          </div>
          {idx < steps.length - 1 && (
            <div className={`w-16 h-0.5 mx-2 ${step.status === 'completed' ? 'bg-verified' : 'bg-dark-border'}`} />
          )}
        </div>
      ))}
    </div>
  );
}
