"use client";

import React from "react";

/**
 * StatusBadge — Standardized status indicator per the Design System.
 *
 * Every status in the system must use this component.
 * No ad-hoc status styling allowed.
 *
 * Usage:
 *   <StatusBadge status="delivered" />
 *   <StatusBadge status="pending" />
 *   <StatusBadge status="cancelled" />
 */

const STATUS_MAP = {
  // Order statuses
  pending:    { label: "Pending",    bg: "var(--warning-bg)",  text: "var(--warning-text)",  border: "var(--warning-border)" },
  confirmed:  { label: "Confirmed",  bg: "var(--info-bg)",     text: "var(--info-text)",     border: "var(--info-border)" },
  dispatched: { label: "Dispatched", bg: "var(--bg-elevated)", text: "var(--text-primary)",  border: "var(--border-default)" },
  delivered:  { label: "Delivered",  bg: "var(--success-bg)",  text: "var(--success-text)",  border: "var(--success-border)" },
  cancelled:  { label: "Cancelled",  bg: "var(--danger-bg)",   text: "var(--danger-text)",   border: "var(--danger-border)" },

  // Payment statuses
  paid:       { label: "Paid",       bg: "var(--success-bg)",  text: "var(--success-text)",  border: "var(--success-border)" },
  overdue:    { label: "Overdue",    bg: "var(--danger-bg)",   text: "var(--danger-text)",   border: "var(--danger-border)" },

  // Inventory statuses
  healthy:    { label: "Healthy",    bg: "var(--success-bg)",  text: "var(--success-text)",  border: "var(--success-border)" },
  low:        { label: "Low Stock",  bg: "var(--warning-bg)",  text: "var(--warning-text)",  border: "var(--warning-border)" },
  critical:   { label: "Critical",   bg: "var(--danger-bg)",   text: "var(--danger-text)",   border: "var(--danger-border)" },

  // Inventory transaction types
  purchase:   { label: "Purchase",   bg: "var(--success-bg)",  text: "var(--success-text)",  border: "var(--success-border)" },
  reserve:    { label: "Reserve",    bg: "var(--warning-bg)",  text: "var(--warning-text)",  border: "var(--warning-border)" },
  load:       { label: "Load",       bg: "var(--info-bg)",     text: "var(--info-text)",     border: "var(--info-border)" },
  waste:      { label: "Waste",      bg: "var(--danger-bg)",   text: "var(--danger-text)",   border: "var(--danger-border)" },
  adjustment: { label: "Adjustment", bg: "var(--bg-elevated)", text: "var(--text-primary)",  border: "var(--border-default)" },

  // Fleet
  safe:       { label: "Safe",       bg: "var(--success-bg)",  text: "var(--success-text)",  border: "var(--success-border)" },
  alert:      { label: "Alert",      bg: "var(--danger-bg)",   text: "var(--danger-text)",   border: "var(--danger-border)" },

  // Generic
  active:     { label: "Active",     bg: "var(--success-bg)",  text: "var(--success-text)",  border: "var(--success-border)" },
  inactive:   { label: "Inactive",   bg: "var(--bg-elevated)", text: "var(--text-secondary)", border: "var(--border-default)" },
};

export default function StatusBadge({ status, label: customLabel, className = "" }) {
  const key = (status || "").toLowerCase().replace(/[\s_-]+/g, "");
  const config = STATUS_MAP[key] || {
    label: status || "Unknown",
    bg: "var(--bg-elevated)",
    text: "var(--text-secondary)",
    border: "var(--border-default)",
  };

  return (
    <span
      className={`inline-flex items-center text-label px-2 py-0.5 rounded-[var(--radius-sm)] border whitespace-nowrap ${className}`}
      style={{
        backgroundColor: config.bg,
        color: config.text,
        borderColor: config.border,
      }}
    >
      {customLabel || config.label}
    </span>
  );
}
