"use client";

import React from "react";

/**
 * Page — Root layout wrapper for all dashboard pages.
 * Provides consistent vertical spacing and animation entry.
 */
export function Page({ children, className = "" }) {
  return (
    <div className={`space-y-6 animate-in fade-in duration-300 ${className}`}>
      {children}
    </div>
  );
}

/**
 * PageHeader — Title bar with optional description and action slot.
 *
 * Usage:
 *   <PageHeader title="Inventory" description="Monitor stock levels.">
 *     <Button variant="primary">Purchase Stock</Button>
 *   </PageHeader>
 */
export function PageHeader({ title, description, children, className = "" }) {
  return (
    <div
      className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 ${className}`}
    >
      <div className="min-w-0">
        <h2 className="text-h2 text-[var(--text-primary)] truncate">{title}</h2>
        {description && (
          <p className="text-caption text-[var(--text-secondary)] mt-1">
            {description}
          </p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-3 flex-shrink-0">{children}</div>
      )}
    </div>
  );
}

/**
 * PageContent — Main content area. Applies vertical spacing between sections.
 */
export function PageContent({ children, className = "" }) {
  return <div className={`space-y-6 ${className}`}>{children}</div>;
}

/**
 * PageSection — Groups related content blocks with an optional title.
 *
 * Usage:
 *   <PageSection title="KPIs">
 *     <KPIStatCard />
 *   </PageSection>
 */
export function PageSection({ title, description, children, className = "" }) {
  return (
    <section className={className}>
      {title && (
        <div className="mb-4">
          <h3 className="text-h3 text-[var(--text-primary)]">{title}</h3>
          {description && (
            <p className="text-caption text-[var(--text-secondary)] mt-1">
              {description}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}

/**
 * PageActions — Standardized action container for PageHeader.
 * Use when multiple actions exist.
 */
export function PageActions({ children, className = "" }) {
  return (
    <div className={`flex items-center gap-3 flex-shrink-0 ${className}`}>
      {children}
    </div>
  );
}
