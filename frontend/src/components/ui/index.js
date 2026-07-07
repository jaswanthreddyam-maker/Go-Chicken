"use client";

import React from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, Send, X, WifiOff } from "lucide-react";
import AnimatedButton from "@/components/AnimatedButton";

export const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl border border-[#EBEBEB] overflow-hidden ${className}`}>
    {children}
  </div>
);

export const StatBox = ({ title, value, icon: Icon, alert = false, subtitle, trend }) => (
  <Card className={`p-4 sm:p-5 min-w-[240px] sm:min-w-[260px] md:min-w-0 snap-start flex-shrink-0 transition-all hover:border-[#111111] ${alert ? 'border-red-300 bg-red-50/20' : ''}`}>
    <div className="flex justify-between items-start">
      <div className="space-y-1 min-w-0 flex-1">
        <p className={`text-[9px] sm:text-[10px] font-bold uppercase tracking-wider ${alert ? 'text-red-700' : 'text-[#666666]'}`}>{title}</p>
        <h3 className={`text-xl sm:text-2xl font-extrabold tracking-tight ${alert ? 'text-red-800' : 'text-[#111111]'}`}>{value}</h3>
        {subtitle && (
          <div className="flex items-center gap-1 mt-1">
            <span className={`text-[9px] sm:text-[10px] font-semibold tracking-wide ${trend === 'up' ? 'text-[#111111]' : trend === 'down' ? 'text-red-600' : 'text-[#666666]'}`}>
              {subtitle}
            </span>
          </div>
        )}
      </div>
      <div className={`p-2 rounded-lg border flex-shrink-0 ${alert ? 'bg-red-50 border-red-150 text-red-600' : 'bg-[#FAFAFA] border-[#EBEBEB] text-[#111111]'}`}>
        <Icon size={16} />
      </div>
    </div>
  </Card>
);

export const TableSkeleton = ({ rows = 4, cols = 5 }) => (
  <div className="animate-pulse p-6 bg-white space-y-4">
    {Array.from({ length: rows }).map((_, r) => (
      <div key={r} className="flex gap-4 items-center">
        {Array.from({ length: cols }).map((_, c) => (
          <div className="h-4 bg-[#EBEBEB] rounded flex-1" key={c}></div>
        ))}
      </div>
    ))}
  </div>
);

export const ChartSkeleton = () => (
  <div className="animate-pulse bg-white border border-[#EBEBEB] rounded-xl p-6 h-80 flex flex-col justify-between">
    <div className="flex justify-between items-center mb-6">
      <div className="h-5 bg-[#EBEBEB] rounded w-1/3"></div>
      <div className="h-8 bg-[#EBEBEB] rounded w-20"></div>
    </div>
    <div className="flex-1 flex items-end gap-3 pb-4">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="bg-[#EBEBEB] rounded-t flex-1" style={{ height: `${20 + (i * 7) % 70}%` }}></div>
      ))}
    </div>
  </div>
);

export const Toast = ({ message, type = 'info', onClose }) => {
  const borderStyles = {
    success: 'border-[#111111] text-[#111111]',
    error: 'border-red-600 text-red-700',
    warning: 'border-amber-500 text-amber-800',
    info: 'border-[#EBEBEB] text-[#111111]',
  };
  const icons = {
    success: <CheckCircle2 size={16} className="text-[#111111]" />,
    error: <AlertCircle size={16} className="text-red-600" />,
    warning: <AlertTriangle size={16} className="text-amber-500" />,
    info: <Send size={16} className="text-[#111111]" />,
  };

  return (
    <div className={`border-l-4 bg-white border border-y-[#EBEBEB] border-r-[#EBEBEB] px-4 py-3 flex items-center justify-between text-xs font-semibold shadow-sm animate-in fade-in slide-in-from-top duration-200 ${borderStyles[type]}`}>
      <span className="flex items-center gap-2">
        {icons[type]} {message}
      </span>
      <button onClick={onClose} className="hover:opacity-70 text-[#666666] ml-4"><X size={14} /></button>
    </div>
  );
};

export function classifyError(err, response) {
  if (!response && (err instanceof TypeError || err.name === 'AbortError')) {
    return {
      type: 'warning',
      message: '⚠️ Network Connection Error: Could not reach the server. UI reverted to previous state.',
    };
  }
  if (response && !response.ok) {
    const code = response.status;
    if (code === 401 || code === 403) {
      return { type: 'error', message: '❌ Access Denied: You do not have permission for this action. UI reverted.' };
    }
    if (code === 404) {
      return { type: 'error', message: '❌ Not Found: The requested resource could not be located. UI reverted.' };
    }
    if (code === 422) {
      return { type: 'error', message: '❌ Validation Error: Please check your input and try again. UI reverted.' };
    }
    return { type: 'error', message: `❌ Request Rejected (HTTP ${code}): Unable to save your changes at this time. Please try again. UI reverted.` };
  }
  return { type: 'error', message: '❌ An unexpected error occurred. UI reverted to previous state.' };
}

export const ErrorBanner = ({ message, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-12 text-[#666666] bg-white border border-[#EBEBEB] rounded-xl">
    <WifiOff size={32} className="mb-3 text-[#111111]" />
    <p className="font-semibold text-xs uppercase tracking-wider">{message}</p>
    <AnimatedButton
      onClick={onRetry}
      className="mt-4 w-auto px-8 bg-[#111111] text-white hover:bg-black"
    >
      Try Again
    </AnimatedButton>
  </div>
);
