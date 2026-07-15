"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { X } from "lucide-react";

/**
 * Drawer — Composable right-side detail drawer.
 * Exposes Subcomponents: Drawer.Header, Drawer.Body, Drawer.Footer
 *
 * Usage:
 *   <Drawer open={isOpen} onClose={close}>
 *     <Drawer.Header title="Order #1024" description="Dispatched to Raju Chicken" />
 *     <Drawer.Body>...</Drawer.Body>
 *     <Drawer.Footer><Button onClick={close}>Close</Button></Drawer.Footer>
 *   </Drawer>
 */
export default function Drawer({ open, onClose, children, className = "" }) {
  const overlayRef = useRef(null);
  const containerRef = useRef(null);

  const handleEscape = useCallback(
    (e) => {
      if (e.key === "Escape" && onClose) onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleEscape);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, handleEscape]);

  // Focus trap
  useEffect(() => {
    if (!open || !containerRef.current) return;
    const focusable = containerRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length > 0) focusable[0].focus();
  }, [open]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[300] flex justify-end bg-black/40 backdrop-blur-[1px] transition-opacity animate-in fade-in duration-300"
      onClick={(e) => {
        if (e.target === overlayRef.current && onClose) onClose();
      }}
    >
      <div
        ref={containerRef}
        className={`w-full max-w-md h-full bg-[var(--bg-surface)] border-l border-[var(--border-subtle)] flex flex-col shadow-2xl relative transition-transform duration-300 animate-in slide-in-from-right ${className}`}
        style={{
          transform: open ? "translateX(0)" : "translateX(100%)",
        }}
        role="dialog"
        aria-modal="true"
      >
        {/* Close Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-[var(--radius-md)] transition-colors focus-ring z-10"
            aria-label="Close drawer"
          >
            <X size={20} />
          </button>
        )}
        {children}
      </div>
    </div>
  );
}

Drawer.Header = function DrawerHeader({ title, description, className = "" }) {
  return (
    <div className={`p-6 border-b border-[var(--border-subtle)] pr-12 ${className}`}>
      <h3 className="text-h3 text-[var(--text-primary)] truncate">{title}</h3>
      {description && (
        <p className="text-caption text-[var(--text-secondary)] mt-1 font-medium leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
};

Drawer.Body = function DrawerBody({ children, className = "" }) {
  return (
    <div className={`flex-1 overflow-y-auto p-6 space-y-4 ${className}`}>
      {children}
    </div>
  );
};

Drawer.Footer = function DrawerFooter({ children, className = "" }) {
  return (
    <div className={`p-6 border-t border-[var(--border-subtle)] bg-[var(--bg-app)] flex items-center justify-end gap-3 ${className}`}>
      {children}
    </div>
  );
};
