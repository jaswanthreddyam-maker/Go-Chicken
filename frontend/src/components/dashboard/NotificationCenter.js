"use client";

import React, { useState, useRef, useEffect } from "react";
import { Bell, Check, X, ShieldAlert, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { useUI } from "@/context/UIContext";

const NOTIF_ICONS = {
  info: <Info size={14} className="text-blue-600" />,
  success: <CheckCircle2 size={14} className="text-[var(--success-text)]" />,
  warning: <AlertTriangle size={14} className="text-[var(--warning-text)]" />,
  critical: <ShieldAlert size={14} className="text-[var(--danger-text)]" />,
};

const NOTIF_BORDERS = {
  info: "border-blue-150 bg-blue-50/20",
  success: "border-[var(--success-border)] bg-[var(--success-bg)]/20",
  warning: "border-[var(--warning-border)] bg-[var(--warning-bg)]/20",
  critical: "border-[var(--danger-border)] bg-[var(--danger-bg)]/20",
};

export default function NotificationCenter() {
  const { notifications, markAllAsRead } = useUI();
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  return (
    <div ref={containerRef} className="relative z-[100]">
      {/* Trigger Button */}
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="relative p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] border border-transparent hover:border-[var(--border-subtle)] rounded-[var(--radius-md)] transition-all focus-ring"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-black rounded-full border border-white" />
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          className="absolute right-0 mt-2 w-80 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] overflow-hidden shadow-[var(--shadow-md)] animate-in slide-in-from-top duration-150"
          style={{ zIndex: "var(--z-dropdown)" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3.5 bg-[var(--bg-app)] border-b border-[var(--border-subtle)]">
            <span className="text-label text-[var(--text-primary)]">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-[10px] font-bold text-[var(--text-primary)] hover:underline flex items-center gap-0.5"
              >
                <Check size={10} /> Mark all read
              </button>
            )}
          </div>

          {/* List content */}
          <div className="divide-y divide-[var(--border-subtle)] max-h-72 overflow-y-auto">
            {notifications.length > 0 ? (
              notifications.map((n) => {
                const border = NOTIF_BORDERS[n.type || "info"];
                const icon = NOTIF_ICONS[n.type || "info"];

                return (
                  <div
                    key={n.id}
                    className={`p-3.5 text-caption transition-colors ${
                      n.read ? "hover:bg-[var(--bg-app)]" : "bg-[var(--bg-app)]/60 font-semibold"
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <div className={`p-1.5 rounded-[var(--radius-sm)] border flex-shrink-0 mt-0.5 ${border}`}>
                        {icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] text-[var(--text-primary)] font-bold truncate">
                          {n.title}
                        </p>
                        <p className="text-[11px] text-[var(--text-secondary)] font-medium mt-0.5 leading-relaxed">
                          {n.text}
                        </p>
                      </div>
                      {!n.read && (
                        <span className="w-1.5 h-1.5 rounded-full bg-black flex-shrink-0 mt-2" />
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-caption text-[var(--text-secondary)] font-medium">
                No active notifications.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
