"use client";

/**
 * UI Component Library — Barrel Export
 *
 * This file re-exports all design system components for clean imports.
 * Legacy components (Card, StatBox, Toast, etc.) are preserved for
 * backward compatibility and will be migrated during integration.
 *
 * Usage:
 *   import { Button, DataTable, Modal, KPIStatCard } from '@/components/ui';
 */

import React from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, Send, X, WifiOff } from "lucide-react";

// ── NEW: Design System Components ───────────────────────
export { default as Button } from "./Button";
export { default as Modal } from "./Modal";
export { default as DataTable } from "./DataTable";
export { default as EmptyState } from "./EmptyState";
export { default as KPIStatCard } from "./KPIStatCard";
export { default as StatusBadge } from "./StatusBadge";
export { default as Drawer } from "./Drawer";
export { default as EventTimeline } from "./EventTimeline";
export { default as CommandPalette } from "./CommandPalette";
export { default as QuoteSummaryCard } from "./QuoteSummaryCard";
export { default as Skeleton, SkeletonCard, SkeletonTable, SkeletonChart, SkeletonForm, SkeletonSidebar } from "./Skeleton";
export { Page, PageHeader, PageContent, PageSection, PageActions } from "./PageLayout";
export { Form, FormField, Label, Input, Select, Textarea, HelperText, FieldError } from "./FormSystem";

// ── LEGACY: Preserved for backward compatibility ────────
// These will be gradually replaced by new components during integration.

export const Card = ({ children, className = "" }) => (
  <div className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] overflow-hidden ${className}`}>
    {children}
  </div>
);

export const StatBox = ({ title, value, icon: Icon, alert = false, subtitle, trend }) => (
  <Card className={`p-4 sm:p-5 min-w-[240px] sm:min-w-[260px] md:min-w-0 snap-start flex-shrink-0 transition-all hover:border-[var(--border-strong)] ${alert ? 'border-[var(--danger-border)] bg-[var(--danger-bg)]' : ''}`}>
    <div className="flex justify-between items-start">
      <div className="space-y-1 min-w-0 flex-1">
        <p className={`text-label ${alert ? 'text-[var(--danger-text)]' : 'text-[var(--text-secondary)]'}`}>{title}</p>
        <h3 className={`text-xl sm:text-2xl font-extrabold tracking-tight ${alert ? 'text-[var(--danger-text)]' : 'text-[var(--text-primary)]'}`}>{value}</h3>
        {subtitle && (
          <div className="flex items-center gap-1 mt-1">
            <span className={`text-[9px] sm:text-[10px] font-semibold tracking-wide ${trend === 'up' ? 'text-[var(--text-primary)]' : trend === 'down' ? 'text-[var(--danger-text)]' : 'text-[var(--text-secondary)]'}`}>
              {subtitle}
            </span>
          </div>
        )}
      </div>
      <div className={`p-2 rounded-[var(--radius-md)] border flex-shrink-0 ${alert ? 'bg-[var(--danger-bg)] border-[var(--danger-border)] text-[var(--danger-text)]' : 'bg-[var(--bg-app)] border-[var(--border-subtle)] text-[var(--text-primary)]'}`}>
        <Icon size={16} />
      </div>
    </div>
  </Card>
);

export const TableSkeleton = ({ rows = 4, cols = 5 }) => (
  <div className="animate-pulse p-6 bg-[var(--bg-surface)] space-y-4">
    {Array.from({ length: rows }).map((_, r) => (
      <div key={r} className="flex gap-4 items-center">
        {Array.from({ length: cols }).map((_, c) => (
          <div className="h-4 bg-[var(--border-subtle)] rounded flex-1" key={c}></div>
        ))}
      </div>
    ))}
  </div>
);

export const ChartSkeleton = () => (
  <div className="animate-pulse bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-6 h-80 flex flex-col justify-between">
    <div className="flex justify-between items-center mb-6">
      <div className="h-5 bg-[var(--border-subtle)] rounded w-1/3"></div>
      <div className="h-8 bg-[var(--border-subtle)] rounded w-20"></div>
    </div>
    <div className="flex-1 flex items-end gap-3 pb-4">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="bg-[var(--border-subtle)] rounded-t flex-1" style={{ height: `${20 + (i * 7) % 70}%` }}></div>
      ))}
    </div>
  </div>
);

export const Toast = ({ message, type = 'info', onClose }) => {
  const borderStyles = {
    success: 'border-[var(--border-strong)] text-[var(--text-primary)]',
    error: 'border-[var(--danger-text)] text-[var(--danger-text)]',
    warning: 'border-[var(--warning-text)] text-[var(--warning-text)]',
    info: 'border-[var(--border-subtle)] text-[var(--text-primary)]',
  };
  const icons = {
    success: <CheckCircle2 size={16} className="text-[var(--success-text)]" />,
    error: <AlertCircle size={16} className="text-[var(--danger-text)]" />,
    warning: <AlertTriangle size={16} className="text-[var(--warning-text)]" />,
    info: <Send size={16} className="text-[var(--text-primary)]" />,
  };

  return (
    <div
      className={`border-l-4 bg-[var(--bg-surface)] border border-y-[var(--border-subtle)] border-r-[var(--border-subtle)] px-4 py-3 flex items-center justify-between text-caption font-semibold animate-in slide-in-from-top duration-150 ${borderStyles[type]}`}
      style={{ boxShadow: "var(--shadow-sm)", zIndex: "var(--z-toast)" }}
    >
      <span className="flex items-center gap-2">
        {icons[type]} {message}
      </span>
      <button onClick={onClose} className="hover:opacity-70 text-[var(--text-secondary)] ml-4 focus-ring rounded-[var(--radius-sm)]"><X size={14} /></button>
    </div>
  );
};

export function classifyError(err, response) {
  if (!response && (err instanceof TypeError || err.name === 'AbortError')) {
    return {
      type: 'warning',
      message: '⚠️ Network Connection Error: Could not reach the server. UI reverted to previous state.',
    };
  }
  if (response && !response.ok) {
    const code = response.status;
    if (code === 401 || code === 403) {
      return { type: 'error', message: '❌ Access Denied: You do not have permission for this action. UI reverted.' };
    }
    if (code === 404) {
      return { type: 'error', message: '❌ Not Found: The requested resource could not be located. UI reverted.' };
    }
    if (code === 422) {
      return { type: 'error', message: '❌ Validation Error: Please check your input and try again. UI reverted.' };
    }
    return { type: 'error', message: `❌ Request Rejected (HTTP ${code}): Unable to save your changes at this time. Please try again. UI reverted.` };
  }
  return { type: 'error', message: '❌ An unexpected error occurred. UI reverted to previous state.' };
}

export const ErrorBanner = ({ message, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-12 text-[var(--text-secondary)] bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)]">
    <WifiOff size={32} className="mb-3 text-[var(--text-primary)]" />
    <p className="text-label">{message}</p>
    <button
      onClick={onRetry}
      className="mt-4 h-10 px-6 bg-[var(--text-primary)] text-white text-xs font-bold uppercase tracking-wider rounded-[var(--radius-md)] hover:bg-black transition-colors focus-ring"
    >
      Try Again
    </button>
  </div>
);
