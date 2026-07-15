"use client";

import React, { forwardRef, createContext, useContext } from "react";

/* ══════════════════════════════════════════════════════════
   FORM SYSTEM — Design System compliant form primitives
   ══════════════════════════════════════════════════════════ */

// ── Form ────────────────────────────────────────────────
export function Form({ children, onSubmit, className = "", ...props }) {
  return (
    <form
      onSubmit={onSubmit}
      className={`space-y-4 ${className}`}
      noValidate
      {...props}
    >
      {children}
    </form>
  );
}

// ── FormField ───────────────────────────────────────────
// Groups Label + Input + HelperText + Error into a single field.
export function FormField({ children, className = "" }) {
  return <div className={`flex flex-col ${className}`}>{children}</div>;
}

// ── Label ───────────────────────────────────────────────
export function Label({ children, htmlFor, required, className = "" }) {
  return (
    <label
      htmlFor={htmlFor}
      className={`text-[10px] font-bold text-[#666666] uppercase tracking-wider mb-2 block ${className}`}
    >
      {children}
      {required && <span className="text-red-500 font-bold ml-1">*</span>}
    </label>
  );
}

// ── Input ───────────────────────────────────────────────
export const Input = forwardRef(function Input(
  { error, className = "", ...props },
  ref
) {
  return (
    <input
      ref={ref}
      className={`w-full h-11 px-3 text-sm text-[#111111] font-medium
        bg-white border rounded-lg
        placeholder:text-[#999999] placeholder:font-normal
        transition-colors
        focus:outline-none focus:border-[#111111] focus:ring-1 focus:ring-[#111111]
        disabled:opacity-50 disabled:cursor-not-allowed
        ${error ? "border-red-500 bg-red-50" : "border-[#EBEBEB] hover:border-[#CCCCCC]"}
        ${className}`}
      {...props}
    />
  );
});
Input.displayName = "Input";

// ── Select ──────────────────────────────────────────────
export const Select = forwardRef(function Select(
  { children, error, className = "", ...props },
  ref
) {
  return (
    <select
      ref={ref}
      className={`w-full h-11 px-3 text-sm text-[#111111] font-medium
        bg-white border rounded-lg
        transition-colors appearance-none
        focus:outline-none focus:border-[#111111] focus:ring-1 focus:ring-[#111111]
        disabled:opacity-50 disabled:cursor-not-allowed
        ${error ? "border-red-500 bg-red-50" : "border-[#EBEBEB] hover:border-[#CCCCCC]"}
        ${className}`}
      {...props}
    >
      {children}
    </select>
  );
});
Select.displayName = "Select";

// ── Textarea ────────────────────────────────────────────
export const Textarea = forwardRef(function Textarea(
  { error, className = "", ...props },
  ref
) {
  return (
    <textarea
      ref={ref}
      className={`w-full px-3 py-2.5 text-caption text-[var(--text-primary)] font-medium
        bg-[var(--bg-app)] border rounded-[var(--radius-md)]
        placeholder:text-[var(--text-tertiary)]
        transition-colors resize-y min-h-[80px]
        focus:outline-none focus:border-[var(--border-strong)] focus:bg-[var(--bg-surface)]
        disabled:opacity-50 disabled:cursor-not-allowed
        ${error ? "border-[var(--danger-border)] bg-[var(--danger-bg)]" : "border-[var(--border-default)]"}
        ${className}`}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

// ── HelperText ──────────────────────────────────────────
export function HelperText({ children, className = "" }) {
  return (
    <p className={`text-[11px] text-[var(--text-tertiary)] font-medium ${className}`}>
      {children}
    </p>
  );
}

// ── Error ───────────────────────────────────────────────
export function FieldError({ children, className = "" }) {
  if (!children) return null;
  return (
    <p className={`text-[11px] text-[var(--danger-text)] font-semibold ${className}`}>
      {children}
    </p>
  );
}
