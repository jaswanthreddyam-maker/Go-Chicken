"use client";

import React from "react";

export default function QuoteSummaryCard({ subtotal = 0, surcharge = 0, total = 0, className = "" }) {
  const numSubtotal = Number(subtotal);
  const numSurcharge = Number(surcharge);
  const numTotal = Number(total);

  return (
    <div className={`p-4 bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] space-y-3 ${className}`}>
      <h4 className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">
        Financial Breakdown Summary
      </h4>
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-semibold text-[var(--text-secondary)]">
          <span>Items Subtotal</span>
          <span className="tabular-nums">₹{numSubtotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>
        <div className="flex justify-between text-xs font-semibold text-[var(--text-secondary)]">
          <span>Zone Logistics Surcharge</span>
          <span className="tabular-nums">₹{numSurcharge.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>
        <div className="h-px bg-[var(--border-subtle)] my-2" />
        <div className="flex justify-between text-sm font-extrabold text-[var(--text-primary)]">
          <span>Quote Grand Total</span>
          <span className="tabular-nums">₹{numTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>
      </div>
    </div>
  );
}
