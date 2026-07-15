"use client";

import React from "react";

/**
 * KPIStatCard — Standardized metric card per the Design System.
 *
 * Props:
 *   title      - Metric label (e.g., "Active Fleet")
 *   value      - Primary value (e.g., "1,850 kg")
 *   icon       - Lucide icon component
 *   trend      - "up" | "down" | "neutral" — colors the subtitle
 *   subtitle   - Secondary context text (e.g., "↑ 8.8% vs Today")
 *   alert      - Boolean, applies danger styling
 *   loading    - Show skeleton pulse
 *   sparkline  - Reserved for future sparkline data array
 *
 * Usage:
 *   <KPIStatCard
 *     title="Tomorrow's Forecast"
 *     value="1,850 kg"
 *     icon={BrainCircuit}
 *     subtitle="↑ 8.8% vs Today (94% confidence)"
 *     trend="up"
 *   />
 */
export default function KPIStatCard({
  title,
  value,
  icon: Icon,
  trend,
  subtitle,
  alert = false,
  loading = false,
  sparkline,
  className = "",
}) {
  // ── Loading skeleton ──
  if (loading) {
    return (
      <div
        className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] p-4 sm:p-5 min-w-[240px] sm:min-w-[260px] md:min-w-0 snap-start flex-shrink-0 animate-pulse ${className}`}
      >
        <div className="flex justify-between items-start">
          <div className="space-y-2 flex-1">
            <div className="h-3 bg-[var(--border-subtle)] rounded w-24" />
            <div className="h-7 bg-[var(--border-subtle)] rounded w-20" />
            <div className="h-3 bg-[var(--border-subtle)] rounded w-32 mt-1" />
          </div>
          <div className="w-9 h-9 bg-[var(--border-subtle)] rounded-[var(--radius-md)]" />
        </div>
      </div>
    );
  }

  // ── Trend color mapping ──
  const trendColor =
    trend === "up"
      ? "text-[var(--success-text)]"
      : trend === "down"
      ? "text-[var(--danger-text)]"
      : "text-[var(--text-secondary)]";

  // ── Alert state styling ──
  const borderStyle = alert
    ? "border-[var(--danger-border)] bg-[var(--danger-bg)]"
    : "border-[var(--border-subtle)] bg-[var(--bg-surface)]";

  const iconBg = alert
    ? "bg-[var(--danger-bg)] border-[var(--danger-border)] text-[var(--danger-text)]"
    : "bg-[var(--bg-app)] border-[var(--border-subtle)] text-[var(--text-primary)]";

  return (
    <div
      className={`rounded-[var(--radius-lg)] border p-4 sm:p-5 min-w-[240px] sm:min-w-[260px] md:min-w-0 snap-start flex-shrink-0 transition-all hover:border-[var(--border-strong)] ${borderStyle} ${className}`}
      style={{ transitionDuration: "var(--duration-fast)" }}
    >
      <div className="flex justify-between items-start">
        <div className="space-y-1 min-w-0 flex-1">
          <p
            className={`text-label ${
              alert ? "text-[var(--danger-text)]" : "text-[var(--text-secondary)]"
            }`}
          >
            {title}
          </p>
          <h3
            className={`text-h2 tracking-tight tabular-nums ${
              alert ? "text-[var(--danger-text)]" : "text-[var(--text-primary)]"
            }`}
          >
            {value}
          </h3>
          {subtitle && (
            <p className={`text-[11px] font-semibold tracking-wide mt-1 ${trendColor}`}>
              {subtitle}
            </p>
          )}
        </div>
        {Icon && (
          <div
            className={`p-2 rounded-[var(--radius-md)] border flex-shrink-0 ${iconBg}`}
          >
            <Icon size={16} />
          </div>
        )}
      </div>
    </div>
  );
}
