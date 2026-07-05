"use client";

import React, { useState } from 'react';

export default function AnimatedButton({ 
  children, 
  onClick, 
  className = "", 
  type = "button",
  disabled = false,
  iconSrc = "/chicken-icon.png"
}) {
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  const handleClick = (e) => {
    setIsClicked(true);
    if (onClick) onClick(e);
  };

  const activeState = isHovered || isClicked;

  return (
    <button 
      type={type}
      onClick={handleClick}
      disabled={disabled}
      className={`h-12 bg-[#111111] rounded-lg border border-[#111111] relative overflow-hidden cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      onMouseEnter={() => !disabled && setIsHovered(true)}
      onMouseLeave={() => !disabled && setIsHovered(false)}
      onTouchStart={() => !disabled && setIsHovered(true)}
      onTouchEnd={() => !disabled && setIsHovered(false)}
    >
      {/* Invisible static layout placeholder to enforce natural width */}
      <div className="flex items-center justify-center opacity-0 pointer-events-none">
        <img src={iconSrc} className="w-4 h-4 shrink-0" />
        <span className="ml-2 font-bold text-xs uppercase tracking-wider whitespace-nowrap">
          {children}
        </span>
      </div>

      {/* Layer 1: Base Black Layer (White Text & Icon) */}
      <div className="absolute inset-0 z-0 w-full h-full pointer-events-none flex items-center justify-center overflow-hidden">
        <img 
          src={iconSrc} 
          alt="Icon"
          className="w-4 h-4 invert shrink-0 transition-all duration-700 ease-in-out"
        />
        <div className={`overflow-hidden transition-all duration-700 ease-in-out flex items-center ${activeState ? 'max-w-0 ml-0 opacity-0 translate-x-10' : 'max-w-[300px] ml-2 opacity-100 translate-x-0'}`}>
          <span className="text-white font-bold text-xs uppercase tracking-wider whitespace-nowrap">
            {children}
          </span>
        </div>
      </div>

      {/* Layer 2: Sweeping White Layer (Black Text & Icon) */}
      <div 
        className="absolute inset-0 z-10 w-full h-full bg-white transition-all duration-700 ease-in-out pointer-events-none flex items-center justify-center overflow-hidden"
        style={{ clipPath: activeState ? 'inset(0 0 0 0)' : 'inset(0 100% 0 0)' }}
      >
        <img 
          src={iconSrc} 
          alt="Icon"
          className="w-4 h-4 shrink-0 transition-all duration-700 ease-in-out"
        />
        <div className={`overflow-hidden transition-all duration-700 ease-in-out flex items-center ${activeState ? 'max-w-0 ml-0 opacity-0 translate-x-10' : 'max-w-[300px] ml-2 opacity-100 translate-x-0'}`}>
          <span className="text-[#111111] font-bold text-xs uppercase tracking-wider whitespace-nowrap">
            {children}
          </span>
        </div>
      </div>
    </button>
  );
}
