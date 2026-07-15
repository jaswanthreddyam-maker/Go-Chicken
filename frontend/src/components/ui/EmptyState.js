"use client";

import React from "react";

/**
 * EmptyState — Standardized empty/zero-data presentation per the Design System.
 *
 * Usage:
 *   <EmptyState
 *     icon={Package}
 *     title="No inventory items"
 *     description="Add your first stock item to get started."
 *     action={<Button variant="primary">Add Stock</Button>}
 *   />
 */
export default function EmptyState({
  icon: Icon,
  title = "Nothing here yet",
  description,
  action,
  className = "",
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-16 px-6 text-center ${className}`}
    >
      {Icon && (
        <div className="p-3 rounded-[var(--radius-lg)] bg-[var(--bg-app)] border border-[var(--border-subtle)] mb-4">
          <Icon size={32} className="text-[var(--text-tertiary)]" />
        </div>
      )}
      <h4 className="text-body font-bold text-[var(--text-primary)]">
        {title}
      </h4>
      {description && (
        <p className="text-caption text-[var(--text-secondary)] mt-1 max-w-xs">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
