"use client";

import React, { useState, forwardRef } from "react";

/**
 * Button — Unified button component per the Design System.
 *
 * Variants: primary | secondary | outline | ghost | destructive
 * Sizes:    sm | md | lg
 * Animated: Pass `animated` prop to enable the AnimatedButton sweep effect.
 *
 * Usage:
 *   <Button variant="primary" size="md">Save</Button>
 *   <Button variant="outline" size="sm" animated>Submit</Button>
 *   <Button variant="destructive" size="sm">Delete</Button>
 */

const VARIANT_STYLES = {
  primary:
    "bg-[#111111] text-white border-[#111111] hover:bg-black active:bg-[#222222]",
  secondary:
    "bg-[#FAFAFA] text-[#111111] border-[#EBEBEB] hover:bg-white hover:border-[#111111] active:bg-[#F0F0F0]",
  outline:
    "bg-transparent text-[var(--text-primary)] border-[var(--border-default)] hover:bg-[var(--bg-elevated)] active:bg-[var(--border-subtle)]",
  ghost:
    "bg-transparent text-[var(--text-secondary)] border-transparent hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)] active:bg-[var(--border-subtle)]",
  destructive:
    "bg-[var(--danger-bg)] text-[var(--danger-text)] border-[var(--danger-border)] hover:bg-[var(--danger-border)] hover:text-[var(--danger-text)] active:bg-red-200",
};

const SIZE_STYLES = {
  sm: "h-8 px-3 text-[11px] gap-1.5",
  md: "h-10 px-4 text-xs gap-2",
  lg: "h-12 px-6 text-sm gap-2.5",
};

const Button = forwardRef(function Button(
  {
    children,
    variant = "primary",
    size = "md",
    animated = false,
    disabled = false,
    iconSrc = "/chicken-icon.png",
    className = "",
    type = "button",
    onClick,
    ...props
  },
  ref
) {
  const [isHovered, setIsHovered] = useState(false);

  const baseStyles =
    "inline-flex items-center justify-center font-bold uppercase tracking-wider rounded-[var(--radius-md)] border transition-all focus-ring cursor-pointer whitespace-nowrap select-none";
  const disabledStyles = disabled ? "opacity-50 cursor-not-allowed pointer-events-none" : "";

  // ── Animated variant (sweep effect from the original AnimatedButton) ──
  if (animated) {
    const activeState = isHovered;
    return (
      <button
        ref={ref}
        type={type}
        onClick={onClick}
        disabled={disabled}
        className={`${SIZE_STYLES[size]} bg-[var(--text-primary)] rounded-[var(--radius-md)] border border-[var(--text-primary)] relative overflow-hidden cursor-pointer font-bold uppercase tracking-wider focus-ring ${disabledStyles} ${className}`}
        onMouseEnter={() => !disabled && setIsHovered(true)}
        onMouseLeave={() => !disabled && setIsHovered(false)}
        onTouchStart={() => !disabled && setIsHovered(true)}
        onTouchEnd={() => !disabled && setIsHovered(false)}
        {...props}
      >
        {/* Invisible static layout placeholder to enforce natural width */}
        <div className="flex items-center justify-center opacity-0 pointer-events-none">
          <img src={iconSrc} className="w-4 h-4 shrink-0" alt="" />
          <span className="ml-2 whitespace-nowrap">{children}</span>
        </div>

        {/* Layer 1: Base Black Layer (White Text & Icon) */}
        <div className="absolute inset-0 z-0 w-full h-full pointer-events-none flex items-center justify-center overflow-hidden">
          <img
            src={iconSrc}
            alt=""
            className="w-4 h-4 invert shrink-0 transition-all duration-700 ease-in-out"
          />
          <div
            className={`overflow-hidden transition-all duration-700 ease-in-out flex items-center ${
              activeState
                ? "max-w-0 ml-0 opacity-0 translate-x-10"
                : "max-w-[300px] ml-2 opacity-100 translate-x-0"
            }`}
          >
            <span className="text-white whitespace-nowrap">{children}</span>
          </div>
        </div>

        {/* Layer 2: Sweeping White Layer (Black Text & Icon) */}
        <div
          className="absolute inset-0 z-10 w-full h-full bg-white transition-all duration-700 ease-in-out pointer-events-none flex items-center justify-center overflow-hidden"
          style={{
            clipPath: activeState ? "inset(0 0 0 0)" : "inset(0 100% 0 0)",
          }}
        >
          <img
            src={iconSrc}
            alt=""
            className="w-4 h-4 shrink-0 transition-all duration-700 ease-in-out"
          />
          <div
            className={`overflow-hidden transition-all duration-700 ease-in-out flex items-center ${
              activeState
                ? "max-w-0 ml-0 opacity-0 translate-x-10"
                : "max-w-[300px] ml-2 opacity-100 translate-x-0"
            }`}
          >
            <span className="text-[var(--text-primary)] whitespace-nowrap">
              {children}
            </span>
          </div>
        </div>
      </button>
    );
  }

  // ── Standard button variants ──
  return (
    <button
      ref={ref}
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${VARIANT_STYLES[variant]} ${SIZE_STYLES[size]} ${disabledStyles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = "Button";

export default Button;
