"use client";

import React from "react";
import { CheckCircle2, Circle, AlertTriangle, Info } from "lucide-react";

/**
 * EventTimeline — Generic timeline indicator for order tracking, logs, audit trails.
 *
 * Props:
 *   events - Array of { title: string, description: string, timestamp: string, status: 'pending'|'success'|'warning'|'neutral' }
 *
 * Usage:
 *   <EventTimeline events={orderTimeline} />
 */

const STATUS_ICONS = {
  success: <CheckCircle2 size={14} className="text-[var(--success-text)] bg-[var(--bg-surface)] z-10" />,
  warning: <AlertTriangle size={14} className="text-[var(--warning-text)] bg-[var(--bg-surface)] z-10" />,
  pending: <Circle size={14} className="text-[var(--warning-text)] fill-[var(--warning-bg)] bg-[var(--bg-surface)] z-10" />,
  neutral: <Info size={14} className="text-[var(--text-secondary)] bg-[var(--bg-surface)] z-10" />,
};

const STATUS_BORDER_COLORS = {
  success: "border-[var(--success-border)]",
  warning: "border-[var(--warning-border)]",
  pending: "border-[var(--warning-border)]",
  neutral: "border-[var(--border-subtle)]",
};

export default function EventTimeline({ events = [], className = "" }) {
  if (events.length === 0) {
    return (
      <p className="text-caption text-[var(--text-secondary)] italic text-center py-4">
        No event history logged.
      </p>
    );
  }

  return (
    <div className={`relative border-l border-[var(--border-subtle)] ml-3 pl-6 space-y-6 py-2 ${className}`}>
      {events.map((event, idx) => {
        const icon = STATUS_ICONS[event.status || "neutral"] || STATUS_ICONS.neutral;
        const borderCol = STATUS_BORDER_COLORS[event.status || "neutral"] || STATUS_BORDER_COLORS.neutral;

        return (
          <div key={idx} className="relative flex flex-col items-start gap-1 group">
            {/* Absolute positioning marker dot */}
            <div
              className={`absolute -left-[32px] top-1 p-0.5 rounded-full border bg-[var(--bg-surface)] flex items-center justify-center ${borderCol}`}
            >
              {icon}
            </div>

            {/* Event Header */}
            <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 w-full">
              <span className="text-caption font-bold text-[var(--text-primary)]">
                {event.title}
              </span>
              {event.timestamp && (
                <span className="text-[10px] text-[var(--text-tertiary)] font-semibold tabular-nums">
                  {event.timestamp}
                </span>
              )}
            </div>

            {/* Event Description */}
            {event.description && (
              <p className="text-[11px] text-[var(--text-secondary)] font-medium leading-relaxed">
                {event.description}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
