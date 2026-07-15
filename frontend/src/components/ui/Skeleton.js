"use client";

import React from "react";

/**
 * Skeleton Library — Loading state components per the Design System.
 *
 * Rule: Loading states map 1-to-1 with final components to prevent layout shift.
 */

// ── Base Skeleton Pulse ──
function Skeleton({ className = "" }) {
  return (
    <div
      className={`bg-[var(--border-subtle)] rounded-[var(--radius-md)] animate-pulse ${className}`}
    />
  );
}

// ── SkeletonCard ──
export function SkeletonCard({ className = "" }) {
  return (
    <div
      className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] p-5 animate-pulse ${className}`}
    >
      <div className="flex justify-between items-start">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-7 w-20" />
          <Skeleton className="h-3 w-32 mt-1" />
        </div>
        <Skeleton className="w-9 h-9 rounded-[var(--radius-md)]" />
      </div>
    </div>
  );
}

// ── SkeletonTable ──
export function SkeletonTable({ rows = 5, cols = 4, className = "" }) {
  return (
    <div
      className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] overflow-hidden animate-pulse ${className}`}
    >
      {/* Header */}
      <div className="flex gap-4 p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-app)]">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-3 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={r}
          className="flex gap-4 p-4 border-b border-[var(--border-subtle)] last:border-b-0"
        >
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

// ── SkeletonChart ──
export function SkeletonChart({ className = "" }) {
  return (
    <div
      className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] p-6 h-80 flex flex-col justify-between animate-pulse ${className}`}
    >
      <div className="flex justify-between items-center mb-6">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-8 w-20" />
      </div>
      <div className="flex-1 flex items-end gap-3 pb-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="bg-[var(--border-subtle)] rounded-t flex-1"
            style={{ height: `${20 + ((i * 7) % 70)}%` }}
          />
        ))}
      </div>
    </div>
  );
}

// ── SkeletonForm ──
export function SkeletonForm({ fields = 3, className = "" }) {
  return (
    <div className={`space-y-4 animate-pulse ${className}`}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-1.5">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
      <div className="flex gap-3 pt-2">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 flex-1" />
      </div>
    </div>
  );
}

// ── SkeletonSidebar ──
export function SkeletonSidebar({ className = "" }) {
  return (
    <div className={`space-y-2 p-4 animate-pulse ${className}`}>
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-8 w-3/4" />
    </div>
  );
}

export default Skeleton;
