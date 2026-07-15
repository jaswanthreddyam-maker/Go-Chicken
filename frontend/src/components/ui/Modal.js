"use client";

import React, { useEffect, useRef, useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

/**
 * Modal — Unified modal/dialog component per the Design System.
 *
 * Sizes: sm | md | lg | fullscreen
 * Features: Escape close, click-outside close, focus trap, blurred backdrop.
 *
 * Usage:
 *   <Modal open={showModal} onClose={() => setShowModal(false)} title="Record Payment" size="md">
 *     <Modal.Body>
 *       <Form>...</Form>
 *     </Modal.Body>
 *     <Modal.Footer>
 *       <Button variant="outline" onClick={close}>Cancel</Button>
 *       <Button variant="primary" type="submit">Save</Button>
 *     </Modal.Footer>
 *   </Modal>
 */

const SIZE_STYLES = {
  sm: "w-full max-w-sm",
  md: "w-full max-w-[540px]",
  lg: "w-full max-w-2xl",
  fullscreen: "w-full h-full max-w-none max-h-none rounded-none",
};

export default function Modal({
  open,
  onClose,
  title,
  description,
  size = "md",
  children,
  className = "",
}) {
  const overlayRef = useRef(null);
  const contentRef = useRef(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(t);
  }, []);

  // ── Escape key handler ──
  const handleEscape = useCallback(
    (e) => {
      if (e.key === "Escape" && onClose) onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleEscape);
    // Prevent body scroll when modal is open
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, handleEscape]);

  // ── Focus trap ──
  useEffect(() => {
    if (!open || !contentRef.current) return;
    const focusable = contentRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length > 0) focusable[0].focus();
  }, [open]);

  if (!open || !mounted) return null;

  const isFullscreen = size === "fullscreen";

  const modalContent = (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[var(--z-modal)] bg-black/40 backdrop-blur-sm flex items-end md:items-center justify-center transition-all animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === overlayRef.current && onClose) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        ref={contentRef}
        className={`
          bg-[var(--bg-surface)]
          ${isFullscreen ? "" : "rounded-[var(--radius-lg)]"}
          flex flex-col overflow-hidden
          ${SIZE_STYLES[size]}
          ${className}
        `}
        style={{
          boxShadow: 'var(--shadow-lg)',
          animation: 'fadeIn 180ms cubic-bezier(0.4,0,0.2,1), scaleInNew 180ms cubic-bezier(0.4,0,0.2,1)'
        }}
      >
        {/* ── Header ── */}
        {title && (
          <div className="flex items-start justify-between p-6 pb-4 border-b border-[#EBEBEB]">
            <div className="min-w-0 flex-1">
              <h2 className="text-xl font-extrabold text-[#111111] truncate tracking-tight">
                {title}
              </h2>
              {description && (
                <p className="text-sm text-[#666666] mt-1 font-medium">
                  {description}
                </p>
              )}
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1.5 -m-1.5 ml-4 text-[#999999] hover:text-[#111111] hover:bg-[#FAFAFA] rounded-lg transition-colors focus-ring flex-shrink-0"
                aria-label="Close dialog"
              >
                <X size={20} />
              </button>
            )}
          </div>
        )}

        {/* ── Mobile drag indicator (shown only on non-fullscreen, below md) ── */}
        {!title && !isFullscreen && (
          <div className="w-12 h-1 bg-[var(--border-subtle)] rounded-full mx-auto mt-3 mb-2 md:hidden" />
        )}

        {/* ── Content ── */}
        {children}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

// ── Modal.Body ──
Modal.Body = function ModalBody({ children, className = "" }) {
  return (
    <div className={`p-6 flex-1 overflow-y-auto ${className}`}>
      {children}
    </div>
  );
};

// ── Modal.Footer ──
Modal.Footer = function ModalFooter({ children, className = "" }) {
  return (
    <div
      className={`flex items-center justify-end gap-3 p-6 pt-0 ${className}`}
    >
      {children}
    </div>
  );
};
